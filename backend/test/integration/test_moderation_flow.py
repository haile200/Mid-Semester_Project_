"""Integration tests for moderation: reports, admin-only endpoints and bans, against SQLite.

Each person gets their own test client, so each has their own session cookie, like separate browsers.
"""
import random

import pytest

import services
from app import app
from bots.profiles import BOTS
from bots.seed import seed_bots
from bots.worker import Pacing, run_tick
from brain import OfflineBrain
from moderation.admins import main as admins_command

ALICE = {'name': 'Alice', 'email': 'alice@example.com', 'password': 'Password123!'}
BOB = {'name': 'Bob', 'email': 'bob@example.com', 'password': 'Password123!'}
CAROL = {'name': 'Carol', 'email': 'carol@example.com', 'password': 'Password123!'}
MOD = {'name': 'Mod', 'email': 'mod@example.com', 'password': 'Password123!'}
MOD_TWO = {'name': 'Mod Two', 'email': 'mod2@example.com', 'password': 'Password123!'}


def signed_in(person, admin=False):
    """A separate browser session, signed up and logged in as `person`."""
    client = app.test_client()
    client.post('/api/signup', json=person)
    if admin:
        services.set_admin(person['email'], True)
    client.post('/api/login', json={'email': person['email'], 'password': person['password']})
    return client


def log_in(person, password=None):
    return app.test_client().post('/api/login', json={'email': person['email'], 'password': password or person['password']})


def user_id(db, person):
    return db.execute('SELECT id FROM users WHERE email = ?', (person['email'],)).fetchone()[0]


def write_post(client):
    return client.post('/api/posts', json={'title': 'My send', 'body': '<p>Hard one.</p>'}).get_json()['postId']


def report(client, post_id, reason='spam', note=None):
    payload = {'reason': reason}
    if note is not None:
        payload['note'] = note
    return client.post(f'/api/posts/{post_id}/reports', json=payload)


# ---- Reporting ----

def test_reporting_requires_login(db):
    # Arrange
    post_id = write_post(signed_in(ALICE))

    # Act
    response = report(app.test_client(), post_id)

    # Assert
    assert response.status_code == 401


def test_a_report_is_stored_as_open(db):
    # Arrange
    post_id = write_post(signed_in(ALICE))
    bob = signed_in(BOB)

    # Act
    response = report(bob, post_id, 'harassment', '  targets a user  ')

    # Assert
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Report received'
    assert db.execute('SELECT reason, note, status FROM reports').fetchone() == ('harassment', 'targets a user', 'open')


def test_reporting_the_same_post_twice_is_a_conflict(db):
    # Arrange
    post_id = write_post(signed_in(ALICE))
    bob = signed_in(BOB)
    report(bob, post_id)

    # Act
    second = report(bob, post_id, 'other')

    # Assert
    assert second.status_code == 409
    assert second.get_json() == {'message': 'You already reported this post'}
    assert db.execute('SELECT COUNT(*) FROM reports').fetchone()[0] == 1


@pytest.mark.parametrize('payload, message', [
    ({'reason': 'boring'}, 'Choose a reason: spam, harassment, hate or other'),
    ({'reason': 'spam', 'note': 'x' * 301}, 'Note must be 300 characters or fewer'),
    ({}, 'Invalid JSON payload'),
])
def test_a_report_with_bad_input_is_rejected(db, payload, message):
    # Arrange
    post_id = write_post(signed_in(ALICE))
    bob = signed_in(BOB)

    # Act
    response = bob.post(f'/api/posts/{post_id}/reports', json=payload)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': message}


def test_you_cannot_report_your_own_post(db):
    # Arrange
    alice = signed_in(ALICE)
    post_id = write_post(alice)

    # Act
    response = report(alice, post_id)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'You cannot report your own post'}


def test_reporting_a_missing_post_returns_404(db):
    # Arrange
    bob = signed_in(BOB)

    # Act
    response = report(bob, 9999)

    # Assert
    assert response.status_code == 404
    assert response.get_json() == {'message': 'Post not found'}


# ---- Who may use the dashboard ----

@pytest.mark.parametrize('who, status', [('anonymous', 401), ('user', 403), ('admin', 200)])
def test_the_dashboard_is_for_admins_only(db, who, status):
    # Arrange: 401 means "who are you?", 403 means "we know you, and the answer is no".
    clients = {
        'anonymous': app.test_client,
        'user': lambda: signed_in(BOB),
        'admin': lambda: signed_in(MOD, admin=True),
    }

    # Act
    response = clients[who]().get('/api/admin/reports')

    # Assert
    assert response.status_code == status
    if status == 403:
        assert response.get_json() == {'message': 'Admin access required'}


