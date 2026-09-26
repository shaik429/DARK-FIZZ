"""Application errors.

Every error the API returns has the same shape:

    {"error": "DUPLICATE_SKU", "message": "A product with this SKU already exists."}

Services raise AppError for expected problems (bad input, not found, not
allowed). app/core/handlers.py turns AppError - and every other failure,
including database errors - into that shape. Users never see a stack trace.
"""

from __future__ import annotations


class AppError(Exception):
    """An expected, user-facing error."""

    def __init__(self, status_code: int, error: str, message: str, details: list | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.error = error
        self.message = message
        self.details = details


# Shortcuts for the most common cases -------------------------------------


def not_found(entity: str) -> AppError:
    return AppError(404, "NOT_FOUND", f"{entity} not found.")


def unauthorized(message: str = "Please log in to continue.") -> AppError:
    return AppError(401, "UNAUTHORIZED", message)


def forbidden(message: str = "You don't have permission to do this.") -> AppError:
    return AppError(403, "FORBIDDEN", message)


# Database constraint -> user-facing error ---------------------------------
# Names follow the naming convention in app/database.py
# (uq_<table>_<first column>, ck_<table>_<name>).

UNIQUE_CONSTRAINTS = {
    "uq_users_email": (409, "EMAIL_ALREADY_EXISTS", "An account with this email already exists."),
    "uq_products_sku": (409, "DUPLICATE_SKU", "A product with this SKU already exists."),
    "uq_warehouses_name": (
        409,
        "DUPLICATE_WAREHOUSE",
        "A warehouse with this name already exists.",
    ),
    "uq_warehouses_code": (
        409,
        "DUPLICATE_WAREHOUSE",
        "A warehouse with this code already exists.",
    ),
    "uq_locations_warehouse_id": (
        409,
        "DUPLICATE_LOCATION",
        "This warehouse already has a location with this name.",
    ),
    "uq_categories_name": (409, "DUPLICATE_CATEGORY", "A category with this name already exists."),
    "uq_uoms_name": (409, "DUPLICATE_UOM", "This unit of measure already exists."),
    "uq_reorder_rules_product_id": (
        409,
        "DUPLICATE_REORDER_RULE",
        "This product already has a reorder rule for this warehouse.",
    ),
    "uq_operations_reference": (
        409,
        "DUPLICATE_REFERENCE",
        "An operation with this reference already exists.",
    ),
    "uq_operation_lines_operation_id": (
        409,
        "DUPLICATE_PRODUCT_LINE",
        "This product is already on this operation.",
    ),
}
# Same errors if a column was declared with unique=True, index=True
UNIQUE_CONSTRAINTS["ix_users_email"] = UNIQUE_CONSTRAINTS["uq_users_email"]
UNIQUE_CONSTRAINTS["ix_products_sku"] = UNIQUE_CONSTRAINTS["uq_products_sku"]

# CHECK constraints are matched by table, so the exact name after the table
# doesn't matter (ck_stock_quants_anything -> INSUFFICIENT_STOCK).
CHECK_CONSTRAINTS_BY_TABLE = {
    "stock_quants": (409, "INSUFFICIENT_STOCK", "Not enough stock at this location."),
    "operations": (400, "SAME_LOCATION", "Source and destination locations must be different."),
    "operation_lines": (400, "INVALID_QUANTITY", "Quantity must be zero or more."),
    "stock_moves": (400, "INVALID_QUANTITY", "Quantity must be greater than zero."),
    "reorder_rules": (
        400,
        "INVALID_REORDER_RULE",
        "Minimum quantity must be between 0 and the maximum quantity.",
    ),
}
