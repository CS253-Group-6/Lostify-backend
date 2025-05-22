# Backend

[![Build and deploy to Azure](https://github.com/CS253-Group-6/Lostify-backend/actions/workflows/main_lostify.yml/badge.svg)](https://github.com/CS253-Group-6/Lostify-backend/actions/workflows/main_lostify.yml)

Lostify's backend exposes a RESTful API that can be called by the frontend.
The backend is implemented using Flask, with SQLite3 for database management.

## Dependencies

### Framework

[Flask](https://pypi.org/project/Flask/) is a lightweight web framework written
in Python. Flask is powered by [Werkzeug](https://pypi.org/project/Werkzeug/),
a library to implement WSGI applications in Python conveniently.

### Database

The backend uses SQLite3, a lightweight relational database management system
with no significant installation requirements. The Python Standard Library
comes with the [`sqlite3` module](https://docs.python.org/3/library/sqlite3.html)
to handle SQLite3 databases.

The database schema for the backend can be found at `lostify/schema.sql`.

### Email

Microsoft Azure Email Communication Service is used to dispatch email (such as
OTPs) to users. The API for the same is called via the
[relevant Python library](https://pypi.org/project/azure-communication-email/).

## Testing

Unit tests are in the [`tests`](tests) directory. The tests are written for
the [pytest](https://pypi.org/project/pytest/) unit-testing framework. The
tests can be run with [coverage](https://pypi.org/project/coverage/).

## Deployment

The backend is currently deployed on Azure using Azure App Services with a 
CI/CD pipeline that builds, tests, and deploys any pushes to the branch.
