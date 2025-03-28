from flask import (
    Blueprint, g, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db
from .otp_sender import send_otp

from secrets import SystemRandom
from datetime import datetime, timedelta
import json

OTP_TIMEOUT = timedelta(minutes = 5)
"""Time till expiration of OTP."""

LOGIN_COUNTER_RESET_DELAY = timedelta(seconds = 30)
"""Time till reset of login counter."""

auth_bp = Blueprint("auth", __name__, url_prefix = '/auth')
"""Blueprint for authentication."""

@auth_bp.route('/signup/get_otp', methods = ('POST',))
def get_otp():
    """
    Open a sign-in request and send an OTP to the user. Collects the user's
    username, password, and profile details.
    """

    if request.method == 'POST':
        # The signup details are transmitted through POST
        try:
            username: str   = request.json["username"]      # Username
            password: str   = request.json["password"]      # Plaintext password

            # If the request is sent through Basic Auth, use the following:
            # username: str = request.authorization["username"]   # Username
            # password: int = request.authorization["password"]   # Password
            profile : dict  = request.json["profile"]       # Profile details (as a `dict`)
        except KeyError as e:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": f"Field '{e.args[0]}' is required"
            }, 400)

        # Check types to validate request
        if (
            type(username) is not str
            or type(password) is not str
            or type(profile) is not dict
            or not (
                type(profile.get("name"))
                is type(profile.get("email"))
                is type(profile.get("phone"))
                is type(profile.get("address"))
                is type(profile.get("designation"))
                is str
            ) or type(profile.get("roll")) is not int
            or (profile.get("image") is not None and type(profile["image"]) is not str)
        ):
            # raise TypeError(
            #     "Signup: Type mismatch for JSON field(s) in POST request"
            # )
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": "Type mismatch for JSON field(s) in POST request"
            }, 400)
        
        # Check if username is alphanumeric so that the email address
        # <username>@iitk.ac.in is valid.
        if not username.isalnum():
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": "Username must be alphanumeric"
            }, 400)
        
        error = None    # Error message

        # Check that the fields are not empty
        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        # TODO: Similar checks for compulsory profile fields.

        
        if error is not None:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": error
            }, 400)
        
        # Retrieve the connection to the database
        db = get_db()

        # Check if the user is already signed up
        if (
            len(
                db.execute(
                    "SELECT 1 FROM users WHERE username = ? LIMIT 1",
                    (username,)
                ).fetchall()
            ) > 0
        ):
            # HTTP 409: Conflict
            return ({
                "error": "Conflict",
                "message": "User already exists"
            }, 409)
        
        # Generate otp
        otp = SystemRandom().randrange(1000000)

        # Send otp
        # If OTP sending fails, a RuntimeError is raised.
        send_otp(otp, f"{username}@iitk.ac.in", profile["name"])

        # Update database
        db.execute(
            "INSERT INTO awaitOTP(username, password, otp, created, profile) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT DO UPDATE "
                "SET otp = excluded.otp, "
                "created = excluded.created, "
                "profile = excluded.profile",
            (
                username,
                generate_password_hash(password),
                otp,
                int(datetime.now().timestamp()),
                json.dumps(
                    request.json["profile"],
                    ensure_ascii = False,
                    separators = (',', ':')
                )
            )
        )

        # Commit changes
        db.commit()

        # HTTP 201: Created
        return ({
            "message": "OTP sent",
            "email": f"{username}@iitk.ac.in",
            "username": username
        }, 201, {
            "Location": f"{url_for('auth.verify_otp')}"
        })

    # HTTP 405: Method Not Allowed
    return ({
        "error": "Method Not Allowed",
        "message": request.method
    }, 405, {
        "Allow": ["POST"]
    })

@auth_bp.route('/signup/verify_otp', methods = ('POST',))
def verify_otp():
    """
    Verify the OTP sent to the user and sign them up if the OTP is correct.
    """

    if request.method == 'POST':
        # The otp is transmitted through POST
        try:
            username: str = request.json["username"]        # Username
            otp     : int = request.json["otp"]             # OTP

            # If the request is sent through Basic Auth, use the following:
            # username: str = request.authorization["username"]   # Username
            # otp     : int = request.authorization["otp"]        # OTP
        except KeyError as e:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": f"Field '{e.args[0]}' is required"
            }, 400)

        # Check types to validate request
        if type(username) is not str or type(otp) is not int:
            # raise TypeError(
            #     "Signup: Type mismatch for JSON field(s) in POST request"
            # )
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": "Type mismatch for JSON field(s) in POST request"
            }, 400)

        error = None    # Error message

        # Check that the fields are not empty
        if not username:
            error = "Username is required."
        
        if error is not None:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": error
            }, 400)
        
        # Retrieve the connection to the database
        db = get_db()

        # Check if the user has an OTP sent
        row = db.execute("SELECT * FROM awaitOTP WHERE username = ? LIMIT 1", (username,)).fetchone()

        if row is None:
            # HTTP 404: Not Found
            return ({
                "error": "Not Found",
                "message": "Username not found"
            }, 404)
        
        if datetime.now() - datetime.fromtimestamp(row["created"]) > OTP_TIMEOUT:
            # HTTP 404: Not Found
            return ({
                "error": "Not Found",
                "message": "OTP timed out"
            }, 404)
        
        if row['otp'] != otp:
            # HTTP 401: Unauthorized
            return ({
                "error": "Unauthorized",
                "message": "Incorrect OTP"
            }, 401, {
                "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
            })
        
        # Context manager automatically commits changes on success
        # and rolls back on failure.
        with db:
            # Move record to users and profile tables
            profile: dict = json.loads(row["profile"])

            db.execute(
                "INSERT INTO users(username, password, role) "
                    "VALUES (?, ?, ?)",
                (username, row["password"], 0)
            )

            user_id = db.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()['id']

            db.execute(
                "INSERT INTO profiles(userid, name, phone, email, address, designation, roll, image) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    profile['name'],
                    profile.get('phone'),
                    profile.get('email'),
                    profile.get('address'),
                    profile.get('designation'),
                    profile['roll'],
                    profile.get('image')
                )
            )

            # Delete record from awaitOTP
            db.execute(
                "DELETE FROM awaitOTP WHERE username = ?",
                (username,)
            )

        # HTTP 201: Created
        return ({
            "message": f"{username} signed up",
            "user": {
                "username": username,
                "role": 'student',
                "profile": profile
            }
        }, 201, {
            # TODO: Fix the URL
            "Location": '' # f"{url_for(f'user.profile', id = user_id)}"
        })
    
        # NOTE: The client is required to login after this step. Signing up
        #       does not automatically log the user in or create a session.

    # HTTP 405: Method Not Allowed
    return ({
        "error": "Method Not Allowed",
        "message": request.method
    }, 405, {
        "Allow": ["POST"]
    })

