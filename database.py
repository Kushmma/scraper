"""
NepCompare — Database Setup
Flask-SQLAlchemy initialization and helper utilities.
"""

from flask_sqlalchemy import SQLAlchemy

# Single shared SQLAlchemy instance
db = SQLAlchemy()


def init_db(app):
    """
    Initialize the database with the Flask app.
    Creates all tables if they don't exist.
    """
    db.init_app(app)
    with app.app_context():
        # Import models so they are registered with SQLAlchemy
        import models  # noqa: F401

        db.create_all()
    return db
