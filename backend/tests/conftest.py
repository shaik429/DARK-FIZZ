"""Test setup: a fresh in-memory SQLite database per test, seeded with demo data.

The real app uses MySQL; SQLite lets the tests run anywhere with no server.
Settings are filled with dummy values so app.config loads without a .env file.
"""

import os

for key, value in {
    "DB_USER": "test",
    "DB_PASSWORD": "test",
    "DB_NAME": "test",
    "SECRET_KEY": "test-secret-key-0123456789abcdef",
}.items():
    os.environ.setdefault(key, value)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app
from app.seed import seed


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    with Session() as db:
        seed(db)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def login(client, email="manager@stocksense.com", password="Manager@123") -> dict:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.json()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def manager(client):
    return login(client)


@pytest.fixture()
def staff(client):
    return login(client, "staff@stocksense.com", "Staff@123")
