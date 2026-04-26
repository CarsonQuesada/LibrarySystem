import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from backend.app import app
from backend.models import db, LibraryUser, Book
from backend.auth import hash_password


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        # 🔥 IMPORTANT: reset DB every test
        db.drop_all()
        db.create_all()

        # Create test users
        user = LibraryUser(
            name="User",
            email="user@test.com",
            password=hash_password("1234"),
            is_librarian=False
        )

        admin = LibraryUser(
            name="Admin",
            email="admin@test.com",
            password=hash_password("admin"),
            is_librarian=True
        )

        db.session.add_all([user, admin])

        # Create test book
        book = Book(
            title="Test Book",
            author="Author",
            isbn="123",
            copy_count=1,
            available_copies=1
        )

        db.session.add(book)
        db.session.commit()

    with app.test_client() as client:
        yield client