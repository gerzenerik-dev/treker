import os

# Must be set before any app module is imported so Settings() can initialize
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-purposes-only-32ch")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.services.auth import hash_password

# StaticPool forces all connections to share the same in-memory SQLite database,
# which is required because SQLite creates an isolated DB per connection by default.
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def regular_user(db):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("password123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_token(client, regular_user):
    resp = client.post("/auth/login", data={"username": "testuser", "password": "password123"})
    return resp.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    resp = client.post("/auth/login", data={"username": "admin", "password": "adminpass123"})
    return resp.json()["access_token"]
