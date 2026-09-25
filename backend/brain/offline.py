"""A provider with no network and no API key: templates and a word list.

It keeps the test suite independent of any external service, and it is the
runtime fallback when the real provider cannot be reached.
"""
import re
import zlib
from typing import List

from .base import Brain, GeneratedPost, ToxicityResult

BLOCKED_TERMS = (
    'idiot', 'moron', 'loser', 'pathetic', 'shut up', 'kill yourself', 'kys', 'hate you',
    'fuck', 'fucking', 'shit', 'bitch', 'asshole', 'bastard',
)

MISSPELLINGS = {
    'i': 'I',
    'bouldring': 'bouldering',
    'carabeener': 'carabiner',
    'carribiner': 'carabiner',
    'rapell': 'rappel',
    'harnes': 'harness',
    'definately': 'definitely',
    'recieve': 'receive',
    'untill': 'until',
    'wich': 'which',
    'thier': 'their',
    'truely': 'truly',
    'alot': 'a lot',
}

VOICE_KEYWORDS = (
    ('trad', ('trad', 'gear', 'crack', 'cam', 'multi-pitch', 'alpine')),
    ('gym', ('gym', 'setter', 'comp', 'plastic', 'indoor', 'board')),
)

VOICES = {
    'trad': {
        'titles': [
            'Hand jams and happy feet',
            'Rack sorted for the weekend',
            'Old-school grades never lie',
            'Long multi-pitch day on the granite',
            'Nothing beats a splitter crack',
            'Bomber gear, bold moves',
        ],
        'bodies': [
            'Ran it out a bit on the second pitch, but every placement was solid. Nothing like the quiet up there.',
            'Taped up, racked up, and spent the whole morning in the crack. My hands hurt and I would do it again tomorrow.',
            'Spent the evening re-slinging old nuts. Take care of your gear and it takes care of you.',
            'Climbed a classic that was graded before half of you were born. Still stiff. Still worth it.',
            'Walked in at dawn, topped out at sunset. The approach was half the adventure.',
            'Reminder: double-check your placements and your partner. The rock does not care about your grade.',
        ],
        'replies': [
            'Solid effort. Did you place gear at the crux or just commit?',
            'That is the spirit. Good gear and a calm head get you up most things.',
            'Back in my day we did that in stiff boots, but I will allow it. Nice work.',
            'Great beta. I would add a cam around the midpoint, it protects the awkward move.',
            'Love to see it. Get out on real rock soon, the plastic will still be there.',
            'Proper climbing. Keep your feet quiet and the rest follows.',
        ],
    },
    'gym': {
        'titles': [
            'New set just dropped',
            'Finally flashed the purple V5',
            'Board session done',
            'Comp prep week',
            'That volume problem is evil',
            'Crimp training update',
        ],
        'bodies': [
            'Setters went wild this week. Three new problems on the overhang and I have already fallen off all of them.',
            'Flashed it on my first go and I still cannot believe it. Heel hook at the top made all the difference.',
            'Forty minutes on the board, fingers are cooked. Tomorrow is a rest day, no matter what.',
            'Working on dynos all week before the comp. Coordination is finally clicking.',
            'Spent an hour on one slab problem. Trust your feet, they said. My feet said no.',
            'Hangboard numbers are up this month. Small gains, but they add up.',
        ],
        'replies': [
            'Nice! Was it the heel hook or the toe hook at the top?',
            'Go again after a rest, you are so close on this one.',
            'The new set is brutal. I fell off the start like five times.',
            'Try matching on the volume first, it saves a lot of energy.',
            'Congrats on the send, that one has been shutting people down all week.',
            'Solid. Stretch those forearms tonight, you earned it.',
        ],
    },
    'general': {
        'titles': [
            'Good day at the crag',
            'Working my project',
            'Rest day thoughts',
            'Skin is shredded',
            'Morning session',
            'Small progress is still progress',
        ],
        'bodies': [
            'Nothing fancy today, just mileage and good company. Went home tired and happy.',
            'Got one move further on my project than last week. It is going to go soon.',
            'Taking a rest day and already thinking about the next session.',
            'Tried something above my grade and learned a lot from falling off it.',
            'Early start, empty walls, fresh skin. Best way to begin a day.',
            'Climbed with a new partner today. Great belays and even better stories.',
        ],
        'replies': [
            'Love this. Where do you usually climb?',
            'Keep at it, that next move will click.',
            'Rest days count as training too.',
            'Nice one! How long have you been working it?',
            'Same here, skin is the real limit some weeks.',
            'Great to see steady progress. Keep showing up.',
        ],
    },
}

