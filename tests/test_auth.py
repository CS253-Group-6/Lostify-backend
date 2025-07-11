import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.security import check_password_hash
from lostify.db import get_db
from lostify.auth import LOGIN_COUNTER_RESET_DELAY
from time import sleep

def test_signup_get_otp(client: FlaskClient, app: Flask):
    # NOTE: This test may be commented out because it sends an actual email.
    #       This may consume email resources.
    # pass

    response = client.post(
        '/auth/signup/get_otp',
        json = {
            'username': 'uname',
            'password': 'pass',
            'profile': {
                'name': 'First M. Last',
                'email': 'uname25@example.com',
                'phone': '+91 12345 67890',
                'address': '123 Main St., City, Country',
                'designation': 'Student',
                'roll': 124,
                'playerId': '1234567890abcdefg',
                'online': True
            }
        }
    )

    assert response.status_code == 201
    assert response.json['email'] == 'uname@iitk.ac.in'
    assert response.headers['Location'] == '/auth/signup/verify_otp'

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM awaitOTP WHERE username = 'uname'",
        ).fetchone() is not None

@pytest.mark.parametrize(('username', 'password', 'profile', 'status'), (
    ('', '', {}, 400),
    ('a', '', {}, 400),
    ('a', 'a', {}, 400),
    ('test', 'test', {
        'name': 'First M. Last',
        'email': 'uname25@example.com',
        'phone': '+91 12345 67890',
        'address': '123 Main St., City, Country',
        'designation': 'Student',
        'roll': 124,
        'online': False,
        'playerId': '1234567890abcdefg'
    }, 409),
    (None, 'test', {}, 400),
    ('#!2a', 'test', {
        'name': 'First M. Last',
        'email': 'uname25@example.com',
        'phone': '+91 12345 67890',
        'address': '123 Main St., City, Country',
        'designation': 'Student',
        'roll': 124,
        'online': False,
        'playerId': '1234567890abcdefg'
    }, 400),
    ('test', '', {
        'name': 'First M. Last',
        'email': 'uname25@example.com',
        'phone': '+91 12345 67890',
        'address': '123 Main St., City, Country',
        'designation': 'Student',
        'roll': 124,
        'online': False,
        'playerId': '1234567890abcdefg'
    }, 400),
))
def test_signup_get_otp_validate_input(client: FlaskClient, username, password, profile, status):
    response = client.post(
        '/auth/signup/get_otp',
        json = {'username': username, 'password': password, 'profile': profile} if username is not None else {'password': password, 'profile': profile}
    )

    assert response.status_code == status

def test_signup_verify_otp(client: FlaskClient, app: Flask):
    # Test with bad requests
    response = client.post(
        '/auth/signup/verify_otp',
        json = {
            'username': 'new'
        }
    )

    assert response.status_code == 400

    response = client.post(
        '/auth/signup/verify_otp',
        json = {
            'otp': 17
        }
    )

    assert response.status_code == 400

    response = client.post(
        '/auth/signup/verify_otp',
        json = {
            'username': 'new',
            'otp': '0017'
        }
    )

    assert response.status_code == 400

    # Test with outdated OTP
    response = client.post(
        '/auth/signup/verify_otp',
        json = {
            'username': 'new',
            'otp': 827
        }
    )

    assert response.status_code == 404

    # Update OTP send time
    with app.app_context():
        from datetime import datetime
        get_db().execute(
            "UPDATE awaitOTP SET created = ? WHERE username = 'new'",
            (int(datetime.now().timestamp()),)
        )
        get_db().commit()

    # Test with invalid username
    response = client.post(
        '/auth/signup/verify_otp',
        json = {
            'username': 'another',
            'otp': 9248
        }
    )

    assert response.status_code == 404

    # Test with incorrect OTP
    response = client.post(
        '/auth/signup/verify_otp',
        json = {
            'username': 'new',
            'otp': 9248
        }
    )

    assert response.status_code == 401

    # Test with correct OTP
    response = client.post(
        '/auth/signup/verify_otp',
        json = {
            'username': 'new',
            'otp': 827
        }
    )

    assert response.status_code == 201

