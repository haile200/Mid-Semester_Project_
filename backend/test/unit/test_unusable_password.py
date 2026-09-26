from utils import unusable_password_hash, verify_password


def test_unusable_password_hash_is_a_bcrypt_hash():
    # Arrange: nothing

    # Act
    result = unusable_password_hash()

    # Assert: the same format as a human password hash, so the column stays uniform.
    assert result.startswith('$2b$')


def test_unusable_password_hash_is_different_every_time():
    # Arrange: nothing

    # Act
    first, second = unusable_password_hash(), unusable_password_hash()

    # Assert
    assert first != second


def test_no_guess_matches_an_unusable_password_hash():
    # Arrange
    stored = unusable_password_hash()

    # Act
    matches = [guess for guess in ('', 'password', 'Password123!', stored) if verify_password(guess, stored)]

    # Assert
    assert matches == []