COMMENT_IDEAS = {
    'celebrate': [
        'Nice send! What was the crux like?',
        'Congrats, that one looks like a proper battle.',
        'Huge. How many sessions did it take?',
        'Well deserved. Any beta for the top?',
    ],
    'encourage': [
        'You are so close, keep at it.',
        'Which move is stopping you right now?',
        'Rest up and go again, it will go.',
        'Try breaking it into sections and linking them.',
    ],
    'general': [
        'Great post, thanks for sharing.',
        'Where was this?',
        'Love the energy here.',
        'How are you feeling after the session?',
    ],
}

CELEBRATE_WORDS = ('sent', 'send', 'flash', 'flashed', 'finally', 'topped')
ENCOURAGE_WORDS = ('project', 'fell', 'falling', 'working', 'close', 'almost')


def stable_index(text, size):
    # crc32 instead of hash(): Python randomizes str hashes per process, which would change the choice on every run.
    return zlib.crc32(text.encode('utf-8')) % size


def _words(text):
    return re.findall(r'[a-z0-9]+', text.lower())


def pick_voice(personality):
    text = personality.lower()
    for voice, keywords in VOICE_KEYWORDS:
        if any(re.search(rf'\b{re.escape(word)}s?\b', text) for word in keywords):
            return voice
    return 'general'


def _fix_word(match):
    word = match.group(0)
    replacement = MISSPELLINGS.get(word.lower())
    if replacement is None:
        return word
    if word[0].isupper():
        replacement = replacement[0].upper() + replacement[1:]
    return replacement


class OfflineBrain(Brain):

    def suggest_correction(self, text):
        text = re.sub(r'[ \t]+', ' ', text).strip()
        text = re.sub(r'[A-Za-z]+', _fix_word, text)
        return re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)

    def propose_comments(self, post_title, post_body):
        plain = re.sub(r'<[^>]+>', ' ', post_body)
        words = set(_words(f'{post_title} {plain}'))
        if words & set(CELEBRATE_WORDS):
            ideas = COMMENT_IDEAS['celebrate']
        elif words & set(ENCOURAGE_WORDS):
            ideas = COMMENT_IDEAS['encourage']
        else:
            ideas = COMMENT_IDEAS['general']
        start = stable_index(f'{post_title}|{plain}', len(ideas))
        return [ideas[(start + offset) % len(ideas)] for offset in range(3)]

    def check_toxicity(self, text):
        # Matching whole words on padded text keeps "moron" from matching inside "oxymoron".
        padded = f" {' '.join(_words(text))} "
        if any(f' {term} ' in padded for term in BLOCKED_TERMS):
            return ToxicityResult(allowed=False, reason='Contains blocked language')
        return ToxicityResult(allowed=True)

    def write_post(self, personality, seed):
        voice = VOICES[pick_voice(personality)]
        title = voice['titles'][stable_index(f'{personality}|{seed}|title', len(voice['titles']))]
        body = voice['bodies'][stable_index(f'{personality}|{seed}|body', len(voice['bodies']))]
        return GeneratedPost(title=title, body=body)

    def write_reply(self, personality, context, seed):
        replies = VOICES[pick_voice(personality)]['replies']
        return replies[stable_index(f'{personality}|{context}|{seed}', len(replies))]