def test_login_tells_the_frontend_who_is_an_admin(db):
    # Arrange
    signed_in(MOD, admin=True)
    signed_in(BOB)

    # Act
    moderator, regular = log_in(MOD).get_json()['user'], log_in(BOB).get_json()['user']

    # Assert
    assert moderator['is_admin'] is True
    assert regular['is_admin'] is False


def test_the_dashboard_groups_open_reports_by_post(db):
    # Arrange: two people report the same post.
    post_id = write_post(signed_in(ALICE))
    report(signed_in(BOB), post_id, 'spam')
    report(signed_in(CAROL), post_id, 'hate', 'slur in the title')
    mod = signed_in(MOD, admin=True)

    # Act
    groups = mod.get('/api/admin/reports').get_json()

    # Assert
    assert len(groups) == 1
    group = groups[0]
    assert group['post']['id'] == post_id
    assert group['post']['author']['name'] == 'Alice'
    assert group['post']['author']['is_banned'] is False
    assert sorted(r['reason'] for r in group['reports']) == ['hate', 'spam']
    assert {r['reporter_name'] for r in group['reports']} == {'Bob', 'Carol'}


# ---- Moderator actions ----

def test_dismissing_clears_the_reports_from_the_dashboard(db):
    # Arrange
    post_id = write_post(signed_in(ALICE))
    report(signed_in(BOB), post_id)
    mod = signed_in(MOD, admin=True)

    # Act
    response = mod.patch(f'/api/admin/posts/{post_id}/reports', json={'status': 'dismissed'})

    # Assert: the report is kept for the record, but no longer open.
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Reports dismissed', 'dismissed': 1}
    assert mod.get('/api/admin/reports').get_json() == []
    status, reviewer = db.execute('SELECT status, reviewed_by FROM reports').fetchone()
    assert (status, reviewer) == ('dismissed', user_id(db, MOD))


def test_dismissing_needs_a_valid_status_and_an_existing_post(db):
    # Arrange
    post_id = write_post(signed_in(ALICE))
    mod = signed_in(MOD, admin=True)

    # Act
    wrong_status = mod.patch(f'/api/admin/posts/{post_id}/reports', json={'status': 'open'})
    missing_post = mod.patch('/api/admin/posts/9999/reports', json={'status': 'dismissed'})

    # Assert
    assert wrong_status.status_code == 400
    assert missing_post.status_code == 404


def test_deleting_a_post_removes_it(db):
    # Arrange
    post_id = write_post(signed_in(ALICE))
    mod = signed_in(MOD, admin=True)

    # Act
    first = mod.delete(f'/api/admin/posts/{post_id}')
    second = mod.delete(f'/api/admin/posts/{post_id}')

    # Assert
    assert first.status_code == 200
    assert first.get_json() == {'message': 'Post deleted'}
    assert db.execute('SELECT COUNT(*) FROM posts').fetchone()[0] == 0
    assert second.status_code == 404


def test_regular_users_cannot_use_moderator_actions(db):
    # Arrange
    post_id = write_post(signed_in(ALICE))
    bob = signed_in(BOB)
    alice_id = user_id(db, ALICE)

    # Act
    responses = [
        bob.patch(f'/api/admin/posts/{post_id}/reports', json={'status': 'dismissed'}),
        bob.delete(f'/api/admin/posts/{post_id}'),
        bob.put(f'/api/admin/users/{alice_id}/ban'),
    ]

    # Assert: refused, and nothing changed.
    assert [r.status_code for r in responses] == [403, 403, 403]
    assert db.execute('SELECT COUNT(*) FROM posts').fetchone()[0] == 1
    assert db.execute('SELECT COUNT(*) FROM users WHERE banned_at IS NOT NULL').fetchone()[0] == 0


# ---- Bans ----

def test_banning_logs_the_user_out_and_blocks_login(db):
    # Arrange
    alice = signed_in(ALICE)
    mod = signed_in(MOD, admin=True)

    # Act
    response = mod.put(f'/api/admin/users/{user_id(db, ALICE)}/ban')

    # Assert
    assert response.status_code == 200
    assert response.get_json()['user']['banned'] is True
    assert alice.get('/api/auth/me').status_code == 401
    # Checked on its own: the session lookup also ignores banned users, which would hide a missing cleanup.
    assert db.execute('SELECT COUNT(*) FROM sessions WHERE user_id = ?', (user_id(db, ALICE),)).fetchone()[0] == 0
    relogin = log_in(ALICE)
    assert relogin.status_code == 403
    assert relogin.get_json() == {'message': 'This account has been banned'}


