import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils import fetchall_dict, fetchone_dict
from mock_db import DummyCursor


def test_fetchall_dict():
    cursor = DummyCursor(
        description=(('id',), ('name',)),
        rows=[(1, 'Alice'), (2, 'Bob')]
    )
    result = fetchall_dict(cursor)

    assert result == [
        {'id': 1, 'name': 'Alice'},
        {'id': 2, 'name': 'Bob'}
    ]


def test_fetchone_dict():
    cursor = DummyCursor(
        description=(('id',), ('name',)),
        rows=[(1, 'Alice')]
    )
    result = fetchone_dict(cursor)

    assert result == {'id': 1, 'name': 'Alice'}
