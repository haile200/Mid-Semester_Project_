"""Integration tests for bot seeding: real SQL against the SQLite database from conftest.py."""
import pytest

import services
from bots.profiles import BOTS, BotProfile
from bots.seed import seed_bots

HUMAN = {'name': 'Real Person', 'email': 'person@example.com', 'password': 'Password123!'}


def bot_rows(db):
    return db.execute('SELECT email, name, bio, personality, is_bot FROM users WHERE is_bot = 1').fetchall()


def test_seeding_creates_every_bot_as_a_bot(db):
    # Arrange: an empty database

    # Act
    results = seed_bots()

    # Assert
    rows = bot_rows(db)
    assert len(rows) == len(BOTS)
    assert {row[0] for row in rows} == {bot.email for bot in BOTS}
    assert all(created for _, _, created in results)
    assert all(row[3] for row in rows)


def test_seeding_twice_creates_no_duplicates(db):
    # Arrange
    seed_bots()

    # Act
    second_run = seed_bots()

    # Assert
    assert len(bot_rows(db)) == len(BOTS)
    assert not any(created for _, _, created in second_run)


def test_reseeding_updates_a_changed_personality(db):
    # Arrange
    original = BOTS[0]
    seed_bots([original])
    edited = BotProfile(original.name, original.email, 'A new bio', 'A completely new personality.')

    # Act
    seed_bots([edited])

    # Assert
    row = db.execute('SELECT bio, personality FROM users WHERE email = ?', (original.email,)).fetchone()
    assert row == ('A new bio', 'A completely new personality.')


def test_seeding_refuses_to_turn_a_human_account_into_a_bot(client, db):
    # Arrange: a human registered with an email that a bot profile wants.
    client.post('/api/signup', json=HUMAN)
    claimed = BotProfile('Impostor Bot', HUMAN['email'], 'bio', 'personality')

    # Act and Assert
    with pytest.raises(ValueError, match='belongs to a human account'):
        services.upsert_bot(claimed.name, claimed.email, claimed.bio, claimed.personality)

    row = db.execute('SELECT name, is_bot, personality FROM users WHERE email = ?', (HUMAN['email'],)).fetchone()
    assert row == ('Real Person', 0, None)


def test_nobody_can_log_in_as_a_bot(client):
    # Arrange
    seed_bots()
    bot = BOTS[0]

    # Act: try the obvious guesses.
    responses = [client.post('/api/login', json={'email': bot.email, 'password': guess})
                 for guess in ('password', bot.name, bot.email, '')]

    # Assert: 401 for real guesses; 400 for the empty password, which never reaches the check.
    assert [r.status_code for r in responses] == [401, 401, 401, 400]


def test_bot_personality_is_not_exposed_by_the_api(client):
    # Arrange
    seed_bots()
    bot_id = client.get('/api/users', query_string={'search': BOTS[0].name}).get_json()[0]['id']

    # Act
    listing = client.get('/api/users?limit=50').get_json()
    profile = client.get(f'/api/users/{bot_id}').get_json()

    # Assert
    assert all('personality' not in user for user in listing)
    assert 'personality' not in profile
    assert profile['bio'] == BOTS[0].bio