def test_a_wrong_password_does_not_reveal_a_ban(db):
    # Arrange: only someone who knows the password should learn that the account is banned.
    signed_in(ALICE)
    signed_in(MOD, admin=True).put(f'/api/admin/users/{user_id(db, ALICE)}/ban')

    # Act
    response = log_in(ALICE, password='WrongPassword1!')

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Invalid credentials'}


def test_a_leftover_session_of_a_banned_user_is_ignored(db):
    # Arrange: the account is banned without its sessions being removed.
    alice = signed_in(ALICE)
    db.execute('UPDATE users SET banned_at = CURRENT_TIMESTAMP WHERE email = ?', (ALICE['email'],))
    db.commit()

    # Act
    response = alice.get('/api/auth/me')

    # Assert
    assert response.status_code == 401


def test_unbanning_restores_login(db):
    # Arrange
    signed_in(ALICE)
    mod = signed_in(MOD, admin=True)
    mod.put(f'/api/admin/users/{user_id(db, ALICE)}/ban')

    # Act
    response = mod.delete(f'/api/admin/users/{user_id(db, ALICE)}/ban')

    # Assert
    assert response.status_code == 200
    assert response.get_json()['user']['banned'] is False
    assert log_in(ALICE).status_code == 200


@pytest.mark.parametrize('target, message', [
    ('self', 'You cannot ban yourself'),
    ('other admin', 'Admins cannot be banned. Revoke their admin rights first.'),
])
def test_admins_cannot_ban_themselves_or_other_admins(db, target, message):
    # Arrange
    mod = signed_in(MOD, admin=True)
    signed_in(MOD_TWO, admin=True)
    target_id = user_id(db, MOD if target == 'self' else MOD_TWO)

    # Act
    response = mod.put(f'/api/admin/users/{target_id}/ban')

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': message}


def test_banning_twice_is_harmless(db):
    # Arrange: PUT means "make it so", so repeating it must give the same result.
    signed_in(ALICE)
    mod = signed_in(MOD, admin=True)
    url = f'/api/admin/users/{user_id(db, ALICE)}/ban'

    # Act
    first, second = mod.put(url), mod.put(url)

    # Assert
    assert (first.status_code, second.status_code) == (200, 200)


def test_banning_a_missing_user_returns_404(db):
    # Arrange
    mod = signed_in(MOD, admin=True)

    # Act
    response = mod.put('/api/admin/users/9999/ban')

    # Assert
    assert response.status_code == 404
    assert response.get_json() == {'message': 'User not found'}


# ---- The bot worker ----

def test_a_banned_bot_stops_acting(db):
    # Arrange
    seed_bots([BOTS[0]])
    bot_id = db.execute('SELECT id FROM users WHERE email = ?', (BOTS[0].email,)).fetchone()[0]
    services.ban_user(bot_id, admin_id=-1)
    logs = []

    # Act
    outcome = run_tick(1, OfflineBrain(), random.Random(1), Pacing(), logs.append)

    # Assert
    assert outcome == 'skip'
    assert 'no active bots' in logs[0]


# ---- The admin command ----

def test_the_admin_command_grants_lists_and_revokes(db, capsys):
    # Arrange
    services.create_user('Future Mod', 'future@example.com', 'Password123!')

    # Act
    granted = admins_command(['grant', 'future@example.com'])
    is_admin_after_grant = db.execute("SELECT is_admin FROM users WHERE email = 'future@example.com'").fetchone()[0]
    admins_command(['list'])
    listing = capsys.readouterr().out
    revoked = admins_command(['revoke', 'future@example.com'])
    is_admin_after_revoke = db.execute("SELECT is_admin FROM users WHERE email = 'future@example.com'").fetchone()[0]

    # Assert
    assert (granted, revoked) == (0, 0)
    assert (is_admin_after_grant, is_admin_after_revoke) == (1, 0)
    assert 'future@example.com' in listing


def test_the_admin_command_refuses_unknown_emails_and_bots(db):
    # Arrange
    seed_bots([BOTS[0]])

    # Act
    unknown = admins_command(['grant', 'nobody@example.com'])
    bot = admins_command(['grant', BOTS[0].email])

    # Assert
    assert (unknown, bot) == (1, 1)
    assert db.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1').fetchone()[0] == 0
