from bots.profiles import BOTS
from brain.offline import OfflineBrain, pick_voice
from utils import is_valid_email


def test_there_are_at_least_ten_bots():
    # Arrange: nothing

    # Act
    count = len(BOTS)

    # Assert
    assert count >= 10


def test_bot_names_and_emails_are_unique():
    # Arrange
    names = [bot.name for bot in BOTS]
    emails = [bot.email.lower() for bot in BOTS]

    # Act and Assert
    assert len(set(names)) == len(names)
    assert len(set(emails)) == len(emails)


def test_bot_emails_are_valid_and_use_the_reserved_test_domain():
    # Arrange: .test is reserved (RFC 2606), so it can never be someone's real mailbox.

    # Act
    invalid = [bot.email for bot in BOTS if not is_valid_email(bot.email) or not bot.email.endswith('.test')]

    # Assert
    assert invalid == []


def test_bot_fields_fit_the_database_columns():
    # Arrange: name VARCHAR(255); bio is shown on the profile page, so keep it short.

    # Act
    too_long = [bot.name for bot in BOTS if len(bot.name) > 255 or len(bot.bio) > 500]
    empty = [bot.name for bot in BOTS if not (bot.name.strip() and bot.bio.strip() and bot.personality.strip())]

    # Assert
    assert too_long == []
    assert empty == []


def test_bots_cover_every_offline_voice():
    # Arrange

    # Act
    voices = {pick_voice(bot.personality) for bot in BOTS}

    # Assert: a world of identical voices would not be much of a world.
    assert voices == {'trad', 'gym', 'general'}


def test_bot_profile_text_passes_the_toxicity_check():
    # Arrange
    brain = OfflineBrain()

    # Act
    blocked = [bot.name for bot in BOTS
               if not all(brain.check_toxicity(text).allowed for text in (bot.name, bot.bio, bot.personality))]

    # Assert
    assert blocked == []
