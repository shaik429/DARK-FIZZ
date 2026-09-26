"""Rules for master data, products, stock and reorder rules."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.models import Category, Location, Product, ReorderRule, Uom, User, Warehouse
from app.repositories import inventory_repository as inv
from app.schemas.inventory import LineIn, OperationIn
from app.services import operation_service


def stock_status(on_hand: float, min_qty: float | None) -> str:
    if on_hand <= 0:
        return "out"
    if min_qty is not None and on_hand <= min_qty:
        return "low"
    return "ok"


def product_rows(db: Session, q=None, category_id=None, warehouse_id=None) -> list[dict]:
    rows = inv.list_products(db, q=q, category_id=category_id, warehouse_id=warehouse_id)
    out = []
    for product, category, uom, on_hand, min_qty, max_qty in rows:
        on_hand = float(on_hand or 0)
        min_qty = float(min_qty) if min_qty is not None else None
        out.append(
            {
                "id": product.id,
                "sku": product.sku,
                "name": product.name,
                "category": category,
                "category_id": product.category_id,
                "uom": uom,
                "uom_id": product.uom_id,
                "is_active": product.is_active,
                "on_hand": on_hand,
                "min_qty": min_qty,
                "max_qty": float(max_qty) if max_qty is not None else None,
                "stock_status": stock_status(on_hand, min_qty),
            }
        )
    return out


def get_product_row(db: Session, product_id: int) -> dict:
    product = inv.get(db, Product, product_id)
    if product is None:
        raise not_found("Product")
    return next(r for r in product_rows(db, q=product.sku) if r["id"] == product_id)


def _check_refs(db: Session, category_id: int | None, uom_id: int | None) -> None:
    if category_id is not None and inv.get(db, Category, category_id) is None:
        raise AppError(400, "INVALID_REFERENCE", "The chosen category does not exist.")
    if uom_id is not None and inv.get(db, Uom, uom_id) is None:
        raise AppError(400, "INVALID_REFERENCE", "The chosen unit of measure does not exist.")


def create_product(db: Session, data, user: User) -> dict:
    sku = data.sku.upper()
    if inv.sku_exists(db, sku):
        raise AppError(409, "DUPLICATE_SKU", "A product with this SKU already exists.")
    _check_refs(db, data.category_id, data.uom_id)

    product = inv.add(
        db, Product(sku=sku, name=data.name, category_id=data.category_id, uom_id=data.uom_id, is_active=True)
    )

    # Initial stock goes through an adjustment, so it appears in the ledger.
    if data.initial_qty:
        op = operation_service.create_draft(
            db,
            OperationIn(
                type="adjustment",
                dest_location_id=data.initial_location_id,
                lines=[LineIn(product_id=product.id, quantity=data.initial_qty)],
            ),
            user,
        )
        operation_service.apply_validation(db, op, user)

    db.commit()
    return get_product_row(db, product.id)


def update_product(db: Session, product_id: int, data) -> dict:
    product = inv.get(db, Product, product_id)
    if product is None:
        raise not_found("Product")
    _check_refs(db, data.category_id, data.uom_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(product, field, value)
    db.commit()
    return get_product_row(db, product_id)


def product_stock(db: Session, product_id: int) -> list[dict]:
    if inv.get(db, Product, product_id) is None:
        raise not_found("Product")
    return [
        {"location_id": loc.id, "location": inv.location_name(loc), "quantity": float(qty)}
        for loc, qty in inv.stock_by_location(db, product_id)
    ]


def location_out(loc: Location) -> dict:
    return {
        "id": loc.id,
        "name": loc.name,
        "type": loc.type,
        "warehouse_id": loc.warehouse_id,
        "full_name": inv.location_name(loc),
    }


def create_warehouse(db: Session, data) -> Warehouse:
    warehouse = inv.add(db, Warehouse(name=data.name, code=data.code.upper()))
    inv.add(db, Location(warehouse_id=warehouse.id, name="Stock", type="internal"))
    db.commit()
    return warehouse


def create_location(db: Session, data) -> dict:
    if inv.get(db, Warehouse, data.warehouse_id) is None:
        raise not_found("Warehouse")
    loc = inv.add(db, Location(warehouse_id=data.warehouse_id, name=data.name, type="internal"))
    db.commit()
    return location_out(loc)


def reorder_rule_out(rule: ReorderRule, product: str, warehouse: str) -> dict:
    return {
        "id": rule.id,
        "product_id": rule.product_id,
        "product": product,
        "warehouse_id": rule.warehouse_id,
        "warehouse": warehouse,
        "min_qty": float(rule.min_qty),
        "max_qty": float(rule.max_qty),
    }


def upsert_reorder_rule(db: Session, data) -> dict:
    product = inv.get(db, Product, data.product_id)
    warehouse = inv.get(db, Warehouse, data.warehouse_id)
    if product is None:
        raise not_found("Product")
    if warehouse is None:
        raise not_found("Warehouse")
    rule = inv.find_reorder_rule(db, data.product_id, data.warehouse_id)
    if rule is None:
        rule = inv.add(
            db, ReorderRule(product_id=product.id, warehouse_id=warehouse.id, min_qty=0, max_qty=0)
        )
    rule.min_qty = Decimal(str(data.min_qty))
    rule.max_qty = Decimal(str(data.max_qty))
    db.commit()
    return reorder_rule_out(rule, product.name, warehouse.name)
