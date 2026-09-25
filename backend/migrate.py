"""Applies the numbered SQL files in migrations/ that this database has not run yet.

Usage:
    python migrate.py            apply pending migrations
    python migrate.py --dry-run  list pending migrations without changing anything

Rules for migration files:
    - Never edit a migration after it has run on any database; add a new one.
    - Statements are split on ';', so no semicolons inside comments or strings.
"""
import argparse
import re
import sys
from contextlib import closing
from pathlib import Path

from db import get_db

MIGRATIONS_DIR = Path(__file__).parent / 'migrations'
MIGRATION_NAME = re.compile(r'^(\d{3})_\w+\.sql$')


def order_migration_names(names):
    """Keeps only migration names and sorts them by number. Raises ValueError on a duplicate number."""
    by_number = {}
    for name in names:
        match = MIGRATION_NAME.match(name)
        if not match:
            continue
        number = int(match.group(1))
        if number in by_number:
            raise ValueError(f'Duplicate migration number {number:03d}: {by_number[number]} and {name}')
        by_number[number] = name
    return [by_number[number] for number in sorted(by_number)]


def list_migration_files(directory):
    return order_migration_names(path.name for path in Path(directory).iterdir() if path.is_file())


def pending_migrations(all_files, applied):
    return [name for name in all_files if name not in applied]


def split_statements(sql):
    statements = []
    for chunk in sql.split(';'):
        chunk = chunk.strip()
        has_code = any(line.strip() and not line.strip().startswith('--') for line in chunk.splitlines())
        if has_code:
            statements.append(chunk)
    return statements


def apply_migration(conn, name, sql):
    with closing(conn.cursor()) as cursor:
        try:
            for statement in split_statements(sql):
                cursor.execute(statement)
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (name,))
            conn.commit()
        except Exception:
            # MySQL commits schema changes (ALTER, CREATE) immediately, so this
            # only undoes data changes. That is why each migration is one atomic change.
            conn.rollback()
            raise


def ensure_tracking_table(conn):
    with closing(conn.cursor()) as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def fetch_applied(conn):
    """Returns the names of applied migrations; an empty set if the tracking table does not exist yet."""
    with closing(conn.cursor()) as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = 'schema_migrations'
        """)
        if cursor.fetchone()[0] == 0:
            return set()
        cursor.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cursor.fetchall()}


def run_migrations(conn, directory=MIGRATIONS_DIR, dry_run=False, log=print):
    """Applies pending migrations in order and stops at the first failure. Returns the pending names."""
    files = list_migration_files(directory)
    if not dry_run:
        ensure_tracking_table(conn)
    todo = pending_migrations(files, fetch_applied(conn))

    if not todo:
        log('Database is up to date.')
    for name in todo:
        if dry_run:
            log(f'Would apply {name}')
            continue
        apply_migration(conn, name, (Path(directory) / name).read_text(encoding='utf-8'))
        log(f'Applied {name}')
    return todo


def main():
    parser = argparse.ArgumentParser(description='Apply pending database migrations.')
    parser.add_argument('--dry-run', action='store_true', help='list pending migrations without applying them')
    args = parser.parse_args()

    with closing(get_db()) as conn:
        try:
            run_migrations(conn, dry_run=args.dry_run)
        except Exception as error:
            print(f'Migration failed: {error}', file=sys.stderr)
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
