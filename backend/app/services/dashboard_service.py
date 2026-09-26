"""Dashboard numbers. Stock totals come from SQL aggregates (see inventory_repository)."""

from sqlalchemy.orm import Session

from app.repositories import operation_repository as ops
from app.services.inventory_service import product_rows


def kpis(db: Session, warehouse_id: int | None = None, category_id: int | None = None) -> dict:
    rows = [r for r in product_rows(db, category_id=category_id, warehouse_id=warehouse_id) if r["is_active"]]
    return {
        "total_products_in_stock": sum(1 for r in rows if r["on_hand"] > 0),
        "low_stock": sum(1 for r in rows if r["stock_status"] == "low"),
        "out_of_stock": sum(1 for r in rows if r["stock_status"] == "out"),
        "pending_receipts": ops.count_open(db, "receipt", warehouse_id),
        "pending_deliveries": ops.count_open(db, "delivery", warehouse_id),
        "internal_scheduled": ops.count_open(db, "internal", warehouse_id),
    }


def low_stock(db: Session, warehouse_id: int | None = None) -> list[dict]:
    """Products at or below their reorder minimum, with how much to order."""
    out = []
    for r in product_rows(db, warehouse_id=warehouse_id):
        if r["min_qty"] is None or r["on_hand"] > r["min_qty"]:
            continue
        out.append(
            {
                "product_id": r["id"],
                "sku": r["sku"],
                "product": r["name"],
                "on_hand": r["on_hand"],
                "min_qty": r["min_qty"],
                "max_qty": r["max_qty"],
                "suggested_order_qty": max(r["max_qty"] - r["on_hand"], 0),
            }
        )
    return out
