import pytest

from utils import MAX_COMMENT_LENGTH, clean_comment_body


def test_clean_comment_body_trims_surrounding_whitespace():
    # Arrange
    body = '   Great heel hook on the crux   '

    # Act
    result = clean_comment_body(body)

    # Assert
    assert result == 'Great heel hook on the crux'


@pytest.mark.parametrize('body', ['', '   ', '\n\t', None])
def test_clean_comment_body_rejects_empty_text(body):
    # Arrange: the parameters above

    # Act and Assert
    with pytest.raises(ValueError, match='Comment cannot be empty'):
        clean_comment_body(body)


def test_clean_comment_body_accepts_the_maximum_length():
    # Arrange
    body = 'a' * MAX_COMMENT_LENGTH

    # Act
    result = clean_comment_body(body)

    # Assert
    assert len(result) == MAX_COMMENT_LENGTH


def test_clean_comment_body_rejects_one_character_over_the_maximum():
    # Arrange
    body = 'a' * (MAX_COMMENT_LENGTH + 1)

    # Act and Assert
    with pytest.raises(ValueError, match='1000 characters or fewer'):
        clean_comment_body(body)


def test_clean_comment_body_measures_length_after_trimming():
    # Arrange: surrounding whitespace must not count against the limit.
    body = '  ' + 'a' * MAX_COMMENT_LENGTH + '  '

    # Act
    result = clean_comment_body(body)

    # Assert
    assert len(result) == MAX_COMMENT_LENGTH


@pytest.mark.parametrize('body', [42, ['text'], {'text': 'x'}])
def test_clean_comment_body_rejects_non_text(body):
    # Arrange: the parameters above

    # Act and Assert
    with pytest.raises(ValueError, match='Invalid input types'):
        clean_comment_body(body)
