"""Integration tests for likes, follower lists and suggested users, against SQLite.

Each person gets their own test client, so each has their own session cookie.
"""
import random

import pytest

import services
from app import app
from bots.profiles import BOTS
from bots.seed import seed_bots
from bots.worker import Pacing, run_tick
from brain import OfflineBrain


def person(name):
    return {'name': name, 'email': f'{name.lower()}@example.com', 'password': 'Password123!'}


ALICE, BOB, CAROL, DAN = person('Alice'), person('Bob'), person('Carol'), person('Dan')


def signed_in(someone):
    client = app.test_client()
    client.post('/api/signup', json=someone)
    client.post('/api/login', json={'email': someone['email'], 'password': someone['password']})
    return client


def user_id(db, someone):
    return db.execute('SELECT id FROM users WHERE email = ?', (someone['email'],)).fetchone()[0]


def write_post(client, title='A send'):
    return client.post('/api/posts', json={'title': title, 'body': '<p>Body</p>'}).get_json()['postId']


def follow(client, target_id):
    return client.post(f'/api/follow/{target_id}')


def tick(pacing):
    logs = []
    outcome = run_tick(1, OfflineBrain(), random.Random(1), pacing, logs.append)
    return outcome, logs


# ---- Likes ----

def test_liking_requires_login(db):
    # Arrange
    post_id = write_post(signed_in(ALICE))

    # Act
    response = app.test_client().put(f'/api/posts/{post_id}/like')

    # Assert
    assert response.status_code == 401


def test_like_and_unlike_update_the_count(db):
    # Arrange
    post_id = write_post(signed_in(ALICE))
    bob = signed_in(BOB)

    # Act
    liked = bob.put(f'/api/posts/{post_id}/like')
    unliked = bob.delete(f'/api/posts/{post_id}/like')

    # Assert
    assert liked.status_code == 200
    assert liked.get_json() == {'liked': True, 'likeCount': 1}
    assert unliked.get_json() == {'liked': False, 'likeCount': 0}


def test_liking_twice_counts_once(db):
    # Arrange: PUT means "make it so", so repeating it must not add a second like.
    post_id = write_post(signed_in(ALICE))
    bob = signed_in(BOB)
    bob.put(f'/api/posts/{post_id}/like')

    # Act
    second = bob.put(f'/api/posts/{post_id}/like')

    # Assert
    assert second.get_json() == {'liked': True, 'likeCount': 1}
    assert db.execute('SELECT COUNT(*) FROM likes').fetchone()[0] == 1


def test_unliking_without_a_like_is_harmless(db):
    # Arrange
    post_id = write_post(signed_in(ALICE))

    # Act
    response = signed_in(BOB).delete(f'/api/posts/{post_id}/like')

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {'liked': False, 'likeCount': 0}


@pytest.mark.parametrize('method', ['put', 'delete'])
def test_liking_a_missing_post_returns_404(db, method):
    # Arrange
    bob = signed_in(BOB)

    # Act
    response = getattr(bob, method)('/api/posts/9999/like')

    # Assert
    assert response.status_code == 404
    assert response.get_json() == {'message': 'Post not found'}


def test_the_feed_shows_the_count_and_the_viewers_own_like(db):
    # Arrange: Bob and Carol like Alice's post; Alice does not.
    alice = signed_in(ALICE)
    post_id = write_post(alice)
    bob = signed_in(BOB)
    bob.put(f'/api/posts/{post_id}/like')
    signed_in(CAROL).put(f'/api/posts/{post_id}/like')

    # Act
    as_bob = bob.get('/api/feed').get_json()[0]
    as_alice = alice.get('/api/feed').get_json()[0]
    as_visitor = app.test_client().get('/api/feed').get_json()[0]
    on_profile = bob.get(f'/api/posts?userId={user_id(db, ALICE)}').get_json()[0]

    # Assert
    assert (as_bob['likeCount'], as_bob['likedByMe']) == (2, True)
    assert (as_alice['likeCount'], as_alice['likedByMe']) == (2, False)
    assert (as_visitor['likeCount'], as_visitor['likedByMe']) == (2, False)
    assert on_profile['likedByMe'] is True


# ---- Follower lists ----

def test_followers_and_following_lists(db):
    # Arrange: Bob and Carol follow Alice; Alice follows Carol.
    alice, bob, carol = signed_in(ALICE), signed_in(BOB), signed_in(CAROL)
    alice_id, carol_id = user_id(db, ALICE), user_id(db, CAROL)
    follow(bob, alice_id)
    follow(carol, alice_id)
    follow(alice, carol_id)
    visitor = app.test_client()

    # Act
    followers = visitor.get(f'/api/users/{alice_id}/followers').get_json()
    following = visitor.get(f'/api/users/{alice_id}/following').get_json()

    # Assert: the lists are public, but never expose emails.
    assert {u['name'] for u in followers} == {'Bob', 'Carol'}
    assert [u['name'] for u in following] == ['Carol']
    assert all(set(u) == {'id', 'name', 'profile_picture', 'is_bot'} for u in followers + following)


