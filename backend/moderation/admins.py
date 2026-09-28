"""Grants or revokes admin rights. A command, not a web page, on purpose: only people with access to
the server can create admins, which also answers who makes the first one.

Run from the backend folder (in production: docker compose exec backend python -m moderation.admins ...):
    python -m moderation.admins list
    python -m moderation.admins grant someone@example.com
    python -m moderation.admins revoke someone@example.com
"""
import argparse
import sys

import services


def main(argv=None):
    parser = argparse.ArgumentParser(description='Manage admin (moderator) accounts.')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list', help='show all admins')
    for name in ('grant', 'revoke'):
        commands.add_parser(name, help=f'{name} admin rights').add_argument('email')
    args = parser.parse_args(argv)

    if args.command == 'list':
        admins = services.list_admins()
        for admin in admins:
            print(f"{admin['id']:<6} {admin['name']:<24} {admin['email']}")
        print(f'{len(admins)} admin(s)')
        return 0

    try:
        name = services.set_admin(args.email, args.command == 'grant')
    except (LookupError, ValueError) as error:
        print(f'Not changed: {error}', file=sys.stderr)
        return 1

    print(f"{name} ({args.email}) is {'now' if args.command == 'grant' else 'no longer'} an admin")
    return 0


if __name__ == '__main__':
    sys.exit(main())
