from lostify.otp_sender import send_otp
from lostify.password_sender import send_password

def test_send_otp_fail():
    """
    Test the send_otp function with invalid parameters.
    """

    fail = False

    try:
        send_otp(1 + 7j, "invalid_email", "Test User")
    except Exception as e:
        fail = True

    assert fail

def test_send_password_fail():
    """
    Test the send_password function with invalid parameters.
    """

    fail = False

    try:
        send_password(1 + 7j, "invalid_email", "Test User")
    except Exception as e:
        fail = True

    assert fail