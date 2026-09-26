"""The bot worker: a separate process that makes the bots post, comment and reply at a human pace.

Run from the backend folder:
    python -m bots.worker                                           default pacing
    python -m bots.worker --min-sleep 5 --max-sleep 15 --cooldown 60   faster, for watching a demo
    python -m bots.worker --ticks 5                                 stop after five ticks

All state lives in the database, so stopping and restarting the worker loses nothing.
"""
import argparse
import html
import logging
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

import services
from brain import get_brain
from utils import html_to_text

ACTIONS = ('post', 'comment', 'reply')
CANDIDATE_LIMIT = 20
IDLE_POOL = 3


@dataclass(frozen=True)
class Pacing:
    min_sleep: float = 30
    max_sleep: float = 120
    cooldown_seconds: int = 600
    daily_cap: int = 12
    max_reply_depth: int = 3
    weights: Dict[str, float] = field(default_factory=lambda: {'post': 0.25, 'comment': 0.45, 'reply': 0.30})


@dataclass(frozen=True)
class BotState:
    id: int
    name: str
    personality: str
    last_action_at: Optional[datetime]
    recent_actions: int


class NothingToDo(Exception):
    """The chosen action has no valid target this tick."""


class BrainUnavailable(Exception):
    """The brain raised an error; bots skip the action instead of falling back."""


# ---- Pure rules ----

def skip_reason(bot, now, pacing):
    if bot.recent_actions >= pacing.daily_cap:
        return 'daily cap reached'
    if bot.last_action_at is not None and (now - bot.last_action_at).total_seconds() < pacing.cooldown_seconds:
        return 'cooldown'
    return None


def choose_bot(bots, now, pacing, rng):
    """Picks one of the bots idle longest among those allowed to act, or None."""
    eligible = [bot for bot in bots if skip_reason(bot, now, pacing) is None]
    if not eligible:
        return None
    eligible.sort(key=lambda bot: bot.last_action_at or datetime.min)
    return rng.choice(eligible[:IDLE_POOL])


def choose_action(rng, weights):
    actions = [action for action in ACTIONS if weights.get(action, 0) > 0]
    return rng.choices(actions, weights=[weights[action] for action in actions])[0]


def reply_allowed(parent_depth, pacing):
    return parent_depth + 1 <= pacing.max_reply_depth


def sleep_seconds(rng, pacing):
    return rng.uniform(pacing.min_sleep, pacing.max_sleep)


def to_post_html(text):
    return f'<p>{html.escape(text)}</p>'


# ---- One tick ----

def _ask(call, *args):
    try:
        return call(*args)
    except Exception as error:
        raise BrainUnavailable(str(error)) from error


