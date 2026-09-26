"""Creates or updates the bot accounts listed in bots/profiles.py.

Run from the backend folder:
    python -m bots.seed

Safe to run again: existing bots are updated, never duplicated.
"""
import sys

import services
from bots.profiles import BOTS
from brain.offline import pick_voice


def seed_bots(profiles=BOTS):
    """Returns (profile, user_id, created) for each bot."""
    results = []
    for bot in profiles:
        user_id, created = services.upsert_bot(bot.name, bot.email, bot.bio, bot.personality)
        results.append((bot, user_id, created))
    return results


def main():
    try:
        results = seed_bots()
    except ValueError as error:
        print(f'Seeding stopped: {error}', file=sys.stderr)
        return 1

    for bot, user_id, created in results:
        action = 'created' if created else 'updated'
        print(f'{action:8} id={user_id:<5} voice={pick_voice(bot.personality):8} {bot.name}')

    created_count = sum(1 for _, _, created in results if created)
    print(f'\n{len(results)} bots: {created_count} created, {len(results) - created_count} updated')
    return 0


if __name__ == '__main__':
    sys.exit(main())
