import pytest

import brain as brain_package
from brain import FallbackBrain, OfflineBrain, get_brain, select_mode
from brain.gemini import GeminiBrain
from config import Config


@pytest.fixture
def fake_gemini_client(monkeypatch):
    """Keeps get_brain from building a real network client."""
    monkeypatch.setattr(brain_package, 'build_client', lambda api_key: object())
    brain_package.gemini_brain.cache_clear()
    yield
    brain_package.gemini_brain.cache_clear()


@pytest.mark.parametrize('mode, api_key, expected', [
    ('', '', 'offline'),
    ('', 'a-key', 'gemini'),
    ('offline', 'a-key', 'offline'),
    ('gemini', 'a-key', 'gemini'),
    ('  Gemini ', 'a-key', 'gemini'),
])
def test_select_mode_picks_the_provider(mode, api_key, expected):
    # Arrange: the parameters above

    # Act
    result = select_mode(mode, api_key)

    # Assert
    assert result == expected


@pytest.mark.parametrize('mode, api_key, message', [
    ('gemini', '', 'needs GEMINI_API_KEY'),
    ('banana', 'a-key', 'Unknown BRAIN_MODE'),
])
def test_select_mode_rejects_a_broken_configuration(mode, api_key, message):
    # Arrange: the parameters above

    # Act and Assert
    with pytest.raises(ValueError, match=message):
        select_mode(mode, api_key)


def test_the_test_suite_never_uses_a_real_model(monkeypatch):
    # Arrange: even with a key present, the autouse fixture in test/conftest.py forces offline.
    monkeypatch.setattr(Config, 'GEMINI_API_KEY', 'a-real-looking-key')

    # Act
    result = get_brain()

    # Assert
    assert Config.BRAIN_MODE == 'offline'
    assert isinstance(result, OfflineBrain)


def test_get_brain_wraps_gemini_with_the_offline_fallback(monkeypatch, fake_gemini_client):
    # Arrange
    monkeypatch.setattr(Config, 'BRAIN_MODE', '')
    monkeypatch.setattr(Config, 'GEMINI_API_KEY', 'a-key')

    # Act
    result = get_brain()

    # Assert
    assert isinstance(result, FallbackBrain)
    assert result.name.startswith('gemini:')
    assert result.name.endswith('(fallback: offline)')


def test_get_brain_without_fallback_returns_bare_gemini(monkeypatch, fake_gemini_client):
    # Arrange
    monkeypatch.setattr(Config, 'BRAIN_MODE', 'gemini')
    monkeypatch.setattr(Config, 'GEMINI_API_KEY', 'a-key')

    # Act
    result = get_brain(fallback=False)

    # Assert
    assert isinstance(result, GeminiBrain)


def test_the_bot_worker_gets_gemini_without_the_template_fallback(monkeypatch, fake_gemini_client):
    # Arrange
    from bots.worker import worker_brain
    monkeypatch.setattr(Config, 'BRAIN_MODE', '')
    monkeypatch.setattr(Config, 'GEMINI_API_KEY', 'a-key')

    # Act
    result = worker_brain()

    # Assert: a failing model must make bots skip, not post offline template text.
    assert isinstance(result, GeminiBrain)


def test_get_brain_reuses_one_gemini_client(monkeypatch, fake_gemini_client):
    # Arrange
    monkeypatch.setattr(Config, 'BRAIN_MODE', 'gemini')
    monkeypatch.setattr(Config, 'GEMINI_API_KEY', 'a-key')

    # Act
    first, second = get_brain(fallback=False), get_brain(fallback=False)

    # Assert: building a client per request would open a new connection every time.
    assert first is second
