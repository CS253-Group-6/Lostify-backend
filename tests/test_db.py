import sqlite3

import pytest
from lostify.db import get_db

def test_get_close_db(app):
    """
    Ensure that the database connection is cached and that the cached
    connection is returned on subsequent calls to `get_db()`.
    """
    with app.app_context():
        db = get_db()
        assert db is get_db()

    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute('SELECT 1')

    assert 'closed' in str(e.value)

def test_init_db_command(runner, monkeypatch):
    """
    Test the `init-db` command.
    """

    class Recorder(object):
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr('lostify.db.init_db', fake_init_db)
    result = runner.invoke(args = ('init-db',))
    assert 'Initial' in result.output
    assert Recorder.called