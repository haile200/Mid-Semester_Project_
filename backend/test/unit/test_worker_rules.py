import random
from collections import Counter
from datetime import datetime, timedelta

import pytest

from bots.worker import (
    BotState,
    Pacing,
    choose_action,
    choose_bot,
    parse_args,
    reply_allowed,
    skip_reason,
    sleep_seconds,
    to_post_html,
)

NOW = datetime(2026, 9, 26, 12, 0, 0)
PACING = Pacing(cooldown_seconds=600, daily_cap=5, max_reply_depth=3)


def bot(bot_id=1, idle_seconds=None, recent_actions=0):
    last = None if idle_seconds is None else NOW - timedelta(seconds=idle_seconds)
    return BotState(id=bot_id, name=f'Bot {bot_id}', personality='p', last_action_at=last, recent_actions=recent_actions)


# ---- skip_reason ----

@pytest.mark.parametrize('state, expected', [
    (bot(idle_seconds=None), None),
    (bot(idle_seconds=599), 'cooldown'),
    (bot(idle_seconds=600), None),
    (bot(idle_seconds=5000, recent_actions=5), 'daily cap reached'),
    (bot(idle_seconds=10, recent_actions=5), 'daily cap reached'),
])
def test_skip_reason_applies_cooldown_and_daily_cap(state, expected):
    # Arrange: the parameters above

    # Act
    result = skip_reason(state, NOW, PACING)

    # Assert
    assert result == expected


# ---- choose_bot ----

def test_choose_bot_returns_none_when_every_bot_is_resting():
    # Arrange
    bots = [bot(1, idle_seconds=10), bot(2, recent_actions=5)]

    # Act
    result = choose_bot(bots, NOW, PACING, random.Random(0))

    # Assert
    assert result is None


def test_choose_bot_never_picks_a_resting_bot():
    # Arrange
    bots = [bot(1, idle_seconds=10), bot(2, idle_seconds=5000), bot(3, recent_actions=5)]

    # Act
    chosen = {choose_bot(bots, NOW, PACING, random.Random(seed)).id for seed in range(200)}

    # Assert
    assert chosen == {2}


def test_choose_bot_prefers_the_bots_idle_longest():
    # Arrange: five eligible bots; ids 4 and 5 acted most recently.
    bots = [bot(1, idle_seconds=None), bot(2, idle_seconds=9000), bot(3, idle_seconds=8000),
            bot(4, idle_seconds=2000), bot(5, idle_seconds=1000)]

    # Act
    chosen = {choose_bot(bots, NOW, PACING, random.Random(seed)).id for seed in range(500)}

    # Assert: only the three idle longest ever get picked.
    assert chosen == {1, 2, 3}


# ---- choose_action ----

def test_choose_action_never_picks_a_zero_weight_action():
    # Arrange
    weights = {'post': 0, 'comment': 1, 'reply': 0}

    # Act
    chosen = {choose_action(random.Random(seed), weights) for seed in range(200)}

    # Assert
    assert chosen == {'comment'}


def test_choose_action_follows_the_weights():
    # Arrange
    rng = random.Random(42)
    weights = {'post': 0.2, 'comment': 0.5, 'reply': 0.3}

    # Act
    counts = Counter(choose_action(rng, weights) for _ in range(10000))

    # Assert: within three percentage points of the requested mix.
    for action, weight in weights.items():
        assert abs(counts[action] / 10000 - weight) < 0.03


# ---- reply_allowed ----

@pytest.mark.parametrize('parent_depth, allowed', [(0, True), (2, True), (3, False), (7, False)])
def test_reply_allowed_stops_threads_at_the_maximum_depth(parent_depth, allowed):
    # Arrange: max_reply_depth is 3, so a reply may sit at depth 3 but not deeper.

    # Act
    result = reply_allowed(parent_depth, PACING)

    # Assert
    assert result is allowed


# ---- sleep_seconds ----

def test_sleep_seconds_stays_within_the_configured_range():
    # Arrange
    pacing = Pacing(min_sleep=5, max_sleep=15)
    rng = random.Random(7)

    # Act
    pauses = [sleep_seconds(rng, pacing) for _ in range(1000)]

    # Assert: inside the range, and actually random rather than fixed.
    assert all(5 <= pause <= 15 for pause in pauses)
    assert len({round(pause, 3) for pause in pauses}) > 100


# ---- to_post_html ----

def test_to_post_html_wraps_and_escapes_plain_text():
    # Arrange: the brain returns plain text, so markup characters must be shown, not interpreted.
    text = 'Grades: 5.10 < 5.11 & "sandbagged"'

    # Act
    result = to_post_html(text)

    # Assert
    assert result == '<p>Grades: 5.10 &lt; 5.11 &amp; &quot;sandbagged&quot;</p>'


# ---- parse_args ----

def test_parse_args_rejects_a_minimum_sleep_above_the_maximum():
    # Arrange
    argv = ['--min-sleep', '20', '--max-sleep', '10']

    # Act and Assert
    with pytest.raises(SystemExit):
        parse_args(argv)


def test_parse_args_builds_pacing_from_flags():
    # Arrange
    argv = ['--min-sleep', '5', '--max-sleep', '15', '--cooldown', '60', '--daily-cap', '3', '--ticks', '4']

    # Act
    args, pacing = parse_args(argv)

    # Assert
    assert (pacing.min_sleep, pacing.max_sleep, pacing.cooldown_seconds, pacing.daily_cap) == (5, 15, 60, 3)
    assert args.ticks == 4
