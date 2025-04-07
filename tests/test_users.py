from flask import Flask
from flask.testing import FlaskClient
from lostify.db import get_db

def test_fetch_profile(client: FlaskClient):
    # Authenticate
    cookie = client.post(
        "/auth/login",
        json = {
            "username": "test",
            "password": "test"
        }
    ).headers["Set-Cookie"]

    # Test fetching a user profile with authentication
    response = client.get(
        "/users/1/profile",
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 200
    assert response.json["userid"] == 1

def test_fetch_profile_validate_input(client: FlaskClient):
    # Test fetching a user profile without authentication
    response = client.get("/users/1/profile")

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        "/auth/login",
        json = {
            "username": "test",
            "password": "test"
        }
    ).headers["Set-Cookie"]

    # Test fetching a non-existent user profile
    response = client.get(
        "/users/100/profile",
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 404

def test_update_profile(client: FlaskClient, app: Flask):
    # Authenticate
    cookie = client.post(
        "/auth/login",
        json = {
            "username": "test",
            "password": "test"
        }
    ).headers["Set-Cookie"]

    # Test updating own user profile
    response = client.put(
        "/users/0/profile",
        json = {
            "name": "Updated Name"
        },
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 204
    with app.app_context():
        assert get_db().execute(
            "SELECT name FROM profiles WHERE userid = 0"
        ).fetchone()[0] == "Updated Name"

def test_update_profile_validate_input(client: FlaskClient, app: Flask):
    # Test updating a user profile without authentication
    response = client.put(
        "/users/1/profile",
        json = {
            "name": "Updated Name"
        }
    )

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        "/auth/login",
        json = {
            "username": "test",
            "password": "test"
        }
    ).headers["Set-Cookie"]

    # Test updating someone else's user profile
    response = client.put(
        "/users/1/profile",
        json = {
            "name": "Updated Name 2"
        },
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 403

    # Empty update request
    response = client.put(
        "/users/0/profile",
        json = {},
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 400

    # Test updating own user profile with invalid data
    response = client.put(
        "/users/0/profile",
        json = {
            "name": None
        },
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 400

    # Test emptying required fields
    response = client.put(
        "/users/0/profile",
        json = {
            "name": ""
        },
        headers = {
            "Cookie": cookie
        }
    )
    
    assert response.status_code == 400

def test_get_online_status(client: FlaskClient, app: Flask):
    # Test fetching online status without authentication
    response = client.get("/users/0/online")

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        "/auth/login",
        json = {
            "username": "test",
            "password": "test"
        }
    ).headers["Set-Cookie"]

    # Test fetching own online status
    response = client.get(
        "/users/0/online",
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 200
    with app.app_context():
        assert response.json["online"] == bool(get_db().execute(
            "SELECT online FROM profiles WHERE userid = 0"
        ).fetchone()[0])

    # Test fetching someone else's online status
    response = client.get(
        "/users/1/online",
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 200
    with app.app_context():
        assert response.json["online"] == bool(get_db().execute(
            "SELECT online FROM profiles WHERE userid = 1"
        ).fetchone()[0])

def test_update_online_status(client: FlaskClient, app: Flask):
    # Test updating an online status without authentication
    response = client.put(
        "/users/0/online",
        json = {
            "status": True
        }
    )

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        "/auth/login",
        json = {
            "username": "test",
            "password": "test"
        }
    ).headers["Set-Cookie"]

    # Test updating someone else's online status
    response = client.put(
        "/users/1/online",
        json = {
            "status": True
        },
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 403

    # Empty update request
    response = client.put(
        "/users/0/online",
        json = {},
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 400

    # Test updating own online status with invalid data
    response = client.put(
        "/users/0/online",
        json = {
            "status": 0
        },
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 400

    # Test updating own online status to true
    response = client.put(
        "/users/0/online",
        json = {
            "status": True
        },
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 204

    with app.app_context():
        assert get_db().execute(
            "SELECT online FROM profiles WHERE userid = 0"
        ).fetchone()[0] == 1

    # Test updating own online status to false
    response = client.put(
        "/users/0/online",
        json = {
            "status": False
        },
        headers = {
            "Cookie": cookie
        }
    )

    assert response.status_code == 204

    with app.app_context():
        assert get_db().execute(
            "SELECT online FROM profiles WHERE userid = 0"
        ).fetchone()[0] == 0