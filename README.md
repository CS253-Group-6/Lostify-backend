# Backend

Lostify's backend exposes a RESTful API that can be called by the frontend. The backend is implemented
using Flask, with SQLite3 for database management.

## Dependencies

### Framework

Flask is a lightweight web framework written in Python. Flask is powered by Werkzeug, a library to
implement WSGI applications in Python conveniently.

### Database

The backend uses SQLite3, a lightweight relational database management system with no significant installation
requirements. The Python Standard Library comes with the `sqlite3` module to handle SQLite3 databases.

The database schema for the backend can be found at `lostify/schema.sql`.

### Email

Microsoft Azure Email Communication Service is used to dispatch email (such as OTPs) to users. The API for the
same is called via the relevant Python library.
