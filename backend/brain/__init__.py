from .base import Brain, GeneratedPost, ToxicityResult
from .offline import OfflineBrain

__all__ = ['Brain', 'GeneratedPost', 'ToxicityResult', 'OfflineBrain', 'get_brain']


def get_brain() -> Brain:
    return OfflineBrain()
