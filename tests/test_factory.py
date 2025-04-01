from lostify import create_app

def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing

def test_hello(client):
    """
    Test the `/hello` endpoint. Basic connection test.
    """

    response = client.get('/hello')
    assert response.data == b'Hello, world!'