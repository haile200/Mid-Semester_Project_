"""Integration tests for the bot worker: run_tick and its queries against the SQLite database from conftest.py."""
import random

import pytest

import bots.worker
import services
from bots.profiles import BOTS
from bots.seed import seed_bots
from bots.worker import Pacing, run_tick
from brain import OfflineBrain

COMMENT_ONLY = {'comment': 1}
REPLY_ONLY = {'reply': 1}


def add_human(db, name='Human Climber', email='human@example.com'):
    db.execute("INSERT INTO users (name, email, password) VALUES (?, ?, 'x')", (name, email))
    db.commit()
    return db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()[0]


def bot_id(db, index=0):
    return db.execute('SELECT id FROM users WHERE email = ?', (BOTS[index].email,)).fetchone()[0]


def tick(pacing, brain=None, seed=1):
    logs = []
    outcome = run_tick(1, brain or OfflineBrain(), random.Random(seed), pacing, logs.append)
    return outcome, logs


class ToxicBrain(OfflineBrain):
    def write_reply(self, personality, context, seed):
        return 'you are an idiot'


class BrokenBrain(OfflineBrain):
    def write_reply(self, personality, context, seed):
        raise RuntimeError('timeout')


# ---- Queries ----

def test_comment_depth_counts_levels_from_the_top(db):
    # Arrange
    human = add_human(db)
    post_id = services.create_post(human, 'Post', '<p>Body</p>')
    top = services.create_comment(post_id, human, 'top')
    reply = services.create_comment(post_id, human, 'reply', parent_id=top['id'])
    nested = services.create_comment(post_id, human, 'nested', parent_id=reply['id'])

    # Act
    depths = [services.comment_depth(c['id']) for c in (top, reply, nested)]

    # Assert
    assert depths == [0, 1, 2]


def test_targets_say_whether_a_person_or_a_bot_wrote_them(db):
    # Arrange: one post and one comment by a person, one of each by another bot.
    seed_bots(BOTS[:2])
    acting, other_bot = bot_id(db, 0), bot_id(db, 1)
    human = add_human(db)
    human_post = services.create_post(human, 'By a person', '<p>Body</p>')
    bot_post = services.create_post(other_bot, 'By a bot', '<p>Body</p>')
    human_comment = services.create_comment(bot_post, human, 'person comment')
    bot_comment = services.create_comment(human_post, other_bot, 'bot comment')

    # Act
    comment_targets = {t['id']: t['author_is_bot'] for t in services.list_comment_targets(acting, 10)}
    like_targets = {t['id']: t['author_is_bot'] for t in services.list_like_targets(acting, 10)}
    reply_targets = {t['id']: t['author_is_bot'] for t in services.list_reply_targets(acting, 10)}

    # Assert: real booleans, not the database's 0 and 1.
    assert comment_targets == {human_post: False, bot_post: True}
    assert like_targets == {human_post: False, bot_post: True}
    assert reply_targets == {human_comment['id']: False, bot_comment['id']: True}


@pytest.mark.parametrize('action', ['comment', 'like', 'reply'])
def test_every_action_picks_its_target_through_order_targets(db, monkeypatch, action):
    # Arrange: a stand-in ordering that always puts the oldest target first. With 20 targets, a plain
    # random pick would land on the oldest only 1 time in 20.
    seed_bots([BOTS[0]])
    human = add_human(db)
    posts = [services.create_post(human, f'Post {n}', '<p>Body</p>') for n in range(20)]
    comments = [services.create_comment(post, human, f'comment {n}')['id'] for n, post in enumerate(posts)]
    monkeypatch.setattr(bots.worker, 'order_targets', lambda targets, rng: list(reversed(targets)))

    # Act
    outcome, logs = tick(Pacing(weights={action: 1}))

    # Assert
    oldest = f'comment={comments[0]} ' if action == 'reply' else f'post={posts[0]} '
    assert outcome == action
    assert oldest in logs[0]


def test_bot_activity_reports_last_action_and_recent_count(db):
    # Arrange
    seed_bots([BOTS[0]])
    bot = bot_id(db)
    services.create_post(bot, 'Bot post', '<p>Body</p>')
    now = services.database_now()

    # Act
    activity = services.list_bot_activity('2000-01-01 00:00:00')

    # Assert
    assert len(activity) == 1
    assert activity[0]['recent_actions'] == 1
    assert abs((now - activity[0]['last_action_at']).total_seconds()) < 5


# ---- run_tick ----

