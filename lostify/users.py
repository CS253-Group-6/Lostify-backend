from flask import Blueprint, request, g
from .db import get_db

users_bp = Blueprint("users", __name__, url_prefix = "/users")

@users_bp.route('/<int:id>/profile', methods = ('PUT', 'GET'))
def profile(id: int):
    """
    Update a user profile."
    expects JSON: {'userid':..., 'name':..., 'phone':...etc.}
    """

    if g.user_id is None:
        # HTTP 401: Unauthorized
        return ({
            "error": "Unauthorized",
            "message": "User not logged in"
        }, 401, {
            "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
        })
    
    if request.method == 'PUT':
        # Only the user associated with the profile can update it
        if g.user_id != id:
            # HTTP 403: Forbidden
            return ({
                "error": "Forbidden",
                "message": "Profile does not belong to user"
            }, 403)
    
        if not request.json:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": "No fields being updated"
            }, 400)
        
        name: str = request.json.get('name')
        phone: str = request.json.get('phone')
        email: str = request.json.get('email')
        address: str = request.json.get('address')
        designation: str = request.json.get('designation')
        roll: str = request.json.get('roll')
        image: str = request.json.get('image')

        error = None

        if not name and name is not None:
            error = "Name is required"

        if error is not None:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": error
            }, 400)
        
        db = get_db()

        with db:
            db.execute(
                ('UPDATE profiles SET '
                + ('name = ?,' if name is not None else '')
                + ('phone = ?,' if phone is not None else '')
                + ('email = ?,' if email is not None else '')
                + ('address = ?,' if address is not None else '')
                + ('designation = ?,' if designation is not None else '')
                + ('roll = ?,' if roll is not None else '')
                + ('image = ?,' if image is not None else ''))[:-1]
                + ' WHERE userid = ?',
                tuple(x for x in (name, phone, email, address, designation, roll, image, id) if x is not None)
            )

        # HTTP 204: No Content
        return ('', 204)
    
    if request.method == 'GET':
        # Any user can view any profile

        db = get_db()
        row = db.execute("SELECT * FROM profiles WHERE userid = ?", (id,)).fetchone()

        if row is None:
            # HTTP 404: Not Found
            return ({
                "error": "Not Found",
                "message": "User not found"
            }), 404

        # HTTP 200: OK
        return (dict(row), 200)
    
    # HTTP 405: Method Not Allowed
    return ({
        "error": "Method Not Allowed",
        "message": request.method
    }, 405, {
        "Allow": ["GET", "PUT"]
    })
