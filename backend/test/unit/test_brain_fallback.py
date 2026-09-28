import pytest

from brain import FallbackBrain, GeneratedPost, ToxicityResult

CALLS = {
    'suggest_correction': ('text',),
    'propose_comments': ('title', 'body'),
    'check_toxicity': ('text',),
    'write_post': ('personality', 1),
    'write_reply': ('personality', 'context', 1),
    'suggest_post': ('notes', 1),
}


class Answering:
    name = 'answering'

    def __init__(self, label):
        self.label = label
        self.calls = []

    def _answer(self, operation, *args):
        self.calls.append((operation, args))
        return f'{self.label}:{operation}'

    def suggest_correction(self, *args): return self._answer('suggest_correction', *args)
    def propose_comments(self, *args): return self._answer('propose_comments', *args)
    def check_toxicity(self, *args): return self._answer('check_toxicity', *args)
    def write_post(self, *args): return self._answer('write_post', *args)
    def write_reply(self, *args): return self._answer('write_reply', *args)
    def suggest_post(self, *args): return self._answer('suggest_post', *args)


class Failing(Answering):
    name = 'failing'

    def _answer(self, operation, *args):
        self.calls.append((operation, args))
        raise TimeoutError('read timed out')


@pytest.mark.parametrize('operation', CALLS)
def test_primary_answer_is_used_when_it_works(operation):
    # Arrange
    primary, fallback, logged = Answering('primary'), Answering('fallback'), []
    brain = FallbackBrain(primary, fallback, lambda op, error: logged.append(op))

    # Act
    result = getattr(brain, operation)(*CALLS[operation])

    # Assert
    assert result == f'primary:{operation}'
    assert fallback.calls == []
    assert logged == []


@pytest.mark.parametrize('operation', CALLS)
def test_fallback_answers_and_the_failure_is_logged(operation):
    # Arrange
    primary, fallback, logged = Failing('primary'), Answering('fallback'), []
    brain = FallbackBrain(primary, fallback, lambda op, error: logged.append((op, str(error))))

    # Act
    result = getattr(brain, operation)(*CALLS[operation])

    # Assert: same arguments reach the fallback, and the reason is recorded.
    assert result == f'fallback:{operation}'
    assert fallback.calls == [(operation, CALLS[operation])]
    assert logged == [(operation, 'read timed out')]


def test_fallback_brain_names_both_providers():
    # Arrange
    brain = FallbackBrain(Failing('p'), Answering('f'), lambda op, error: None)

    # Act
    result = brain.name

    # Assert
    assert result == 'failing (fallback: answering)'
