from .base import Brain


def _name(brain):
    return getattr(brain, 'name', type(brain).__name__)


class FallbackBrain(Brain):
    """Answers from the primary provider, or from the fallback when the primary raises."""

    def __init__(self, primary, fallback, on_fallback):
        self._primary = primary
        self._fallback = fallback
        self._on_fallback = on_fallback
        self.name = f'{_name(primary)} (fallback: {_name(fallback)})'

    def _call(self, operation, *args):
        try:
            return getattr(self._primary, operation)(*args)
        except Exception as error:
            self._on_fallback(operation, error)
            return getattr(self._fallback, operation)(*args)

    def suggest_correction(self, text):
        return self._call('suggest_correction', text)

    def propose_comments(self, post_title, post_body):
        return self._call('propose_comments', post_title, post_body)

    def check_toxicity(self, text):
        return self._call('check_toxicity', text)

    def write_post(self, personality, seed):
        return self._call('write_post', personality, seed)

    def write_reply(self, personality, context, seed):
        return self._call('write_reply', personality, context, seed)

    def suggest_post(self, notes, seed):
        return self._call('suggest_post', notes, seed)
