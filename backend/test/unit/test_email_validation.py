import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils import is_valid_email


def test_valid_email_is_accepted():
    # Arrange
    email = 'alice@example.com'

    # Act
    result = is_valid_email(email)

    # Assert
    assert result is True


def test_email_without_at_sign_is_rejected():
    # Arrange
    email = 'alice.example.com'

    # Act
    result = is_valid_email(email)

    # Assert
    assert result is False


def test_email_without_domain_dot_is_rejected():
    # Arrange
    email = 'alice@example'

    # Act
    result = is_valid_email(email)

    # Assert
    assert result is False


def test_email_with_spaces_is_rejected():
    # Arrange
    email = 'alice smith@example.com'

    # Act
    result = is_valid_email(email)

    # Assert
    assert result is False


def test_empty_email_is_rejected():
    # Arrange
    email = ''

    # Act
    result = is_valid_email(email)

    # Assert
    assert result is False


def test_overlong_email_is_rejected():
    # Arrange
    email = 'a' * 250 + '@example.com'

    # Act
    result = is_valid_email(email)

    # Assert
    assert result is False
