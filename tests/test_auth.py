import pytest
from flask import Flask, g, session
from flask.testing import FlaskClient
from lostify.db import get_db
from lostify.auth import LOGIN_COUNTER_RESET_DELAY
from time import sleep

# def test_signup_get_otp(client: FlaskClient, app: Flask):
#     response = client.post(
#         '/auth/signup/get_otp',
#         json = {
#             'username': 'uname',
#             'password': 'pass',
#             'profile': {
#                 'name': 'First M. Last',
#                 'email': 'uname25@example.com',
#                 'phone': '+91 12345 67890',
#                 'address': '123 Main St., City, Country',
#                 'designation': 'Student',
#                 'roll': 124
#             }
#         }
#     )

#     assert response.status_code == 201
#     assert response.json['email'] == 'uname@iitk.ac.in'
#     assert response.headers['Location'] == '/auth/signup/verify_otp'

#     with app.app_context():
#         assert get_db().execute(
#             "SELECT * FROM awaitOTP WHERE username = 'uname'",
#         ).fetchone() is not None

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
        'roll': 124
    }, 409)
))
def test_signup_get_otp_validate_input(client: FlaskClient, username, password, profile, status):
    response = client.post(
        '/auth/signup/get_otp',
        json = {'username': username, 'password': password, 'profile': profile}
    )

    assert response.status_code == status

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

    with app.app_context():
        assert get_db().execute(
            "SELECT counter FROM users WHERE username = 'test'",
        ).fetchone()[0] is not None

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

