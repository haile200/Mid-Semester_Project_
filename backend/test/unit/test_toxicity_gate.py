from unittest.mock import MagicMock

import pytest

import services
from brain import ToxicityResult
from services import ContentRejected


class RecordingBrain:
    """Stands in for any provider: records what it was asked and answers as told."""

    def __init__(self, allowed):
        self.allowed = allowed
        self.checked = []

    def check_toxicity(self, text):
        self.checked.append(text)
        if self.allowed:
            return ToxicityResult(allowed=True)
        return ToxicityResult(allowed=False, reason='Contains blocked language')


class FailingBrain:
    def check_toxicity(self, text):
        raise TimeoutError('read timed out')


@pytest.fixture
def rejecting_brain(monkeypatch):
    brain = RecordingBrain(allowed=False)
    monkeypatch.setattr(services, 'get_brain', lambda fallback=True: brain)
    return brain


@pytest.fixture
def get_db(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(services, 'get_db', fake)
    return fake


def test_content_rejected_is_a_value_error():
    # Arrange: routes already turn ValueError into a 400 response.

    # Act
    result = issubclass(ContentRejected, ValueError)

    # Assert
    assert result is True


def test_rejected_comment_never_touches_the_database(rejecting_brain, get_db):
    # Arrange: fixtures above

    # Act and Assert
    with pytest.raises(ContentRejected, match='Not published: contains blocked language'):
        services.create_comment(post_id=1, author_id=2, body='some text')

    get_db.assert_not_called()


def test_comment_is_checked_after_cleaning(rejecting_brain, get_db):
    # Arrange
    body = '   nice send   '

    # Act
    with pytest.raises(ContentRejected):
        services.create_comment(post_id=1, author_id=2, body=body)

    # Assert: the check sees exactly the text that would be stored.
    assert rejecting_brain.checked == ['nice send']


def test_invalid_comment_is_refused_before_the_check(rejecting_brain, get_db):
    # Arrange: empty text never needs a (possibly slow, paid) check.
    body = '   '

    # Act
    with pytest.raises(ValueError, match='Comment cannot be empty'):
        services.create_comment(post_id=1, author_id=2, body=body)

    # Assert
    assert rejecting_brain.checked == []


def test_rejected_post_never_touches_the_database(rejecting_brain, get_db):
    # Arrange: fixtures above

    # Act and Assert
    with pytest.raises(ContentRejected):
        services.create_post(author_id=1, title='My title', body='<p>Body</p>')

    get_db.assert_not_called()


def test_post_is_checked_as_title_and_plain_text_body(rejecting_brain, get_db):
    # Arrange
    body = '<p>Hello <strong>wor</strong>ld</p><p>Second</p>'

    # Act
    with pytest.raises(ContentRejected):
        services.create_post(author_id=1, title='My title', body=body)

    # Assert
    assert rejecting_brain.checked == ['My title\nHello world Second']


@pytest.mark.parametrize('strict, expected_fallback', [(False, True), (True, False)])
def test_strict_mode_asks_for_a_brain_without_fallback(monkeypatch, get_db, strict, expected_fallback):
    # Arrange
    requested = []
    brain = RecordingBrain(allowed=False)
    monkeypatch.setattr(services, 'get_brain', lambda fallback=True: requested.append(fallback) or brain)

    # Act
    with pytest.raises(ContentRejected):
        services.create_comment(post_id=1, author_id=2, body='text', strict=strict)

    # Assert
    assert requested == [expected_fallback]


def test_strict_mode_reports_a_failed_check_instead_of_publishing(monkeypatch, get_db):
    # Arrange: bots use strict mode, so a broken check must stop them, not wave them through.
    monkeypatch.setattr(services, 'get_brain', lambda fallback=True: FailingBrain())

    # Act and Assert
    with pytest.raises(services.ModerationUnavailable, match='read timed out'):
        services.create_post(author_id=1, title='Title', body='<p>Body</p>', strict=True)

    get_db.assert_not_called()
