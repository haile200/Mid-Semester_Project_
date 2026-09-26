import os
import subprocess
import sys

import pytest

from brain import Brain, GeneratedPost, ToxicityResult, get_brain
from brain.offline import OfflineBrain, pick_voice
from utils import MAX_COMMENT_LENGTH

TRAD = 'The Trad Dad. Forty years of placing gear, distrusts bolts, loves a good hand crack.'
GYM = 'The Gym Boulderer. Lives at the climbing gym, talks in V-grades, waits for every new set.'
OTHER = 'The Weekend Warrior. Climbs whenever work allows and is happy just to be outside.'
MAX_TITLE_LENGTH = 255

brain = OfflineBrain()


# ---- The contract ----

def test_get_brain_returns_a_brain():
    # Arrange: nothing

    # Act
    result = get_brain()

    # Assert
    assert isinstance(result, Brain)


def test_provider_missing_an_operation_cannot_be_created():
    # Arrange: a provider that implements only one of the five operations.
    class IncompleteBrain(Brain):
        def check_toxicity(self, text):
            return ToxicityResult(allowed=True)

    # Act and Assert: the abstract base class refuses to build it.
    with pytest.raises(TypeError):
        IncompleteBrain()


# ---- check_toxicity ----

def test_check_toxicity_allows_normal_climbing_talk():
    # Arrange
    text = 'Sent it! The crux crimp was brutal but the rest was cruiser.'

    # Act
    result = brain.check_toxicity(text)

    # Assert
    assert result == ToxicityResult(allowed=True, reason=None)


@pytest.mark.parametrize('text', ['You are an idiot', 'IDIOT', 'what an idiot!!!', 'idiot, seriously'])
def test_check_toxicity_blocks_listed_words_in_any_case_or_punctuation(text):
    # Arrange: the parameters above

    # Act
    result = brain.check_toxicity(text)

    # Assert
    assert result == ToxicityResult(allowed=False, reason='Contains blocked language')


def test_check_toxicity_blocks_multi_word_phrases():
    # Arrange
    text = 'Just shut up about grades'

    # Act
    result = brain.check_toxicity(text)

    # Assert
    assert result.allowed is False


@pytest.mark.parametrize('text, allowed', [
    ('That is the move you hate. You will love the top.', True),
    ('I hate you.', False),
])
def test_check_toxicity_does_not_join_phrases_across_sentences(text, allowed):
    # Arrange: the parameters above

    # Act
    result = brain.check_toxicity(text)

    # Assert
    assert result.allowed is allowed


def test_check_toxicity_does_not_match_inside_other_words():
    # Arrange: "oxymoron" contains a blocked word but is not an insult.
    text = 'Calling that route a warm-up is an oxymoron.'

    # Act
    result = brain.check_toxicity(text)

    # Assert
    assert result.allowed is True


# ---- suggest_correction ----

@pytest.mark.parametrize('text, expected', [
    ('i love bouldring', 'I love bouldering'),
    ('Bouldring is life', 'Bouldering is life'),
    # Mid-sentence, so only the capital-keeping rule can produce the capital B.
    ('Best Bouldring Spots', 'Best Bouldering Spots'),
    ('great session. sent the roof! next week?', 'Great session. Sent the roof! Next week?'),
    ('too    many   spaces', 'Too many spaces'),
    ('Sent my project today.', 'Sent my project today.'),
])
def test_suggest_correction_fixes_common_mistakes(text, expected):
    # Arrange: the parameters above

    # Act
    result = brain.suggest_correction(text)

    # Assert
    assert result == expected


@pytest.mark.parametrize('text', ['i love bouldring', 'great session. sent it', '  alot of   chalk  '])
def test_suggest_correction_is_stable_when_applied_twice(text):
    # Arrange
    once = brain.suggest_correction(text)

    # Act
    twice = brain.suggest_correction(once)

    # Assert: a corrected text has nothing left to correct.
    assert twice == once


# ---- propose_comments ----

