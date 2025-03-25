"""
*file: lostify/db.py*

------
Functions for database retrieval for the current request (handled through
`flask.g`) and for app initialisation in the context of database handling.

Also registers the command-line command `init-db` to initialise
the database using a SQLite3 schema (retrieved from the file `schema.sql`)
for first-time use.
"""

import sqlite3
from datetime import datetime
import click
from flask import Flask, current_app, g

def get_db() -> sqlite3.Connection:
    """
    Get a SQLite3 database connection object (`sqlite3.Connection`) to the
    database stored at the path specified by the value corresponding to 
    `'DATABASE'` in the configuration dictionary of the current app (*i.e.*,
    `current_app.config['DATABASE']`). The returned connection object is also
    cached in `g.db`.

    If `g` already has a member `db`, it is assumed that it holds an open
    connection object to the database; in that case, `g.db` is returned
    without opening a new connection.
    """

    if "db" not in g:
        # A connection has not been set up previously
        # Create a connection
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types = sqlite3.PARSE_DECLTYPES
        )

        g.db.row_factory = sqlite3.Row

        g.db.execute("PRAGMA foreign_keys = ON")

    # Return the connection to the database
    return g.db

def close_db(e = None):
    """
    Close the SQLite3 database connection object at `g.db` if it exists.

    :param e:
    Exception or `None`.
    """

    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """
    Initialise the database from the schema at `schema.sql`. For use by
    the command `init-db`.
    """

    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode("utf8"))

@click.command('init-db')
def init_db_command():
    """
    Clear the existing data and create new tables. Called by the command
    `init-db`.
    """

    init_db()
    click.echo("Initialised the database.")

# Register a converter for timestamps retrieved from the database to
# Python `datetime.datetime` instances.
sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)

def init_app(app: Flask):
    """
    Initialise the app. Performs the following:

    - Registers `close_db` as a teardown function for the application context
      (`app.app_context()`).

    - Adds the `init-db` command to `app.cli`.

    :param app:
    `Flask` instance corresponding to the current Flask application.
    """

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)