@auth_bp.route('/login', methods = ('POST',))
def login():
    """
    Authenticate the user. Sets a session cookie on successful login.
    """

    if request.method == 'POST':
        try:
            # The login credentials are transmitted through POST
            username: str = request.json["username"]
            password: str = request.json["password"]

            # If the request is sent through Basic Auth, use the following:
            # username: str = request.authorization["username"]   # Username
            # password: int = request.authorization["password"]   # Password
        except KeyError as e:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": f"Field '{e.args[0]}' is required"
            }, 400)

        # Retrieve the connection to the database
        db = get_db()
        error = None    # Error message

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is not None:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": error
            }, 400)

        # Fetch records from the database
        row = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if row is None:
            # HTTP 404: Not Found
            return ({
                "error": "Not Found",
                "message": "Username not found"
            }, 404)
        
        if row["counter"] >= 5 and datetime.now() - datetime.fromtimestamp(row["lastAttempt"]) < LOGIN_COUNTER_RESET_DELAY:
            # HTTP 429: Too Many Requests
            return ({
                "error": "Too Many Requests",
                "message": "Login attempt limit reached"
            }, 429, {
                "Retry-After": int((LOGIN_COUNTER_RESET_DELAY - (datetime.now() - datetime.fromtimestamp(row["lastAttempt"]))).total_seconds())
            })

        if not check_password_hash(row["password"], password):
            # Incorrect password; increment counter for failed attempts
            db.execute(
                "UPDATE users SET counter = ? WHERE username = ?",
                (row["counter"] + 1, username)
            )
            db.commit()

            # HTTP 401: Unauthorized
            return ({
                "error": "Unauthorized",
                "message": "Incorrect password"
            }, 401, {
                "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
            })
        
        db.execute(
            "UPDATE users SET counter = ? WHERE username = ?", (0, username)
        )
        db.commit()

        # If successful, set session cookie
        session.clear()
        session["user_id"] = row["id"]      # Set session cookie
        session["user_role"] = row["role"]  # Set session cookie

        # HTTP 200: OK
        return ({
            "message": "User authenticated"
        }, 200)
        
    # HTTP 405: Method Not Allowed
    return ({
        "error": "Method Not Allowed",
        "message": request.method
    }, 405, {
        "Allow": ["POST"]
    }) 

# Called before every handling request dispatched to the app.
@auth_bp.before_app_request
def load_logged_in_user():
    """
    Load the user id from the session cookie, if it exists.
    """

    # Get session cookie
    g.user_id = session.get('user_id')
    g.user_role = session.get('user_role')

@auth_bp.route('/logout')
def logout():
    """
    Log the user out by clearing the session cookie.
    """

    # Clear session cookie
    session.clear()

    # HTTP 205: Reset Content
    return ('', 205)

@auth_bp.route('/change_password', methods = ('POST',))
def change_password():
    """
    Change the account password.
    """

    if g.user_id is None:
        # HTTP 401: Unauthorized
        return ({
            "error": "Unauthorized",
            "message": "User not logged in"
        }, 401, {
            "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
        })

    if request.method == 'POST':
        # The login credentials are transmitted through POST
        old_password: str = request.json["old_password"]
        new_password: str = request.json["new_password"]

        # Retrieve the connection to the database
        db = get_db()
        error = None    # Error message

        if not old_password:
            error = "Old password is required."
        elif not new_password:
            error = "New password is required."

        if error is not None:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": error
            }, 400)

        # Fetch records from the database
        row = db.execute(
            "SELECT password FROM users WHERE id = ?", (g.user_id,)
        ).fetchone()

        if row is None:
            # HTTP 404: Not Found
            return ({
                "error": "Not Found",
                "message": "Username not found"
            }, 404)
        
        if not check_password_hash(row["password"], old_password):
            # HTTP 401: Unauthorized
            return ({
                "error": "Unauthorized",
                "message": "Incorrect password"
            }, 401, {
                "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
            })

        db.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (generate_password_hash(new_password), g.user_id)
        )
        db.commit()

        # HTTP 204: No Content
        return ('', 204)
        
    # HTTP 405: Method Not Allowed
    return ({
        "error": "Method Not Allowed",
        "message": request.method
    }, 405, {
        "Allow": ["POST"]
    })