def test_tick_with_no_bots_skips_and_says_why(db):
    # Arrange: an empty database

    # Act
    outcome, logs = tick(Pacing())

    # Assert
    assert outcome == 'skip'
    assert 'no active bots' in logs[0]


def test_tick_comment_publishes_a_bot_comment_on_a_human_post(db):
    # Arrange
    seed_bots([BOTS[0]])
    human = add_human(db)
    post_id = services.create_post(human, 'Sent my project', '<p>Finally.</p>')

    # Act
    outcome, logs = tick(Pacing(weights=COMMENT_ONLY))

    # Assert
    row = db.execute('SELECT post_id, author_id FROM comments').fetchone()
    assert outcome == 'comment'
    assert row == (post_id, bot_id(db))
    assert 'action=comment' in logs[0] and '-> comment' in logs[0]


def test_tick_post_publishes_escaped_html(db):
    # Arrange
    seed_bots([BOTS[0]])

    # Act
    outcome, logs = tick(Pacing(weights={'post': 1}))

    # Assert
    row = db.execute('SELECT author_id, body FROM posts').fetchone()
    assert outcome == 'post'
    assert row[0] == bot_id(db)
    assert row[1].startswith('<p>') and row[1].endswith('</p>')


def test_bot_rests_during_its_cooldown(db):
    # Arrange: one bot has just acted.
    seed_bots([BOTS[0]])
    human = add_human(db)
    services.create_post(human, 'Post', '<p>Body</p>')
    tick(Pacing(weights=COMMENT_ONLY))

    # Act
    outcome, logs = tick(Pacing(weights=COMMENT_ONLY, cooldown_seconds=600))

    # Assert
    assert outcome == 'skip'
    assert 'all bots resting (cooldown)' in logs[0]


def test_bot_stops_at_its_daily_cap(db):
    # Arrange
    seed_bots([BOTS[0]])
    pacing = Pacing(weights={'post': 1}, cooldown_seconds=0, daily_cap=1)
    tick(pacing)

    # Act
    outcome, logs = tick(pacing)

    # Assert
    assert outcome == 'skip'
    assert 'daily cap reached' in logs[0]


def test_bot_never_comments_twice_on_the_same_post(db):
    # Arrange
    seed_bots([BOTS[0]])
    human = add_human(db)
    services.create_post(human, 'Only post', '<p>Body</p>')
    pacing = Pacing(weights=COMMENT_ONLY, cooldown_seconds=0)
    tick(pacing)

    # Act
    outcome, logs = tick(pacing)

    # Assert: no second comment; the bot writes a post instead.
    assert outcome == 'post'
    assert 'no posts left to comment on' in logs[0]
    assert db.execute('SELECT COUNT(*) FROM comments').fetchone()[0] == 1


def test_bot_never_comments_on_its_own_post(db):
    # Arrange: the only post belongs to the bot. Writing it counts as bot activity,
    # so the cooldown is zero to reach the rule under test.
    seed_bots([BOTS[0]])
    services.create_post(bot_id(db), 'My own post', '<p>Body</p>')

    # Act
    outcome, logs = tick(Pacing(weights=COMMENT_ONLY, cooldown_seconds=0))

    # Assert
    assert outcome == 'post'
    assert 'no posts left to comment on' in logs[0]
    assert db.execute('SELECT COUNT(*) FROM comments').fetchone()[0] == 0


def test_bot_never_replies_to_itself(db):
    # Arrange: the only comment belongs to the bot.
    seed_bots([BOTS[0]])
    human = add_human(db)
    post_id = services.create_post(human, 'Post', '<p>Body</p>')
    services.create_comment(post_id, bot_id(db), 'my own comment')

    # Act
    outcome, logs = tick(Pacing(weights=REPLY_ONLY, cooldown_seconds=0))

    # Assert: it cannot reply to itself or comment twice here, so it ends up posting.
    replies = db.execute('SELECT COUNT(*) FROM comments WHERE parent_id IS NOT NULL').fetchone()[0]
    assert outcome == 'post'
    assert 'no comments to reply to' in logs[0]
    assert replies == 0


def test_a_bot_on_an_empty_site_posts_instead_of_skipping(db):
    # Arrange: a brand-new site has nothing to reply to and nothing to comment on.
    seed_bots([BOTS[0]])

    # Act
    outcome, logs = tick(Pacing(weights=REPLY_ONLY))

    # Assert: the whole chain is visible in the log, and a post was written.
    assert outcome == 'post'
    assert 'no comments to reply to' in logs[0]
    assert 'no posts left to comment on' in logs[0]
    assert db.execute('SELECT COUNT(*) FROM posts').fetchone()[0] == 1


