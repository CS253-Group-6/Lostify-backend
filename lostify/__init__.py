import os
from flask import Flask
from dotenv import dotenv_values

def create_app(test_config = None):
    env = dotenv_values(".env")                     # Load environment variables from .env file

    # Create the app
    app = Flask(__name__, instance_relative_config = True)

    # Configure the app
    app.config.from_mapping(
        SECRET_KEY = env['FLASK_SECRET_KEY'],       # Used for signing cookies
        DATABASE = os.path.join(app.instance_path, env['FLASK_DB_NAME'])    # Path to the SQLite database
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent = True)
    else:
        # Load the test config if passed in (for testing only)
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        # Directory exists
        pass

    # A simple page that says "Hello, world!" for testing purposes
    @app.route('/hello')
    def hello():
        return "Hello, world!"
    
    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.auth_bp)

    from . import items
    app.register_blueprint(items.items_bp)

    from . import users
    app.register_blueprint(users.users_bp)

    return app