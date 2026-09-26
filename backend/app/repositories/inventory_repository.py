"""Database queries for master data, products and stock. No business rules here."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Category,
    Location,
    Partner,
    Product,
    ReorderRule,
    StockQuant,
    Uom,
    Warehouse,
)

# ---- master data ------------------------------------------------------------


def list_categories(db: Session):
    return db.scalars(select(Category).order_by(Category.name)).all()


def list_uoms(db: Session):
    return db.scalars(select(Uom).order_by(Uom.name)).all()


def list_warehouses(db: Session):
    return db.scalars(select(Warehouse).order_by(Warehouse.id)).all()


def list_partners(db: Session, type_: str | None = None):
    q = select(Partner).order_by(Partner.name)
    if type_:
        q = q.where(Partner.type == type_)
    return db.scalars(q).all()


def list_locations(db: Session, type_: str | None = None, warehouse_id: int | None = None):
    q = select(Location).order_by(Location.warehouse_id, Location.id)
    if type_:
        q = q.where(Location.type == type_)
    if warehouse_id:
        q = q.where(Location.warehouse_id == warehouse_id)
    return db.scalars(q).all()


def virtual_location(db: Session, type_: str) -> Location | None:
    return db.scalar(select(Location).where(Location.type == type_).limit(1))


def location_name(loc: Location) -> str:
    return f"{loc.warehouse.code}/{loc.name}" if loc.warehouse else loc.name


def add(db: Session, obj):
    db.add(obj)
    db.flush()
    return obj


def get(db: Session, model, obj_id: int):
    return db.get(model, obj_id)


# ---- products ---------------------------------------------------------------


def sku_exists(db: Session, sku: str) -> bool:
    return db.scalar(select(func.count()).where(Product.sku == sku)) > 0


def like_pattern(value: str) -> str:
    return f"%{value.strip()}%"


def on_hand_subquery(warehouse_id: int | None = None):
    """Total quantity per product across INTERNAL locations (optionally one warehouse)."""
    q = (
        select(StockQuant.product_id, func.sum(StockQuant.quantity).label("on_hand"))
        .join(Location, Location.id == StockQuant.location_id)
        .where(Location.type == "internal")
        .group_by(StockQuant.product_id)
    )
    if warehouse_id:
        q = q.where(Location.warehouse_id == warehouse_id)
    return q.subquery()


def rules_subquery():
    return (
        select(
            ReorderRule.product_id,
            func.sum(ReorderRule.min_qty).label("min_qty"),
            func.sum(ReorderRule.max_qty).label("max_qty"),
        )
        .group_by(ReorderRule.product_id)
        .subquery()
    )


def list_products(
    db: Session,
    q: str | None = None,
    category_id: int | None = None,
    warehouse_id: int | None = None,
):
    oh = on_hand_subquery(warehouse_id)
    rr = rules_subquery()
    stmt = (
        select(
            Product,
            Category.name,
            Uom.name,
            func.coalesce(oh.c.on_hand, 0),
            rr.c.min_qty,
            rr.c.max_qty,
        )
        .join(Category, Category.id == Product.category_id)
        .join(Uom, Uom.id == Product.uom_id)
        .outerjoin(oh, oh.c.product_id == Product.id)
        .outerjoin(rr, rr.c.product_id == Product.id)
        .order_by(Product.sku)
    )
    if q:
        stmt = stmt.where(or_(Product.sku.ilike(like_pattern(q)), Product.name.ilike(like_pattern(q))))
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    return db.execute(stmt).all()


def stock_by_location(db: Session, product_id: int):
    stmt = (
        select(Location, StockQuant.quantity)
        .join(StockQuant, StockQuant.location_id == Location.id)
        .where(StockQuant.product_id == product_id, Location.type == "internal")
        .order_by(Location.id)
    )
    return db.execute(stmt).all()


def quant_for_update(db: Session, product_id: int, location_id: int) -> StockQuant | None:
    """Row-locks the quant (SELECT ... FOR UPDATE) so two validations can't race."""
    return db.scalar(
        select(StockQuant)
        .where(StockQuant.product_id == product_id, StockQuant.location_id == location_id)
        .with_for_update()
    )


def quantity_at(db: Session, product_id: int, location_id: int) -> float:
    qty = db.scalar(
        select(StockQuant.quantity).where(
            StockQuant.product_id == product_id, StockQuant.location_id == location_id
        )
    )
    return float(qty or 0)


def list_reorder_rules(db: Session):
    stmt = (
        select(ReorderRule, Product.name, Warehouse.name)
        .join(Product, Product.id == ReorderRule.product_id)
        .join(Warehouse, Warehouse.id == ReorderRule.warehouse_id)
        .order_by(Product.name)
    )
    return db.execute(stmt).all()


def find_reorder_rule(db: Session, product_id: int, warehouse_id: int) -> ReorderRule | None:
    return db.scalar(
        select(ReorderRule).where(
            ReorderRule.product_id == product_id, ReorderRule.warehouse_id == warehouse_id
        )
    )
