import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils import session_cookie_flags


def test_insecure_flags_for_local_development():
    # Arrange
    secure = False

    # Act
    flags = session_cookie_flags(secure)

    # Assert
    assert flags == {'httponly': True, 'samesite': 'Lax', 'secure': False}


def test_secure_flags_for_production():
    # Arrange
    secure = True

    # Act
    flags = session_cookie_flags(secure)

    # Assert
    assert flags == {'httponly': True, 'samesite': 'None', 'secure': True}
