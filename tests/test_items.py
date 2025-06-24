import pytest
from flask import Flask
from flask.testing import FlaskClient
from lostify.db import get_db
from datetime import datetime

def test_create(client: FlaskClient, app: Flask):
    # Test adding an item without authentication
    response = client.post(
        '/items/post',
        json = {
            'type': 0,
            'title': 'Test Item',
            'description': 'This is a test item.',
            'location1': 'Test Location',
        }
    )

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test adding an item
    response = client.post(
        '/items/post',
        json = {
            'type': 0,
            'title': 'Test Item',
            'description': 'This is a test item.',
            'location1': 'Test Location',
            'date': int(datetime.now().timestamp()),
            'image': 'bIDsNSoAks-djeddneJED'
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 201
    assert type(response.json['id']) is int
    assert response.headers['Location'] == f"/items/{response.json['id']}"

    with app.app_context():
        assert get_db().execute(
            "SELECT creator FROM posts WHERE id = ?",
            (response.json['id'],)
        ).fetchone()[0] == 0    # ID of user 'test'

@pytest.mark.parametrize(('type', 'title', 'location1'), (
    (2, '', 'Test Location'),
    (1, 'Title', ''),
    (0, 25, None)
))
def test_create_validate_input(client: FlaskClient, type, title, location1):
    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test adding an item with invalid input
    response = client.post(
        '/items/post',
        json = {
            'type': type,
            'title': title,
            'location1': location1,
            'date': int(datetime.now().timestamp()),
            'posttype': 1
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 400

def test_retrieve(client: FlaskClient, app: Flask):
    # Test retrieving an item without authentication
    response = client.get('/items/1')

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test retrieving own post
    response = client.get(
        '/items/1',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 200
    assert response.json['id'] == 1

    # Test retrieving another user's post
    response = client.get(
        '/items/6',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 200
    assert response.json['id'] == 6

    # Test retrieving a non-existent item
    response = client.get(
        '/items/9999',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 404

def test_update(client: FlaskClient, app: Flask):
    # Test updating an item without authentication
    response = client.put(
        '/items/1',
        json = {
            'type': 0,
            'title': 'Updated Item',
            'description': 'This is an updated test item.',
            'location1': 'Updated Location'
        }
    )

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test updating an item
    response = client.put(
        '/items/1',
        json = {
            'type': 0,
            'title': 'Updated Item',
            'description': 'This is an updated test item.',
            'location1': 'Updated Location'
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 204

    with app.app_context():
        row = get_db().execute(
            "SELECT title, type FROM posts WHERE id = ?",
            (1,)
        ).fetchone()
        assert (row[0], row[1]) == ("Updated Item", 1)  # Updated title; type must not change

    # Test updating a non-existent item
    response = client.put(
        '/items/9999',
        json = {
            'type': 0,
            'title': 'Updated Item',
            'description': 'This is an updated test item.',
            'location1': 'Updated Location'
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 404

    # Test updating another user's post
    response = client.put(
        '/items/6',
        json = {
            'type': 0,
            'title': 'Updated Item',
            'description': 'This is an updated test item.',
            'location1': 'Updated Location'
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 403

    # Test empty update request
    response = client.put(
        '/items/1',
        json = {},
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 400

def test_delete(client: FlaskClient, app: Flask):
    # Test deleting an item without authentication
    response = client.delete('/items/1')

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test deleting an item
    response = client.delete(
        '/items/1',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 204

    with app.app_context():
        row = get_db().execute(
            "SELECT * FROM posts WHERE id = ?",
            (1,)
        ).fetchone()
        assert row is None  # Item should be deleted

    # Test deleting a non-existent item
    response = client.delete(
        '/items/9999',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 404

    # Test deleting another user's post
    response = client.delete(
        '/items/6',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 403

def test_retrieve_all(client: FlaskClient):
    # Test retrieving all items without authentication
    response = client.get('/items/all')

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test retrieving all items
    response = client.get(
        '/items/all',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 200
    assert type(response.json['posts']) is list  # Should return a list of items

def test_report_post(client: FlaskClient, app: Flask):
    # Test reporting a post without authentication
    response = client.put('/items/2/report')

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test reporting a post
    response = client.put(
        '/items/2/report',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 204
    
    with app.app_context():
        assert get_db().execute(
            "SELECT reportCount FROM posts WHERE id = ?",
            (2,)
        ).fetchone()[0] == 1  # Post should be reported
        
        assert get_db().execute(
            "SELECT * FROM reports WHERE postid = ? AND userid = ?",
            (2, 0)
        ).fetchone() is not None

    # Test idempotence
    response = client.put(
        '/items/2/report',
        headers = {
            'Cookie': cookie
        }
    )
    
    assert response.status_code == 204
    with app.app_context():
        assert get_db().execute(
            "SELECT reportCount FROM posts WHERE id = ?",
            (2,)
        ).fetchone()[0] == 1  # Report count should not increase
        assert get_db().execute(
            "SELECT * FROM reports WHERE postid = ? AND userid = ?",
            (2, 0)
        ).fetchone() is not None

    # Test reporting a non-existent item
    response = client.put(
        '/items/9999/report',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 404

def test_get_report_count(client: FlaskClient, app: Flask):
    # Test getting report count without authentication
    response = client.get('/items/4/report')

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test getting report count for a post as a non-admin user
    response = client.get(
        '/items/4/report',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 403

    # Authenticate as admin
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'other',
            'password': 'other'
        }
    ).headers['Set-Cookie']

    # Test getting report count for a post
    response = client.get(
        '/items/4/report',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 200
    assert response.json['reportCount'] == 5  # Report count should be 5

    # Test getting report count for a non-existent item
    response = client.get(
        '/items/9999/report',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 404

def test_delete_report(client: FlaskClient, app: Flask):
    # Test deleting a report without authentication
    response = client.delete('/items/4/report')

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Report the post first
    response = client.put(
        '/items/4/report',
        headers = {
            'Cookie': cookie
        }
    )

    # Test deleting own report
    response = client.delete(
        '/items/4/report',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 204
    with app.app_context():
        assert get_db().execute(
            "SELECT reportCount FROM posts WHERE id = ?",
            (4,)
        ).fetchone()[0] == 5

    # Test deleting a report not made
    response = client.delete(
        '/items/4/report',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 204
    with app.app_context():
        assert get_db().execute(
            "SELECT reportCount FROM posts WHERE id = ?",
            (4,)
        ).fetchone()[0] == 5    # Report count should not decrease

    # Test deleting a report from a non-existent post
    response = client.delete(
        '/items/9999/report',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 404

def test_claim(client: FlaskClient, app: Flask):
    # Test claiming an item without authentication
    response = client.post('/items/1/claim')

    assert response.status_code == 401

    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test claiming own item, direction 1
    response = client.post(
        '/items/1/claim',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 415

    with app.app_context():
        assert get_db().execute(
            "SELECT 1 FROM confirmations WHERE postid = ? AND initid = ? AND otherid = ?",
            (1, 0, 0)
        ).fetchone() is None

        # The action should not close the post
        assert get_db().execute(
            "SELECT closedBy FROM posts WHERE id = ?",
            (1,)
        ).fetchone()[0] is None

    # Test claiming own item, direction 2
    response = client.post(
        '/items/1/claim',
        json = {
            'otherid': 0
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 200

    with app.app_context():
        assert get_db().execute(
            "SELECT 1 FROM confirmations WHERE postid = ? AND initid = ? AND otherid = ?",
            (1, 0, 0)
        ).fetchone() is not None

        # The action should not close the post
        assert get_db().execute(
            "SELECT closedBy FROM posts WHERE id = ?",
            (1,)
        ).fetchone()[0] is None

    # Test claiming a non-existent item
    response = client.post(
        '/items/9999/claim',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 404

    # Test claiming item, direction 1
    response = client.post(
        '/items/7/claim',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 200
    assert response.json['closed'] == False

    with app.app_context():
        assert get_db().execute(
            "SELECT 1 FROM confirmations WHERE postid = ? AND initid = ? AND otherid = ?",
            (7, 0, 1)
        ).fetchone() is not None

        # The action should not close the post
        assert get_db().execute(
            "SELECT closedBy FROM posts WHERE id = ?",
            (7,)
        ).fetchone()[0] is None

    # Authenticate as other
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'other',
            'password': 'other'
        }
    ).headers['Set-Cookie']

    # Test claiming item, direction 2
    response = client.post(
        '/items/7/claim',
        json = {
            'otherid': 0
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 200
    assert response.json['closed'] == True

    with app.app_context():
        assert get_db().execute(
            "SELECT 1 FROM confirmations WHERE postid = ?",
            (7,)
        ).fetchone() is None

        # The action should close the post
        assert get_db().execute(
            "SELECT closedBy FROM posts WHERE id = ?",
            (7,)
        ).fetchone()[0] == 0  # ID of user 'test'

    # Test claiming item, direction 2
    response = client.post(
        '/items/8/claim',
        json = {
            'otherid': 0
        },
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 200
    assert response.json['closed'] == False

    with app.app_context():
        assert get_db().execute(
            "SELECT 1 FROM confirmations WHERE postid = ?",
            (8,)
        ).fetchone() is not None

        # The action should not close the post
        assert get_db().execute(
            "SELECT closedBy FROM posts WHERE id = ?",
            (8,)
        ).fetchone()[0] is None

    # Authenticate
    cookie = client.post(
        '/auth/login',
        json = {
            'username': 'test',
            'password': 'test'
        }
    ).headers['Set-Cookie']

    # Test claiming item, direction 1
    response = client.post(
        '/items/8/claim',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 200
    assert response.json['closed'] == True

    with app.app_context():
        assert get_db().execute(
            "SELECT 1 FROM confirmations WHERE postid = ?",
            (8,)
        ).fetchone() is None

        # The action should close the post
        assert get_db().execute(
            "SELECT closedBy FROM posts WHERE id = ?",
            (8,)
        ).fetchone()[0] == 0  # ID of user 'test'

    # Test conflict
    response = client.post(
        '/items/7/claim',
        headers = {
            'Cookie': cookie
        }
    )

    assert response.status_code == 409