def test_bots_reply_to_each_other(db):
    # Arrange: bot A comments; A is then on cooldown, so bot B must be the one to reply.
    seed_bots(BOTS[:2])
    human = add_human(db)
    services.create_post(human, 'Post', '<p>Body</p>')
    tick(Pacing(weights=COMMENT_ONLY))

    # Act
    outcome, logs = tick(Pacing(weights=REPLY_ONLY))

    # Assert
    parent, reply = db.execute('SELECT id, author_id, parent_id FROM comments ORDER BY id').fetchall()
    assert outcome == 'reply'
    assert reply[2] == parent[0]
    assert reply[1] != parent[1]
    assert {parent[1], reply[1]} == {bot_id(db, 0), bot_id(db, 1)}


def test_bot_replies_stop_at_the_depth_limit(db):
    # Arrange: a human thread two levels deep; with a limit of 1, only the top comment may get a reply.
    seed_bots([BOTS[0]])
    human = add_human(db)
    post_id = services.create_post(human, 'Post', '<p>Body</p>')
    top = services.create_comment(post_id, human, 'top')
    services.create_comment(post_id, human, 'reply', parent_id=top['id'])
    pacing = Pacing(weights=REPLY_ONLY, cooldown_seconds=0, max_reply_depth=1)

    # Act
    first, _ = tick(pacing)
    second, logs = tick(pacing)

    # Assert: the second time, the only reply target is too deep, so the bot comments on the post instead.
    bot_comments = db.execute(
        'SELECT parent_id FROM comments WHERE author_id = ? ORDER BY id', (bot_id(db),)
    ).fetchall()
    assert first == 'reply'
    assert second == 'comment'
    assert 'within the depth limit' in logs[0]
    assert bot_comments == [(top['id'],), (None,)]


def test_toxic_bot_text_is_skipped_and_not_stored(db):
    # Arrange
    seed_bots([BOTS[0]])
    human = add_human(db)
    services.create_post(human, 'Post', '<p>Body</p>')

    # Act
    outcome, logs = tick(Pacing(weights=COMMENT_ONLY), brain=ToxicBrain())

    # Assert
    assert outcome == 'rejected'
    assert 'toxicity' in logs[0]
    assert db.execute('SELECT COUNT(*) FROM comments').fetchone()[0] == 0


class UnreachableModerator:
    def check_toxicity(self, text):
        raise TimeoutError('read timed out')


def test_bot_action_is_skipped_when_moderation_is_unavailable(db, monkeypatch):
    # Arrange: bots never fall back to a weaker check; they skip instead.
    seed_bots([BOTS[0]])
    human = add_human(db)
    services.create_post(human, 'Post', '<p>Body</p>')
    monkeypatch.setattr(services, 'get_brain', lambda fallback=True: UnreachableModerator())

    # Act
    outcome, logs = tick(Pacing(weights=COMMENT_ONLY))

    # Assert
    assert outcome == 'moderation-error'
    assert 'moderation unavailable: read timed out' in logs[0]
    assert db.execute('SELECT COUNT(*) FROM comments').fetchone()[0] == 0


def test_a_skip_after_a_fallback_still_says_why_it_fell_back(db):
    # Arrange: an empty site forces reply -> comment -> post, and the post's text is rejected.
    seed_bots([BOTS[0]])

    class ToxicPoster(OfflineBrain):
        def write_post(self, personality, seed):
            post = super().write_post(personality, seed)
            return type(post)(title=post.title, body='you are an idiot')

    # Act
    outcome, logs = tick(Pacing(weights=REPLY_ONLY), brain=ToxicPoster())

    # Assert
    assert outcome == 'rejected'
    assert 'toxicity' in logs[0]
    assert 'no comments to reply to' in logs[0]


def test_brain_failure_is_skipped_not_crashed(db):
    # Arrange
    seed_bots([BOTS[0]])
    human = add_human(db)
    services.create_post(human, 'Post', '<p>Body</p>')

    # Act
    outcome, logs = tick(Pacing(weights=COMMENT_ONLY), brain=BrokenBrain())

    # Assert
    assert outcome == 'brain-error'
    assert 'brain unavailable: timeout' in logs[0]
    assert db.execute('SELECT COUNT(*) FROM comments').fetchone()[0] == 0
