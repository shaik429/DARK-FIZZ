"""Every kind of failure must come back as {"error", "message"} - never a raw 500.

These tests need NO database: DB errors are simulated, and "database down"
uses a real connection attempt to a port where nothing is listening.

Run from backend/:   pytest -v
"""

import pymysql
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.errors import AppError, not_found
from app.core.handlers import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SignupIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


@app.post("/signup")
def signup(body: SignupIn):
    return {"ok": True}


@app.get("/app-error")
def app_error():
    raise AppError(409, "EMAIL_ALREADY_EXISTS", "An account with this email already exists.")


@app.get("/products/{product_id}")
def get_product(product_id: int):
    raise not_found("Product")


@app.get("/duplicate-sku")
def duplicate_sku():
    orig = pymysql.err.IntegrityError(
        1062, "Duplicate entry 'STL-01' for key 'products.uq_products_sku'"
    )
    raise IntegrityError("INSERT INTO products ...", {}, orig)


@app.get("/negative-stock")
def negative_stock():
    orig = pymysql.err.OperationalError(
        3819, "Check constraint 'ck_stock_quants_quantity_non_negative' is violated."
    )
    raise OperationalError("UPDATE stock_quants ...", {}, orig)


@app.get("/bad-reference")
def bad_reference():
    orig = pymysql.err.IntegrityError(
        1452, "Cannot add or update a child row: a foreign key constraint fails"
    )
    raise IntegrityError("INSERT INTO products ...", {}, orig)


@app.get("/database-down")
def database_down():
    engine = create_engine("mysql+pymysql://u:p@127.0.0.1:1/nothing")  # nothing listens on port 1
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


@app.get("/crash")
def crash():
    raise ValueError("secret internal detail")


client = TestClient(app, raise_server_exceptions=False)


def assert_error_shape(response, status, error):
    body = response.json()
    assert response.status_code == status, body
    assert body["error"] == error, body
    assert isinstance(body["message"], str) and body["message"], body
    return body


def test_app_error():
    assert_error_shape(client.get("/app-error"), 409, "EMAIL_ALREADY_EXISTS")


def test_not_found_helper():
    body = assert_error_shape(client.get("/products/999"), 404, "NOT_FOUND")
    assert body["message"] == "Product not found."


def test_missing_field():
    r = client.post("/signup", json={"email": "a@b.com", "password": "Secret123"})
    body = assert_error_shape(r, 400, "VALIDATION_ERROR")
    assert body["message"] == "name is required."


def test_bad_email():
    r = client.post("/signup", json={"name": "A", "email": "not-an-email", "password": "Secret123"})
    body = assert_error_shape(r, 400, "VALIDATION_ERROR")
    assert body["details"][0]["field"] == "email"


def test_short_password():
    r = client.post("/signup", json={"name": "A", "email": "a@b.com", "password": "123"})
    body = assert_error_shape(r, 400, "VALIDATION_ERROR")
    assert body["details"][0]["field"] == "password"


def test_malformed_json():
    r = client.post("/signup", content="{not json", headers={"Content-Type": "application/json"})
    assert_error_shape(r, 400, "MALFORMED_REQUEST")


def test_invalid_id_type():
    assert_error_shape(client.get("/products/abc"), 400, "VALIDATION_ERROR")


def test_unknown_route():
    assert_error_shape(client.get("/does-not-exist"), 404, "NOT_FOUND")


def test_wrong_method():
    assert_error_shape(client.delete("/signup"), 405, "METHOD_NOT_ALLOWED")


def test_duplicate_sku():
    assert_error_shape(client.get("/duplicate-sku"), 409, "DUPLICATE_SKU")


def test_negative_stock_blocked():
    assert_error_shape(client.get("/negative-stock"), 409, "INSUFFICIENT_STOCK")


def test_bad_foreign_key():
    assert_error_shape(client.get("/bad-reference"), 400, "INVALID_REFERENCE")


def test_database_down_is_503():
    assert_error_shape(client.get("/database-down"), 503, "DATABASE_UNAVAILABLE")


def test_crash_hides_internal_details():
    body = assert_error_shape(client.get("/crash"), 500, "INTERNAL_ERROR")
    assert "secret internal detail" not in body["message"]
    assert "ref:" in body["message"]


def test_errors_keep_cors_headers():
    for path in ("/crash", "/app-error", "/database-down"):
        r = client.get(path, headers={"Origin": "http://localhost:5173"})
        assert r.headers.get("access-control-allow-origin") == "http://localhost:5173", path
