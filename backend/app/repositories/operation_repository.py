"""Database queries for operations, lines, stock moves and dashboard counts."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models import Location, Operation, Product, StockMove, User

OPEN_STATUSES = ("draft", "waiting", "ready")


def get(db: Session, operation_id: int) -> Operation | None:
    return db.get(Operation, operation_id)


def get_for_update(db: Session, operation_id: int) -> Operation | None:
    return db.scalar(select(Operation).where(Operation.id == operation_id).with_for_update())


def add(db: Session, operation: Operation) -> Operation:
    db.add(operation)
    db.flush()
    return operation


def count_by_type(db: Session, type_: str) -> int:
    return db.scalar(select(func.count()).where(Operation.type == type_)) or 0


def list_operations(
    db: Session,
    type_: str | None = None,
    status: str | None = None,
    warehouse_id: int | None = None,
    limit: int = 200,
):
    q = select(Operation).order_by(Operation.id.desc()).limit(limit)
    if type_:
        q = q.where(Operation.type == type_)
    if status:
        q = q.where(Operation.status == status)
    if warehouse_id:
        src, dst = aliased(Location), aliased(Location)
        q = (
            q.join(src, src.id == Operation.source_location_id)
            .join(dst, dst.id == Operation.dest_location_id)
            .where(or_(src.warehouse_id == warehouse_id, dst.warehouse_id == warehouse_id))
        )
    return db.scalars(q).all()


def add_move(db: Session, move: StockMove) -> None:
    db.add(move)


def list_moves(db: Session, product_id: int | None = None, limit: int = 100, offset: int = 0):
    src, dst = aliased(Location), aliased(Location)
    q = (
        select(StockMove, Operation, Product, src, dst, User.name)
        .join(Operation, Operation.id == StockMove.operation_id)
        .join(Product, Product.id == StockMove.product_id)
        .join(src, src.id == StockMove.from_location_id)
        .join(dst, dst.id == StockMove.to_location_id)
        .join(User, User.id == StockMove.done_by)
        .order_by(StockMove.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if product_id:
        q = q.where(StockMove.product_id == product_id)
    return db.execute(q).all()


def count_open(db: Session, type_: str, warehouse_id: int | None = None) -> int:
    q = select(func.count(Operation.id)).where(Operation.type == type_, Operation.status.in_(OPEN_STATUSES))
    if warehouse_id:
        src, dst = aliased(Location), aliased(Location)
        q = (
            q.join(src, src.id == Operation.source_location_id)
            .join(dst, dst.id == Operation.dest_location_id)
            .where(or_(src.warehouse_id == warehouse_id, dst.warehouse_id == warehouse_id))
        )
    return db.scalar(q) or 0
