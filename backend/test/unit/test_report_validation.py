import pytest

from utils import MAX_REPORT_NOTE_LENGTH, REPORT_REASONS, clean_report


@pytest.mark.parametrize('reason', REPORT_REASONS)
def test_every_listed_reason_is_accepted(reason):
    # Arrange: the parameters above

    # Act
    result = clean_report(reason, None)

    # Assert
    assert result == (reason, None)


@pytest.mark.parametrize('reason', ['boring', '', None, 'SPAM', ['spam']])
def test_anything_else_is_rejected_as_a_reason(reason):
    # Arrange: exact match only, so the dashboard can rely on four known values.

    # Act and Assert
    with pytest.raises(ValueError, match='Choose a reason'):
        clean_report(reason, None)


def test_the_note_is_trimmed_and_a_blank_note_becomes_none():
    # Arrange: nothing

    # Act
    trimmed = clean_report('other', '  keeps posting the same link  ')
    blank = clean_report('other', '   ')

    # Assert
    assert trimmed == ('other', 'keeps posting the same link')
    assert blank == ('other', None)


def test_the_note_has_a_length_limit():
    # Arrange
    at_limit = 'a' * MAX_REPORT_NOTE_LENGTH

    # Act
    result = clean_report('spam', at_limit)

    # Assert
    assert result == ('spam', at_limit)
    with pytest.raises(ValueError, match='300 characters or fewer'):
        clean_report('spam', at_limit + 'a')


def test_a_note_must_be_text():
    # Arrange: nothing

    # Act and Assert
    with pytest.raises(ValueError, match='Invalid input types'):
        clean_report('spam', 42)