@pytest.mark.parametrize('kind', ['followers', 'following'])
def test_follower_lists_of_a_missing_user_return_404(db, kind):
    # Arrange: an empty database

    # Act
    response = app.test_client().get(f'/api/users/9999/{kind}')

    # Assert
    assert response.status_code == 404
    assert response.get_json() == {'message': 'User not found'}


def test_follower_lists_reject_bad_pagination(db):
    # Arrange
    signed_in(ALICE)

    # Act
    response = app.test_client().get(f'/api/users/{user_id(db, ALICE)}/followers?limit=abc')

    # Assert
    assert response.status_code == 400


# ---- Suggested users ----

def test_suggestions_require_login(db):
    # Arrange: nobody is logged in

    # Act
    response = app.test_client().get('/api/users/suggestions')

    # Assert
    assert response.status_code == 401


def test_suggestions_rank_by_mutual_follows_then_popularity(db):
    # Arrange: I follow A and B. Both follow X, only A follows Y. Z is popular but unconnected to me.
    me, a, b, x, y, z, c = (person(n) for n in ('Me', 'A', 'B', 'X', 'Y', 'Z', 'C'))
    clients = {p['name']: signed_in(p) for p in (me, a, b, x, y, z, c)}
    ids = {p['name']: user_id(db, p) for p in (me, a, b, x, y, z, c)}
    for follower, target in [('Me', 'A'), ('Me', 'B'), ('A', 'X'), ('B', 'X'), ('A', 'Y'), ('C', 'Z'), ('Y', 'Z')]:
        follow(clients[follower], ids[target])

    # Act
    suggestions = clients['Me'].get('/api/users/suggestions?limit=10').get_json()

    # Assert: X (2 mutual), Y (1 mutual), then Z (2 followers), then C (nothing).
    assert [s['name'] for s in suggestions] == ['X', 'Y', 'Z', 'C']
    assert [s['mutualCount'] for s in suggestions] == [2, 1, 0, 0]


def test_suggestions_skip_yourself_people_you_follow_and_banned_users(db):
    # Arrange
    me = signed_in(ALICE)
    for someone in (BOB, CAROL, DAN):
        signed_in(someone)
    follow(me, user_id(db, BOB))
    services.ban_user(user_id(db, CAROL), admin_id=-1)

    # Act
    names = [s['name'] for s in me.get('/api/users/suggestions').get_json()]

    # Assert
    assert names == ['Dan']


def test_suggestions_respect_the_limit_and_reject_bad_ones(db):
    # Arrange
    me = signed_in(ALICE)
    for someone in (BOB, CAROL, DAN):
        signed_in(someone)

    # Act
    two = me.get('/api/users/suggestions?limit=2')
    bad = me.get('/api/users/suggestions?limit=abc')
    too_many = me.get('/api/users/suggestions?limit=500')

    # Assert
    assert len(two.get_json()) == 2
    assert (bad.status_code, too_many.status_code) == (400, 400)


# ---- Bots ----

def test_a_bot_likes_a_post(db):
    # Arrange
    seed_bots([BOTS[0]])
    post_id = write_post(signed_in(ALICE))

    # Act
    outcome, logs = tick(Pacing(weights={'like': 1}))

    # Assert
    bot = db.execute('SELECT id FROM users WHERE email = ?', (BOTS[0].email,)).fetchone()[0]
    assert outcome == 'like'
    assert db.execute('SELECT user_id, post_id FROM likes').fetchall() == [(bot, post_id)]
    assert 'liked' in logs[0]


def test_a_bot_never_likes_its_own_post_or_the_same_post_twice(db):
    # Arrange: the bot has already liked the only post it may like.
    seed_bots([BOTS[0]])
    bot = db.execute('SELECT id FROM users WHERE email = ?', (BOTS[0].email,)).fetchone()[0]
    post_id = write_post(signed_in(ALICE))
    services.create_post(bot, 'My own post', '<p>Body</p>')
    services.like_post(bot, post_id)

    # Act
    outcome, logs = tick(Pacing(weights={'like': 1}, cooldown_seconds=0))

    # Assert: nothing left to like, so the bot writes a post instead.
    assert outcome == 'post'
    assert 'no posts left to like' in logs[0]
    assert db.execute('SELECT COUNT(*) FROM likes').fetchone()[0] == 1


def test_likes_count_toward_a_bots_cooldown(db):
    # Arrange
    seed_bots([BOTS[0]])
    write_post(signed_in(ALICE))
    tick(Pacing(weights={'like': 1}))

    # Act
    outcome, logs = tick(Pacing(weights={'like': 1}, cooldown_seconds=600))

    # Assert
    assert outcome == 'skip'
    assert 'cooldown' in logs[0]
