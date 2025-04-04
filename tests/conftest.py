import os
import tempfile

import pytest
from lostify import create_app
from lostify.db import get_db, init_db

from flask import Flask
from flask.testing import FlaskClient

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf8')

@pytest.fixture
def app():
    """
    Create a new app instance for the tests.
    """

    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })

    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)

    yield app

    # Cleanup after tests
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app: Flask):
    """
    A test client for the app.
    """

    return app.test_client()

@pytest.fixture
def runner(app: Flask):
    """
    A test cli runner for the app.
    """
    
    return app.test_cli_runner()

class AuthActions:
    """
    Helper class for authentication actions.
    This class provides methods to log in and log out users.
    """
    def __init__(self, client: FlaskClient):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post(
            '/auth/login',
            json = {'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')

@pytest.fixture
def auth(client):
    return AuthActions(client)