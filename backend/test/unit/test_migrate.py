from unittest.mock import MagicMock

import pytest

import migrate
from migrate import (
    apply_migration,
    list_migration_files,
    order_migration_names,
    pending_migrations,
    run_migrations,
    split_statements,
)


def _write_files(directory, names):
    for name in names:
        (directory / name).write_text('SELECT 1;')


# ---- order_migration_names ----

def test_order_migration_names_sorts_by_number():
    # Arrange: the input order is controlled here, not by the filesystem,
    # so the test fails on every OS if sorting is missing.
    names = ['010_third.sql', '001_first.sql', '009_second.sql']

    # Act
    result = order_migration_names(names)

    # Assert
    assert result == ['001_first.sql', '009_second.sql', '010_third.sql']


def test_order_migration_names_ignores_names_that_are_not_migrations():
    # Arrange: one real migration surrounded by near misses.
    names = ['README.md', '002_notes.txt', '001_first.sql', '3_short.sql', '001_first.sql.bak']

    # Act
    result = order_migration_names(names)

    # Assert
    assert result == ['001_first.sql']


def test_order_migration_names_rejects_duplicate_numbers():
    # Arrange: two files claim the same position in the order.
    names = ['001_first.sql', '002_a.sql', '002_b.sql']

    # Act and Assert
    with pytest.raises(ValueError):
        order_migration_names(names)


# ---- list_migration_files ----

def test_list_migration_files_reads_files_and_skips_folders(tmp_path):
    # Arrange: a folder whose name looks like a migration must not be treated as one.
    _write_files(tmp_path, ['002_second.sql', '001_first.sql'])
    (tmp_path / '003_folder.sql').mkdir()

    # Act
    result = list_migration_files(tmp_path)

    # Assert
    assert result == ['001_first.sql', '002_second.sql']


# ---- pending_migrations ----

def test_pending_migrations_returns_unapplied_files_in_order():
    # Arrange
    all_files = ['001_a.sql', '002_b.sql', '003_c.sql']
    applied = {'002_b.sql'}

    # Act
    result = pending_migrations(all_files, applied)

    # Assert
    assert result == ['001_a.sql', '003_c.sql']


def test_pending_migrations_is_empty_when_everything_is_applied():
    # Arrange
    all_files = ['001_a.sql', '002_b.sql']
    applied = {'001_a.sql', '002_b.sql'}

    # Act
    result = pending_migrations(all_files, applied)

    # Assert
    assert result == []


# ---- split_statements ----

def test_split_statements_returns_trimmed_statements_in_order():
    # Arrange
    sql = '  CREATE TABLE a (id INT);\n\n  CREATE TABLE b (id INT);  '

    # Act
    result = split_statements(sql)

    # Assert
    assert result == ['CREATE TABLE a (id INT)', 'CREATE TABLE b (id INT)']


def test_split_statements_drops_empty_and_comment_only_chunks():
    # Arrange: a trailing semicolon, blank lines and a final comment would
    # otherwise become statements that the database rejects as empty.
    sql = 'CREATE TABLE a (id INT);\n\n;\n-- end of file\n'

    # Act
    result = split_statements(sql)

    # Assert
    assert result == ['CREATE TABLE a (id INT)']


def test_split_statements_keeps_comments_inside_a_statement():
    # Arrange
    sql = '-- explains the change\nALTER TABLE a ADD COLUMN b INT;'

    # Act
    result = split_statements(sql)

    # Assert
    assert result == ['-- explains the change\nALTER TABLE a ADD COLUMN b INT']


# ---- apply_migration ----

def test_apply_migration_runs_statements_then_records_then_commits():
    # Arrange
    conn = MagicMock()
    cursor = conn.cursor.return_value

    # Act
    apply_migration(conn, '001_a.sql', 'CREATE TABLE a (id INT); CREATE TABLE b (id INT);')

    # Assert: the statements run first and in order, the record comes last.
    executed = cursor.execute.call_args_list
    assert executed[0].args == ('CREATE TABLE a (id INT)',)
    assert executed[1].args == ('CREATE TABLE b (id INT)',)
    record_sql, record_params = executed[2].args
    assert 'schema_migrations' in record_sql
    assert record_params == ('001_a.sql',)
    assert len(executed) == 3
    conn.commit.assert_called_once()


def test_apply_migration_does_not_record_or_commit_when_a_statement_fails():
    # Arrange: the second statement fails.
    conn = MagicMock()
    cursor = conn.cursor.return_value
    cursor.execute.side_effect = [None, RuntimeError('syntax error')]

    # Act and Assert: the error reaches the caller.
    with pytest.raises(RuntimeError):
        apply_migration(conn, '001_a.sql', 'CREATE TABLE a (id INT); BROKEN SQL;')

    # Assert: the migration was never marked as applied.
    recorded = [c for c in cursor.execute.call_args_list if 'schema_migrations' in c.args[0]]
    assert recorded == []
    conn.commit.assert_not_called()
    conn.rollback.assert_called_once()


# ---- run_migrations ----

@pytest.fixture
def empty_tracking_table(monkeypatch):
    """Replaces the two functions that talk to the real schema_migrations
    table, so run_migrations can be tested without a database."""
    ensure = MagicMock()
    monkeypatch.setattr(migrate, 'ensure_tracking_table', ensure)
    monkeypatch.setattr(migrate, 'fetch_applied', lambda conn: set())
    return ensure


def test_run_migrations_stops_at_the_first_failure(tmp_path, empty_tracking_table):
    # Arrange: two pending migrations, and the first one fails.
    (tmp_path / '001_bad.sql').write_text('BROKEN SQL;')
    (tmp_path / '002_good.sql').write_text('CREATE TABLE good (id INT);')
    conn = MagicMock()
    conn.cursor.return_value.execute.side_effect = RuntimeError('syntax error')

    # Act and Assert
    with pytest.raises(RuntimeError):
        run_migrations(conn, tmp_path)

    # Assert: the second migration was never attempted.
    executed = [c.args[0] for c in conn.cursor.return_value.execute.call_args_list]
    assert 'CREATE TABLE good (id INT)' not in executed


def test_run_migrations_dry_run_changes_nothing(tmp_path, empty_tracking_table):
    # Arrange
    _write_files(tmp_path, ['001_a.sql', '002_b.sql'])
    conn = MagicMock()

    # Act
    result = run_migrations(conn, tmp_path, dry_run=True, log=lambda message: None)

    # Assert: it reports what would run, but executes and creates nothing.
    assert result == ['001_a.sql', '002_b.sql']
    conn.cursor.return_value.execute.assert_not_called()
    conn.commit.assert_not_called()
    empty_tracking_table.assert_not_called()