def test_propose_comments_returns_three_distinct_suggestions():
    # Arrange
    title, body = 'Finally sent my project', '<p>Took me <strong>six sessions</strong>.</p>'

    # Act
    result = brain.propose_comments(title, body)

    # Assert
    assert len(result) == 3
    assert len(set(result)) == 3
    assert all(suggestion.strip() for suggestion in result)


def test_propose_comments_is_deterministic():
    # Arrange
    title, body = 'Rest day', '<p>Skin needs a break.</p>'

    # Act
    first = brain.propose_comments(title, body)
    second = brain.propose_comments(title, body)

    # Assert
    assert first == second


# ---- write_post ----

def test_write_post_returns_a_valid_post():
    # Arrange: nothing

    # Act
    result = brain.write_post(TRAD, seed=0)

    # Assert
    assert isinstance(result, GeneratedPost)
    assert 0 < len(result.title) <= MAX_TITLE_LENGTH
    assert result.body.strip()


def test_write_post_is_deterministic_for_the_same_seed():
    # Arrange: nothing

    # Act
    first = brain.write_post(GYM, seed=7)
    second = brain.write_post(GYM, seed=7)

    # Assert
    assert first == second


def test_write_post_varies_with_the_seed():
    # Arrange
    seeds = range(10)

    # Act
    titles = {brain.write_post(GYM, seed).title for seed in seeds}
    bodies = {brain.write_post(GYM, seed).body for seed in seeds}

    # Assert
    assert len(titles) > 1
    assert len(bodies) > 1


@pytest.mark.parametrize('personality, voice', [
    (TRAD, 'trad'),
    (GYM, 'gym'),
    (OTHER, 'general'),
    ('THE TRAD DAD', 'trad'),
])
def test_pick_voice_follows_the_personality(personality, voice):
    # Arrange: the parameters above

    # Act
    result = pick_voice(personality)

    # Assert
    assert result == voice


# ---- write_reply ----

def test_write_reply_fits_in_a_comment_and_is_deterministic():
    # Arrange
    context = 'Where do you rest on this route?'

    # Act
    first = brain.write_reply(TRAD, context, seed=3)
    second = brain.write_reply(TRAD, context, seed=3)

    # Assert
    assert first == second
    assert 0 < len(first) <= MAX_COMMENT_LENGTH


def test_write_reply_varies_with_the_seed():
    # Arrange
    context = 'Nice send!'

    # Act
    replies = {brain.write_reply(GYM, context, seed) for seed in range(10)}

    # Assert
    assert len(replies) > 1


# ---- Properties across many inputs ----

@pytest.mark.parametrize('personality', [TRAD, GYM, OTHER])
def test_generated_text_never_trips_the_toxicity_check(personality):
    # Arrange: bots skip any action whose text is blocked, so a template that
    # tripped the filter would silently stop a bot from ever using it.
    outputs = []
    for seed in range(50):
        post = brain.write_post(personality, seed)
        outputs += [post.title, post.body, brain.write_reply(personality, 'Nice send', seed)]
        outputs += brain.propose_comments(post.title, post.body)

    # Act
    blocked = [text for text in outputs if not brain.check_toxicity(text).allowed]

    # Assert
    assert blocked == []


def test_output_does_not_depend_on_python_hash_randomization():
    # Arrange: Python scrambles str hashes per process; PYTHONHASHSEED fixes the scramble.
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    script = (
        'import sys; sys.path.insert(0, sys.argv[1]);'
        'from brain.offline import OfflineBrain; b = OfflineBrain();'
        'print(b.propose_comments("Rest day", "<p>Skin needs a break.</p>"));'
        'print(b.write_post("A climber who loves long days outside", 4))'
    )

    def run_with_hash_seed(value):
        env = {**os.environ, 'PYTHONHASHSEED': value}
        return subprocess.run([sys.executable, '-c', script, backend_dir], env=env,
                               capture_output=True, text=True, check=True).stdout

    # Act
    first = run_with_hash_seed('1')
    second = run_with_hash_seed('2')

    # Assert
    assert first == second
