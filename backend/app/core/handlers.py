"""Global error handling.

register_exception_handlers(app) makes EVERY failure come back as
    {"error": "SOME_CODE", "message": "Something a person can read."}
and never as a raw 500 or a stack trace.

In app/main.py call it right after creating the app and BEFORE adding CORS,
so error responses still carry CORS headers:

    app = FastAPI(title="StockSense API")
    register_exception_handlers(app)
    app.add_middleware(CORSMiddleware, ...)
"""

import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import CHECK_CONSTRAINTS_BY_TABLE, UNIQUE_CONSTRAINTS, AppError
from app.core.logging_config import LOGGER_NAME, setup_logging

logger = logging.getLogger(LOGGER_NAME)

# MySQL error numbers we translate into readable errors
MYSQL_DUPLICATE = 1062
MYSQL_NULL_NOT_ALLOWED = 1048
MYSQL_DATA_TOO_LONG = 1406
MYSQL_CHECK_FAILED = 3819
MYSQL_PARENT_MISSING = (1216, 1452)  # foreign key points at a row that doesn't exist
MYSQL_ROW_IN_USE = (1217, 1451)  # deleting a row that other rows still point at
MYSQL_DEADLOCK = (1205, 1213)  # lock wait timeout / deadlock
MYSQL_UNAVAILABLE = (1040, 1044, 1045, 1049, 2002, 2003, 2006, 2013)  # can't reach / log in to DB

HTTP_CODES = {
    400: ("BAD_REQUEST", "The request could not be processed."),
    401: ("UNAUTHORIZED", "Please log in to continue."),
    403: ("FORBIDDEN", "You don't have permission to do this."),
    404: ("NOT_FOUND", "The requested resource was not found."),
    405: ("METHOD_NOT_ALLOWED", "This action is not allowed on this address."),
}


def error_response(status_code: int, error: str, message: str, details=None) -> JSONResponse:
    body = {"error": error, "message": message}
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)


# ---------------------------------------------------------------- handlers


async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.error, exc.message, exc.details)


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    if any(e.get("type") == "json_invalid" for e in errors):
        return error_response(400, "MALFORMED_REQUEST", "The request body is not valid JSON.")

    details = []
    for e in errors:
        field = ".".join(str(p) for p in e.get("loc", []) if p not in ("body", "query", "path"))
        field = field or "request"
        if e.get("type") == "missing":
            msg = f"{field} is required."
        else:
            msg = str(e.get("msg", "Invalid value.")).removeprefix("Value error, ")
        details.append({"field": field, "message": msg})

    first = details[0]
    message = (
        first["message"]
        if first["message"].startswith(first["field"])
        else (f"{first['field']}: {first['message']}")
    )
    return error_response(400, "VALIDATION_ERROR", message, details)


async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    error, default_message = HTTP_CODES.get(exc.status_code, ("HTTP_ERROR", "Request failed."))
    detail = exc.detail if isinstance(exc.detail, str) else None
    generic = {"Not Found", "Method Not Allowed", "Not authenticated", "Unauthorized", "Forbidden"}
    message = detail if detail and detail not in generic else default_message
    return error_response(exc.status_code, error, message)


async def handle_database_error(request: Request, exc: DBAPIError) -> JSONResponse:
    orig = getattr(exc, "orig", None)
    args = getattr(orig, "args", ()) or ()
    errno = args[0] if args and isinstance(args[0], int) else None
    text = str(args[1]) if len(args) > 1 else str(orig)

    if errno == MYSQL_DUPLICATE:
        key = _match(r"for key '([^']+)'", text).split(".")[-1]
        status, error, message = UNIQUE_CONSTRAINTS.get(
            key, (409, "DUPLICATE_RECORD", "This record already exists.")
        )
        logger.info("Duplicate blocked by %s on %s %s", key, request.method, request.url.path)
        return error_response(status, error, message)

    if errno == MYSQL_CHECK_FAILED:
        name = _match(r"[Cc]heck constraint '([^']+)'", text)
        status, error, message = _check_error(name)
        logger.info("CHECK %s blocked %s %s", name, request.method, request.url.path)
        return error_response(status, error, message)

    if errno in MYSQL_PARENT_MISSING:
        return error_response(400, "INVALID_REFERENCE", "One of the linked records does not exist.")

    if errno in MYSQL_ROW_IN_USE:
        return error_response(
            409, "RECORD_IN_USE", "This record is used by other records and can't be deleted."
        )

    if errno == MYSQL_NULL_NOT_ALLOWED:
        column = _match(r"Column '([^']+)'", text) or "A required field"
        return error_response(400, "MISSING_FIELD", f"{column} is required.")

    if errno == MYSQL_DATA_TOO_LONG:
        column = _match(r"column '([^']+)'", text) or "One of the values"
        return error_response(400, "VALUE_TOO_LONG", f"{column} is too long.")

    if errno in MYSQL_DEADLOCK:
        return error_response(
            409, "CONFLICT_RETRY", "Someone else changed this at the same moment. Please try again."
        )

    if errno in MYSQL_UNAVAILABLE or exc.connection_invalidated:
        logger.error("Database unavailable (%s) on %s %s", errno, request.method, request.url.path)
        return error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "The database is not reachable right now. Please try again in a moment.",
        )

    return _internal_error(request, exc)


# ---------------------------------------------------------------- helpers


def _match(pattern: str, text: str) -> str:
    found = re.search(pattern, text)
    return found.group(1) if found else ""


def _check_error(constraint_name: str):
    for table in sorted(CHECK_CONSTRAINTS_BY_TABLE, key=len, reverse=True):
        if constraint_name.startswith(f"ck_{table}_"):
            return CHECK_CONSTRAINTS_BY_TABLE[table]
    return 400, "CONSTRAINT_VIOLATION", "This change breaks a data rule and was not saved."


def _internal_error(request: Request, exc: Exception) -> JSONResponse:
    ref = uuid.uuid4().hex[:8]
    logger.exception("Unhandled error ref=%s on %s %s", ref, request.method, request.url.path)
    return error_response(
        500, "INTERNAL_ERROR", f"Something went wrong on our side. Please try again. (ref: {ref})"
    )


# ---------------------------------------------------------------- wiring


def register_exception_handlers(app: FastAPI) -> None:
    setup_logging()

    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(DBAPIError, handle_database_error)

    @app.middleware("http")
    async def log_and_catch(request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001  (anything no handler above caught)
            response = _internal_error(request, exc)
        ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.0f ms)", request.method, request.url.path, response.status_code, ms
        )
        return response
