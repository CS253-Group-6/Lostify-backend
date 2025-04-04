from flask import (
    Blueprint, g, request, url_for
)

from datetime import datetime

from .db import get_db

items_bp = Blueprint('items', __name__, url_prefix='/items')

@items_bp.route('/post', methods = ('POST',))
def post():
    """
    Create a new post.
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
        try:
            type        : int = request.json['type']
            title       : str = request.json['title']
            description : str = request.json.get('description')
            location1   : str = request.json['location1']
            location2   : str = request.json.get('location2')
            image       : str = request.json.get('image')
        except KeyError as e:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": f"Field '{e.args[0]}' is required"
            }, 400)

        error = None

        if not title:
            error = 'Item name is required.'
        elif not location1:
            error = 'Location 1 is required.' 
        elif type not in (0, 1):
            error = 'Type must be either 0 or 1.'   

        if error is not None:
            # HTTP 400: Bad Request
            return ({
                "error": "Bad Request",
                "message": error
            }, 400)
        
        if image is not None:
            image = bytes(image, 'utf-8')
        
        db = get_db()

        db.execute(
            'INSERT INTO posts ('
                'title,'
                'creator,'
                'description,'
                'image,'
                'type,'
                'location1,'
                'location2,'
                'date'
                ') VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (title, g.user_id, description, image, type, location1, location2, int(datetime.now().timestamp()))
        )
        db.commit()
        post_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # HTTP 201: Created
        return ({
            "message": "Post created successfully",
            "id": post_id
        }, 201, {
            "Location": f"{url_for(f'.post_actions', id = post_id)}"
        })
    
    # HTTP 405: Method Not Allowed
    return ({
        "error": "Method Not Allowed",
        "message": request.method
    }, 405, {
        "Allow": ["POST"]
    })

def get(id: int):
    """
    Retrieve a post by its ID.
    """

    if g.user_id is None:
        # HTTP 401: Unauthorized
        return ({
            "error": "Unauthorized",
            "message": "User not logged in"
        }, 401, {
            "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
        })

    db = get_db()
    row = db.execute(
        "SELECT "
            "title,"
            "creator,"
            "description,"
            "date,"
            "location1,"
            "location2,"
            "type,"
            "closedBy,"
            "closedDate,"
            "image"
            " FROM posts WHERE id = ?",
        (id,)
    ).fetchone()

    if row is None:
        # HTTP 404: Not Found
        return ({
            "error": "Not Found",
            "message": f"Post not found"
        }, 404)

    # HTTP 200: OK
    return ({
        'id': id,
        'title': row['title'],
        'location1': row['location1'],
        'location2': row['location2'],
        'date': row['date'],
        'image': row['image'],
        'type': row['type'],
        'creator': row['creator'],
        'description': row['description'],
        'closedBy': row['closedBy'],
        'closedDate': row['closedDate']
    }, 200)

def put(id: int):
    """
    Update an item.
    """

    if g.user_id is None:
        # HTTP 401: Unauthorized
        return ({
            "error": "Unauthorized",
            "message": "User not logged in"
        }, 401, {
            "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
        })
    
    db = get_db()
    row = db.execute(
        "SELECT creator FROM posts WHERE id = ?", (id,)
    ).fetchone()

    if row is None:
        # HTTP 404: Not Found
        return ({
            "error": "Not Found",
            "message": "Post not found"
        }, 404)
    
    if g.user_id != row[0]:
        # HTTP 403: Forbidden
        return ({
            "error": "Forbidden",
            "message": "User is not creator of post"
        }, 403)

    title: str = request.json.get('title')
    description: str = request.json.get('description')
    image: str = request.json.get('image')
    location1: str = request.json.get('location1')
    location2: str = request.json.get('location2')

    error = None

    if title is description is image is location1 is location2 is None:
        error = 'No fields to update.'
    elif not title and title is not None:
        error = 'Item name is required.'
    elif not location1 and location1 is not None:
        error = 'Location 1 is required.'

    if error is not None:
        # HTTP 400: Bad Request
        return ({
            "error": "Bad Request",
            "message": error
        }, 400)
    else:
        if image is not None:
            image = bytes(image, 'utf-8')
            
        db.execute(
            ('UPDATE posts SET '
            + ('title = ?,' if title is not None else '')
            + ('description = ?,' if description is not None else '')
            + ('image = ?,' if image is not None else '')
            + ('location1 = ?,' if location1 is not None else '')
            + ('location2 = ?,' if location2 is not None else ''))[:-1]
            + ' WHERE id = ?',
            tuple(x for x in (title, description, image, location1, location2, id) if x is not None)
        )
        db.commit()
        
        # HTTP 204: No Content
        return ('', 204)

def delete(id: int):
    """
    Delete a post.
    """   

    if g.user_id is None:
        # HTTP 401: Unauthorized
        return ({
            "error": "Unauthorized",
            "message": "User not logged in"
        }, 401, {
            "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
        })
    
    db = get_db()
    row = db.execute(
        "SELECT creator FROM posts WHERE id = ?", (id,)
    ).fetchone()

    if row is None:
        # HTTP 404: Not Found
        return ({
            "error": "Not Found",
            "message": "Post not found"
        }, 404)
    
    if g.user_role != 1 and g.user_id != row[0]:
        # HTTP 403: Forbidden
        return ({
            "error": "Forbidden",
            "message": "User is not authorised to delete post"
        }, 403)

    db.execute('DELETE FROM posts WHERE id = ?', (id,))
    db.commit()

    # HTTP 204: No Content
    return ('', 204)

@items_bp.route('/<int:id>', methods = ('GET', 'PUT', 'DELETE'))
def post_actions(id: int):
    """
    Perform an action on a post, determined by the HTTP method.
    """

    if request.method == 'GET':
        return get(id)
    elif request.method == 'PUT':
        return put(id)
    elif request.method == 'DELETE':
        return delete(id)
    else:
        # HTTP 405: Method Not Allowed
        return ({
            "error": "Method Not Allowed",
            "message": request.method
        }, 405, {
            "Allow": ["GET", "PUT", "DELETE"]
        })

@items_bp.route('/all', methods = ('GET',))
def get_all():
    """
    Retrieve all posts.
    """

    if g.user_id is None:
        # HTTP 401: Unauthorized
        return ({
            "error": "Unauthorized",
            "message": "User not logged in"
        }, 401, {
            "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
        })
    
    if request.method == 'GET':
        db = get_db()
        rows = db.execute(
            "SELECT "
                "id,"
                "title,"
                "creator,"
                "description,"
                "date,"
                "location1,"
                "location2,"
                "type,"
                "closedBy,"
                "closedDate,"
                "image"
                " FROM posts"
        ).fetchall()

        # HTTP 200: OK
        return ({
            'posts': [
                {
                    'id': row['id'],
                    'title': row['title'],
                    'location1': row['location1'],
                    'location2': row['location2'],
                    'date': row['date'],
                    'image': row['image'],
                    'type': row['type'],
                    'creator': row['creator'],
                    'description': row['description'],
                    'closedBy': row['closedBy'],
                    'closedDate': row['closedDate']
                } for row in rows
            ]
        }, 200)

    # HTTP 405: Method Not Allowed
    return ({
        "error": "Method Not Allowed",
        "message": request.method
    }, 405, {
        "Allow": ["GET"]
    })
        
# Claim an item (post) by searching its id or scrolling through the found section
@items_bp.route('/<int:id>/claim', methods = ('POST',))
def claim(id: int):
    if g.user_id is None:
        # HTTP 401: Unauthorized
        return ({
            "error": "Unauthorized",
            "message": "User not logged in"
        }, 401, {
            "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
        })
     
    if request.method == 'POST':        
        db = get_db()

        with db:
            row = db.execute("SELECT creator, closedBy FROM posts WHERE id = ?", (id,)).fetchone()
            
            # Check if the post exists
            if row is None:
                # HTTP 404: Not Found
                return ({
                    "error": "Not Found",
                    "message": "Post not found"
                }, 404)
            
            # Check if the post is already claimed
            if row[1] is not None:
                # HTTP 409: Conflict
                return ({
                    "error": "Conflict",
                    "message": "Post already claimed"
                }, 409)
            
            # Check if the user is the creator of the post
            if g.user_id == row['creator']:
                otherid: int = request.json.get('otherid')

                if type(otherid) is not int:
                    # HTTP 400: Bad Request
                    return ({
                        "error": "Bad Request",
                        "message": "Id of second party is required"
                    }, 400)
            
                # Check if the other user exists
                if db.execute("SELECT 1 FROM users WHERE id = ?", (otherid,)).fetchone() is None:
                    # HTTP 404: Not Found
                    return ({
                        "error": "Not Found",
                        "message": "Second party not found"
                    }, 404)
                
                # Check if the other user has already claimed the post
                if db.execute("SELECT 1 FROM confirmations WHERE postid = ? AND initid = ?", (id, otherid)).fetchone() is not None:
                    db.execute("UPDATE posts SET closedBy = ?, closedDate = ? WHERE id = ?", (otherid, int(datetime.now().timestamp()), id))
                    db.execute("DELETE FROM confirmations WHERE postid = ?", (id,))
                    db.commit()

                    # HTTP 200: OK
                    return ({
                        'closed': True,
                        'postid': id,
                        'creator': g.user_id,
                        'closedBy': otherid
                    }, 200)
                else:
                    # Replace any previous confirmations by the creator
                    db.execute(
                        'INSERT INTO confirmations (postid, initid, otherid) VALUES (?, ?, ?)',
                        (id, g.user_id, otherid)
                    )
                    db.commit()

                    # HTTP 200: OK
                    return ({
                        'closed': False,
                        'postid': id,
                        'creator': g.user_id
                    }, 200)
            else:
                otherid: int = row['creator']

                # Check if the other user has already claimed the post
                if db.execute(
                    "SELECT 1 FROM confirmations WHERE postid = ? AND otherid = ?",
                    (id, g.user_id)
                ).fetchone() is not None:
                    db.execute("UPDATE posts SET closedBy = ?, closedDate = ? WHERE id = ?", (g.user_id, int(datetime.now().timestamp()), id))
                    db.execute("DELETE FROM confirmations WHERE postid = ?", (id,))
                    db.commit()

                    # HTTP 200: OK
                    return ({
                        'closed': True,
                        'postid': id,
                        'creator': otherid,
                        'closedBy': g.user_id
                    }, 200)
                else:
                    # Replace any previous confirmations by the user
                    db.execute(
                        'INSERT INTO confirmations (postid, initid, otherid) VALUES (?, ?, ?)',
                        (id, g.user_id, otherid)
                    )
                    db.commit()

                    # HTTP 200: OK
                    return ({
                        'closed': False,
                        'postid': id,
                        'creator': otherid
                    }, 200)

    # HTTP 405: Method Not Allowed
    return ({
        "error": "Method Not Allowed",
        "message": request.method
    }, 405, {
        "Allow": ["POST"]
    })
        
@items_bp.route("/<int:id>/report", methods=('GET', 'PUT', 'DELETE'))
def report_post(id: int):
    """
    Report a post or undo it.
    """
    
    if g.user_id is None:
        # HTTP 401: Unauthorized
        return ({
            "error": "Unauthorized",
            "message": "User not logged in"
        }, 401, {
            "WWW-Authenticate": "Basic"     # Relevant only if the request was sent through Basic Auth
        })
    
    conn = get_db()

    if request.method == 'GET':
        if g.user_role == 1:
            row = conn.execute("SELECT reportCount FROM posts WHERE id = ?", (id,)).fetchone()
            if row is None:
                # HTTP 404: Not Found
                return ({
                    "error": "Not Found",
                    "message": "Post not found"
                }, 404)
            
            # HTTP 200: OK
            return ({
                'reportCount': row[0]
            }, 200)
        else:
            # HTTP 403: Forbidden
            return ({
                "error": "Forbidden",
                "message": "User is not authorised to view report count"
            }, 403)

    # Check if the post exists
    if conn.execute("SELECT 1 FROM posts WHERE id = ?", (id,)).fetchone() is None:
        # HTTP 404: Not Found
        return ({
            "error": "Not Found",
            "message": "Post not found"
        }, 404)

    if request.method == 'PUT':
        if conn.execute("SELECT 1 FROM reports WHERE postid = ? AND userid = ?", (id, g.user_id)).fetchone() is None:
            # Insert a new report
            conn.execute("INSERT INTO reports (postid, userid) VALUES (?, ?)", (id, g.user_id))
            # Update the report count
            conn.execute("UPDATE posts SET reportCount = reportCount + 1 WHERE id = ?", (id,))
            conn.commit()
        
        # HTTP 204: No content
        return ('', 204)
    
    if request.method == 'DELETE':
        if conn.execute("SELECT 1 FROM reports WHERE postid = ? AND userid = ?", (id, g.user_id)).fetchone() is not None:
            # Remove the report
            conn.execute("DELETE FROM reports WHERE postid = ? AND userid = ?", (id, g.user_id))
            # Update the report count
            conn.execute("UPDATE posts SET reportCount = reportCount - 1 WHERE id = ?", (id,))
            conn.commit()
        
        # HTTP 204: No content
        return ('', 204)
    
    # HTTP 405: Method Not Allowed
    return ({
        "error": "Method Not Allowed",
        "message": request.method
    }, 405, {
        "Allow": ["GET", "PUT", "DELETE"]
    })
