import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils import hash_password, verify_password


def test_hash_is_not_plaintext():
    # Arrange
    password = 'secret123'

    # Act
    hashed = hash_password(password)

    # Assert
    assert hashed != password


def test_hash_uses_bcrypt_format():
    # Arrange
    password = 'secret123'

    # Act
    hashed = hash_password(password)

    # Assert
    assert hashed.startswith('$2b$')


def test_verify_returns_true_for_correct_password():
    # Arrange
    password = 'secret123'
    hashed = hash_password(password)

    # Act
    result = verify_password(password, hashed)

    # Assert
    assert result is True


def test_verify_returns_false_for_wrong_password():
    # Arrange
    hashed = hash_password('secret123')

    # Act
    result = verify_password('not-the-password', hashed)

    # Assert
    assert result is False


def test_same_password_produces_different_hashes_that_both_verify():
    # Arrange
    password = 'secret123'

    # Act
    first_hash = hash_password(password)
    second_hash = hash_password(password)

    # Assert - unique salts, yet both hashes verify the original password
    assert first_hash != second_hash
    assert verify_password(password, first_hash) is True
    assert verify_password(password, second_hash) is True


def test_verify_returns_false_for_malformed_hash():
    # Arrange
    malformed_hash = 'not-a-bcrypt-hash'

    # Act
    result = verify_password('secret123', malformed_hash)

    # Assert
    assert result is False


def test_verify_returns_false_for_empty_hash():
    # Arrange
    empty_hash = ''

    # Act
    result = verify_password('secret123', empty_hash)

    # Assert
    assert result is False


def test_unicode_password_round_trip():
    # Arrange
    password = 'סיסמה-חזקה-🔒-123'

    # Act
    hashed = hash_password(password)

    # Assert
    assert verify_password(password, hashed) is True
    assert verify_password('סיסמה-אחרת', hashed) is False
