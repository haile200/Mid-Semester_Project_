"""The Gemini provider. Every answer is parsed and validated; anything unexpected raises BrainError.

The google-genai SDK is imported inside functions, so the offline brain and the tests work without it.
"""
import json
import re

from . import prompts
from .base import Brain, GeneratedPost, ToxicityResult

# The Gemini API rejects deadlines under 10 seconds; this still fails well before gunicorn's 30s limit.
TIMEOUT_MS = 10000
MAX_TITLE = 100
MAX_POST_BODY = 1000
MAX_REPLY = 500
MAX_IDEA = 300
MAX_REASON = 200


class BrainError(Exception):
    """The model answered, but not in the expected shape."""


def build_client(api_key):
    from google import genai
    from google.genai import types
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=TIMEOUT_MS))


def _plain(markup):
    return ' '.join(re.sub(r'<[^>]+>', ' ', markup).split())


def _text(data, key, max_length):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BrainError(f'Model answer is missing "{key}"')
    value = value.strip()
    if len(value) > max_length:
        raise BrainError(f'Model answer "{key}" is longer than {max_length} characters')
    return value


class GeminiBrain(Brain):

    def __init__(self, client, model):
        self._client = client
        self.model = model
        self.name = f'gemini:{model}'

    def _ask(self, system, contents, temperature, seed=None, max_tokens=512):
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            seed=seed,
            max_output_tokens=max_tokens,
            response_mime_type='application/json',
            # Short tasks do not need the model's slower step-by-step reasoning.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        response = self._client.models.generate_content(model=self.model, contents=contents, config=config)
        # response.text is None when Gemini's own safety filter blocks the answer.
        try:
            data = json.loads(response.text or '')
        except ValueError as error:
            raise BrainError('Model answer is not valid JSON') from error
        if not isinstance(data, dict):
            raise BrainError('Model answer is not a JSON object')
        return data

    def check_toxicity(self, text):
        data = self._ask(prompts.MODERATION, prompts.wrap('text', text), temperature=0)
        allowed = data.get('allowed')
        if not isinstance(allowed, bool):
            raise BrainError('Model answer is missing "allowed"')
        if allowed:
            return ToxicityResult(allowed=True)
        reason = data.get('reason')
        if not isinstance(reason, str) or not reason.strip():
            reason = 'Rejected by moderation'
        return ToxicityResult(allowed=False, reason=reason.strip()[:MAX_REASON])

    def suggest_correction(self, text):
        if not text.strip():
            return text
        data = self._ask(prompts.CORRECTION, prompts.wrap('text', text), temperature=0.2, max_tokens=2048)
        return _text(data, 'text', max_length=max(2 * len(text), 200))

    def propose_comments(self, post_title, post_body):
        contents = prompts.wrap('post', f'{post_title}\n{_plain(post_body)}')
        data = self._ask(prompts.COMMENT_IDEAS, contents, temperature=0.7)
        ideas = data.get('comments')
        if not isinstance(ideas, list) or len(ideas) < 3:
            raise BrainError('Model answer needs three comments')
        cleaned = []
        for idea in ideas[:3]:
            if not isinstance(idea, str) or not idea.strip() or len(idea.strip()) > MAX_IDEA:
                raise BrainError('Model answer has an invalid comment')
            cleaned.append(idea.strip())
        return cleaned

    def write_post(self, personality, seed):
        data = self._ask(prompts.bot_post(personality), prompts.WRITE_POST_REQUEST, temperature=0.9, seed=seed)
        return GeneratedPost(title=_text(data, 'title', MAX_TITLE), body=_text(data, 'body', MAX_POST_BODY))

    def write_reply(self, personality, context, seed):
        data = self._ask(prompts.bot_reply(personality), prompts.wrap('context', context), temperature=0.9, seed=seed)
        return _text(data, 'reply', MAX_REPLY)
