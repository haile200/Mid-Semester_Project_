"""Integration tests for the bot worker: run_tick and its queries against the SQLite database from conftest.py."""
import random

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
    assert 'no bots seeded' in logs[0]


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

    # Assert
    assert outcome == 'nothing'
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
    assert outcome == 'nothing'
    assert 'no posts left to comment on' in logs[0]


def test_bot_never_replies_to_itself(db):
    # Arrange: the only comment belongs to the bot.
    seed_bots([BOTS[0]])
    human = add_human(db)
    post_id = services.create_post(human, 'Post', '<p>Body</p>')
    services.create_comment(post_id, bot_id(db), 'my own comment')

    # Act
    outcome, logs = tick(Pacing(weights=REPLY_ONLY, cooldown_seconds=0))

    # Assert
    assert outcome == 'nothing'
    assert 'no comments to reply to' in logs[0]


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

    # Assert
    bot_reply = db.execute('SELECT parent_id FROM comments WHERE author_id = ?', (bot_id(db),)).fetchall()
    assert first == 'reply'
    assert bot_reply == [(top['id'],)]
    assert second == 'nothing'
    assert 'within the depth limit' in logs[0]


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