def test_login(client: FlaskClient, app: Flask):
    response = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    )

    assert response.status_code == 200
    assert response.headers['Set-Cookie'].startswith('session=')
    user_id, user_role = response.json['id'], response.json['role']

    with app.app_context():
        row = get_db().execute(
            "SELECT id, role, counter FROM users WHERE username = 'test'",
        ).fetchone()

        assert row is not None
        assert row['id'] == user_id
        assert row['role'] == user_role

@pytest.mark.parametrize(('username', 'password', 'status'), (
    ('', '', 400),
    ('a', '', 400),
    ('a', 'a', 404),
    ('test', 'wrong', 401),
))
def test_login_validate_input(client: FlaskClient, app: Flask, username, password, status):
    response = client.post(
        '/auth/login',
        json = {'username': username, 'password': password}
    )

    assert response.status_code == status

    if username == 'test' and password == 'wrong':
        with app.app_context():
            db = get_db()

            for i in range(4):
                assert client.post(
                    '/auth/login',
                    json = {'username': username, 'password': password}
                ).status_code == 401

                assert db.execute(
                    "SELECT counter FROM users WHERE username = 'test'",
                ).fetchone()[0] == i + 2
                
            assert client.post(
                '/auth/login',
                json = {'username': username, 'password': password}
            ).status_code == 429

            assert db.execute(
                "SELECT counter FROM users WHERE username = 'test'",
            ).fetchone()[0] == 5

            sleep(LOGIN_COUNTER_RESET_DELAY.seconds + 1)
            assert client.post(
                '/auth/login',
                json = {'username': username, 'password': password}
            ).status_code == 401

            assert db.execute(
                "SELECT counter FROM users WHERE username = 'test'",
            ).fetchone()[0] == 1
    elif username == '':
        response = client.post(
            '/auth/login',
            json = {'password': password}
        )

        assert response.status_code == status
    elif password == '':
        response = client.post(
            '/auth/login',
            json = {'username': username}
        )

        assert response.status_code == status

def test_logout(client: FlaskClient):
    response = client.get('/auth/logout')
    assert response.status_code == 205

def test_change_password(client: FlaskClient, app: Flask):
    # Test without session cookie
    response = client.post(
        '/auth/change_password',
        json = {
            'old_password': 'test',
            'new_password': 'new_test'
        }
    )

    assert response.status_code == 401

    # Set session cookie
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test with session cookie
    response = client.post(
        '/auth/change_password',
        json = {
            'old_password': 'test',
            'new_password': 'new_test'
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 204

    # Check if password is changed in the database
    with app.app_context():
        assert check_password_hash(get_db().execute(
            "SELECT password FROM users WHERE username = 'test'",
        ).fetchone()[0], 'new_test')

    # Test with incorrect password
    response = client.post(
        '/auth/change_password',
        json = {
            'old_password': 'a',
            'new_password': 'new_test'
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 401

    # Test with empty new password
    response = client.post(
        '/auth/change_password',
        json = {
            'old_password': 'a',
            'new_password': ''
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 400

    # Test with empty old password
    response = client.post(
        '/auth/change_password',
        json = {
            'old_password': '',
            'new_password': '12'
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 400

def test_reset_password(client: FlaskClient):
    # NOTE: This test may be commented out because it sends an actual email.
    #       This may consume email resources.
    # pass

    response = client.post(
        '/auth/reset_password',
        json = {
            'username': 'test'
        }
    )

    assert response.status_code == 204

def test_reset_password_validate_input(client: FlaskClient):
    response = client.post(
        '/auth/reset_password',
        json = {
            'username': ''
        }
    )

    assert response.status_code == 400

    response = client.post(
        '/auth/reset_password',
        json = {
            'username': 'non_existent_user'
        }
    )

    assert response.status_code == 404