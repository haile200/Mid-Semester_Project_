import pytest

from utils import MAX_NOTES_LABEL_LENGTH, MAX_NOTES_TEXT_LENGTH, MAX_NOTES_TITLE_LENGTH, clean_post_notes


def test_valid_notes_are_returned_trimmed():
    # Arrange
    raw = ('  Bouldering ', ' V4 ', '  My project  ', '  Fell at the top.  ')

    # Act
    result = clean_post_notes(*raw)

    # Assert
    assert result == ('Bouldering', 'V4', 'My project', 'Fell at the top.')


def test_title_and_text_are_optional():
    # Arrange: the author has not started writing yet.

    # Act
    result = clean_post_notes('Lead', '6c+', None, None)

    # Assert
    assert result == ('Lead', '6c+', '', '')


@pytest.mark.parametrize('style, grade', [
    (None, 'V4'),
    ('Bouldering', None),
    ('   ', 'V4'),
    ('Bouldering', ''),
])
def test_style_and_grade_are_required(style, grade):
    # Arrange: nothing

    # Act and Assert
    with pytest.raises(ValueError, match='Style and grade are required'):
        clean_post_notes(style, grade, '', '')


@pytest.mark.parametrize('values', [
    (1, 'V4', '', ''),
    ('Bouldering', ['V4'], '', ''),
    ('Bouldering', 'V4', 7, ''),
    ('Bouldering', 'V4', '', {'text': 'x'}),
])
def test_non_text_values_are_rejected(values):
    # Arrange: nothing

    # Act and Assert
    with pytest.raises(ValueError, match='Invalid input types'):
        clean_post_notes(*values)


@pytest.mark.parametrize('values, message', [
    (('x' * (MAX_NOTES_LABEL_LENGTH + 1), 'V4', '', ''), 'Style and grade must be'),
    (('Bouldering', 'x' * (MAX_NOTES_LABEL_LENGTH + 1), '', ''), 'Style and grade must be'),
    (('Bouldering', 'V4', 'x' * (MAX_NOTES_TITLE_LENGTH + 1), ''), 'Title must be'),
    (('Bouldering', 'V4', '', 'x' * (MAX_NOTES_TEXT_LENGTH + 1)), 'Post suggestions work from up to'),
])
def test_values_over_the_limit_are_rejected(values, message):
    # Arrange: nothing

    # Act and Assert
    with pytest.raises(ValueError, match=message):
        clean_post_notes(*values)


def test_values_at_the_limit_are_accepted():
    # Arrange
    values = ('x' * MAX_NOTES_LABEL_LENGTH, 'y' * MAX_NOTES_LABEL_LENGTH,
              't' * MAX_NOTES_TITLE_LENGTH, 'b' * MAX_NOTES_TEXT_LENGTH)

    # Act
    result = clean_post_notes(*values)

    # Assert
    assert result == values
