import pytest

from utils import MAX_CORRECTION_LENGTH, clean_correction_text


def test_valid_text_is_returned_unchanged():
    # Arrange: whitespace is the correction's job, not the validator's.
    text = 'i love  bouldring\nsent it'

    # Act
    result = clean_correction_text(text)

    # Assert
    assert result == text


@pytest.mark.parametrize('text', [None, '', '   \n '])
def test_missing_or_blank_text_is_rejected(text):
    # Arrange: the parameters above

    # Act and Assert
    with pytest.raises(ValueError, match='Text is required'):
        clean_correction_text(text)


@pytest.mark.parametrize('text', [42, ['text'], {'text': 'x'}])
def test_non_text_is_rejected(text):
    # Arrange: the parameters above

    # Act and Assert
    with pytest.raises(ValueError, match='Invalid input types'):
        clean_correction_text(text)


def test_the_maximum_length_is_accepted_and_one_more_is_rejected():
    # Arrange
    at_limit = 'a' * MAX_CORRECTION_LENGTH
    over_limit = 'a' * (MAX_CORRECTION_LENGTH + 1)

    # Act
    result = clean_correction_text(at_limit)

    # Assert
    assert result == at_limit
    with pytest.raises(ValueError, match='5000 characters or fewer'):
        clean_correction_text(over_limit)
