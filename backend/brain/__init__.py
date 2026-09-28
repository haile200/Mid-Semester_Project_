import logging
from functools import lru_cache

from config import Config

from .base import Brain, GeneratedPost, ToxicityResult
from .fallback import FallbackBrain
from .gemini import GeminiBrain, build_client
from .offline import OfflineBrain

__all__ = [
    'Brain', 'GeneratedPost', 'ToxicityResult', 'OfflineBrain', 'GeminiBrain', 'FallbackBrain',
    'select_mode', 'get_brain',
]

MODES = ('offline', 'gemini')


def select_mode(brain_mode, api_key):
    """Returns 'offline' or 'gemini'. Raises ValueError for a configuration that cannot work."""
    mode = (brain_mode or '').strip().lower()
    if mode and mode not in MODES:
        raise ValueError(f'Unknown BRAIN_MODE {brain_mode!r}; use "offline" or "gemini"')
    if mode == 'gemini' and not api_key:
        raise ValueError('BRAIN_MODE=gemini needs GEMINI_API_KEY')
    if mode:
        return mode
    return 'gemini' if api_key else 'offline'


@lru_cache(maxsize=1)
def gemini_brain(api_key, model):
    # One client per process, so connections are reused between requests.
    return GeminiBrain(build_client(api_key), model)


def _log_fallback(operation, error):
    logging.getLogger('brain').warning(
        'Gemini %s failed (%s: %s); answered by the offline brain', operation, type(error).__name__, error
    )


def get_brain(fallback=True):
    """The configured brain. With fallback, a failing Gemini call is answered by the offline brain."""
    if select_mode(Config.BRAIN_MODE, Config.GEMINI_API_KEY) == 'offline':
        return OfflineBrain()
    gemini = gemini_brain(Config.GEMINI_API_KEY, Config.GEMINI_MODEL)
    return FallbackBrain(gemini, OfflineBrain(), _log_fallback) if fallback else gemini