def load_bots(now):
    since = (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
    return [BotState(**row) for row in services.list_bot_activity(since)]


def do_post(bot, brain, rng, pacing, seed):
    post = _ask(brain.write_post, bot.personality, seed)
    post_id = services.create_post(bot.id, post.title, to_post_html(post.body))
    return f'-> post {post_id} "{post.title}"'


def do_comment(bot, brain, rng, pacing, seed):
    targets = services.list_comment_targets(bot.id, CANDIDATE_LIMIT)
    if not targets:
        raise NothingToDo('no posts left to comment on')
    target = rng.choice(targets)
    context = f"{target['title']}\n{html_to_text(target['body'])}"
    text = _ask(brain.write_reply, bot.personality, context, seed)
    comment = services.create_comment(target['id'], bot.id, text)
    return f'post={target["id"]} -> comment {comment["id"]}'


def do_reply(bot, brain, rng, pacing, seed):
    targets = services.list_reply_targets(bot.id, CANDIDATE_LIMIT)
    if not targets:
        raise NothingToDo('no comments to reply to')
    rng.shuffle(targets)
    for target in targets:
        depth = services.comment_depth(target['id'])
        if reply_allowed(depth, pacing):
            text = _ask(brain.write_reply, bot.personality, target['body'], seed)
            comment = services.create_comment(target['post_id'], bot.id, text, parent_id=target['id'])
            return f'comment={target["id"]} depth={depth + 1} -> comment {comment["id"]}'
    raise NothingToDo('no comment to reply to within the depth limit')


HANDLERS = {'post': do_post, 'comment': do_comment, 'reply': do_reply}


def run_tick(tick, brain, rng, pacing, log):
    """Runs one bot action and logs one line. Returns the outcome."""
    now = services.database_now()
    bots = load_bots(now)
    prefix = f'tick {tick:<4}'

    bot = choose_bot(bots, now, pacing, rng)
    if bot is None:
        reasons = sorted({skip_reason(b, now, pacing) for b in bots}) or ['no bots seeded']
        log(f'{prefix} action=skip     all bots resting ({", ".join(reasons)})' if bots
            else f'{prefix} action=skip     {reasons[0]}')
        return 'skip'

    action = choose_action(rng, pacing.weights)
    head = f'{prefix} bot={bot.name:<20} action={action:<8}'
    try:
        result = HANDLERS[action](bot, brain, rng, pacing, rng.randrange(1_000_000))
    except NothingToDo as reason:
        log(f'{head} -> skipped ({reason})')
        return 'nothing'
    except services.ContentRejected as error:
        log(f'{head} -> skipped (toxicity: {error})')
        return 'rejected'
    except BrainUnavailable as error:
        log(f'{head} -> skipped (brain unavailable: {error})')
        return 'brain-error'

    log(f'{head} {result}')
    return action


# ---- The loop ----

def parse_args(argv=None):
    defaults = Pacing()
    parser = argparse.ArgumentParser(description='Run the bot worker.')
    parser.add_argument('--min-sleep', type=float, default=defaults.min_sleep, help='shortest pause between ticks, seconds')
    parser.add_argument('--max-sleep', type=float, default=defaults.max_sleep, help='longest pause between ticks, seconds')
    parser.add_argument('--cooldown', type=int, default=defaults.cooldown_seconds, help='seconds a bot rests after acting')
    parser.add_argument('--daily-cap', type=int, default=defaults.daily_cap, help='most actions per bot in 24 hours')
    parser.add_argument('--max-depth', type=int, default=defaults.max_reply_depth, help='deepest reply level bots may create')
    parser.add_argument('--ticks', type=int, default=None, help='stop after this many ticks (default: run forever)')
    parser.add_argument('--seed', type=int, default=None, help='random seed, for a repeatable run')
    args = parser.parse_args(argv)

    if args.min_sleep < 0 or args.min_sleep > args.max_sleep:
        parser.error('--min-sleep must be between 0 and --max-sleep')

    pacing = Pacing(
        min_sleep=args.min_sleep,
        max_sleep=args.max_sleep,
        cooldown_seconds=args.cooldown,
        daily_cap=args.daily_cap,
        max_reply_depth=args.max_depth,
    )
    return args, pacing


def main(argv=None):
    args, pacing = parse_args(argv)
    # logging writes each line out immediately; print() output can sit in a buffer when not on a terminal.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(message)s', datefmt='%H:%M:%S', stream=sys.stdout)
    log = logging.getLogger('bots.worker').info

    rng = random.Random(args.seed)
    brain = get_brain()
    log(f'worker started  brain={type(brain).__name__}  sleep={pacing.min_sleep:g}-{pacing.max_sleep:g}s  '
        f'cooldown={pacing.cooldown_seconds}s  daily cap={pacing.daily_cap}  max reply depth={pacing.max_reply_depth}')

    tick = 0
    try:
        while args.ticks is None or tick < args.ticks:
            tick += 1
            try:
                run_tick(tick, brain, rng, pacing, log)
            except Exception as error:
                log(f'tick {tick:<4} error: {type(error).__name__}: {error} (retrying next tick)')
            if args.ticks is not None and tick >= args.ticks:
                break
            pause = sleep_seconds(rng, pacing)
            log(f'          sleeping {pause:.0f}s')
            time.sleep(pause)
    except KeyboardInterrupt:
        log('worker stopped (Ctrl+C)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
