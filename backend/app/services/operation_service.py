"""The operations engine.

Every stock change is a move FROM one location TO another:
  receipt     Vendors (virtual)      -> internal location
  delivery    internal location      -> Customers (virtual)
  internal    internal location      -> internal location
  adjustment  Inventory Adjustment  <-> internal location (direction from the count)

validate() runs in ONE transaction: lock the stock rows, check there is enough,
update on-hand, write the ledger (stock_moves), mark the operation done.
If anything fails, nothing is saved.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.models import Location, Operation, OperationLine, Partner, Product, StockMove, StockQuant, User
from app.repositories import inventory_repository as inv
from app.repositories import operation_repository as ops

PREFIX = {"receipt": "IN", "delivery": "OUT", "internal": "INT", "adjustment": "ADJ"}
OPEN = ("draft", "waiting", "ready")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)  # stored as naive UTC


def _internal_location(db: Session, location_id: int | None, label: str) -> Location:
    loc = inv.get(db, Location, location_id) if location_id else None
    if loc is None or loc.type != "internal":
        raise AppError(400, "INVALID_LOCATION", f"Choose a valid warehouse location as {label}.")
    return loc


def _virtual(db: Session, type_: str) -> Location:
    loc = inv.virtual_location(db, type_)
    if loc is None:
        raise AppError(500, "SETUP_MISSING", f"The {type_} location is missing. Run the seed script.")
    return loc


def _next_reference(db: Session, type_: str, warehouse_code: str) -> str:
    return f"{warehouse_code}/{PREFIX[type_]}/{ops.count_by_type(db, type_) + 1:05d}"


# ---------------------------------------------------------------- create


def create_draft(db: Session, data, user: User) -> Operation:
    """Builds a draft operation (no commit)."""
    if data.type == "receipt":
        dst = _internal_location(db, data.dest_location_id, "destination")
        src = _virtual(db, "vendor")
    elif data.type == "delivery":
        src = _internal_location(db, data.source_location_id, "source")
        dst = _virtual(db, "customer")
    elif data.type == "internal":
        src = _internal_location(db, data.source_location_id, "source")
        dst = _internal_location(db, data.dest_location_id, "destination")
        if src.id == dst.id:
            raise AppError(400, "SAME_LOCATION", "Source and destination locations must be different.")
    else:  # adjustment
        dst = _internal_location(db, data.dest_location_id, "location")
        src = _virtual(db, "adjustment")

    if data.partner_id and inv.get(db, Partner, data.partner_id) is None:
        raise not_found("Partner")

    for line in data.lines:
        product = inv.get(db, Product, line.product_id)
        if product is None or not product.is_active:
            raise AppError(
                400, "INVALID_PRODUCT", f"Product {line.product_id} does not exist or is inactive."
            )

    warehouse = (dst if dst.warehouse else src).warehouse
    op = Operation(
        reference=_next_reference(db, data.type, warehouse.code),
        type=data.type,
        status="draft",
        partner_id=data.partner_id,
        source_location_id=src.id,
        dest_location_id=dst.id,
        scheduled_date=data.scheduled_date,
        created_by=user.id,
    )
    op.lines = [
        OperationLine(product_id=line.product_id, quantity=Decimal(str(line.quantity))) for line in data.lines
    ]
    return ops.add(db, op)


def create(db: Session, data, user: User) -> Operation:
    op = create_draft(db, data, user)
    db.commit()
    return op


# ---------------------------------------------------------------- state changes


def _get_open(db: Session, operation_id: int, lock: bool = False) -> Operation:
    op = ops.get_for_update(db, operation_id) if lock else ops.get(db, operation_id)
    if op is None:
        raise not_found("Operation")
    if op.status not in OPEN:
        raise AppError(409, "INVALID_STATE", f"This operation is already {op.status}.")
    return op


def _shortages(db: Session, op: Operation, lock: bool) -> list[str]:
    """Lines that don't have enough stock at the source location."""
    if op.type not in ("delivery", "internal"):
        return []
    problems = []
    for line in op.lines:
        if lock:
            quant = inv.quant_for_update(db, line.product_id, op.source_location_id)
            available = Decimal(quant.quantity) if quant else Decimal(0)
        else:
            available = Decimal(str(inv.quantity_at(db, line.product_id, op.source_location_id)))
        if Decimal(line.quantity) > available:
            product = inv.get(db, Product, line.product_id)
            problems.append(
                f"{product.name}: {float(available):g} available, {float(line.quantity):g} requested"
            )
    return problems


def confirm(db: Session, operation_id: int) -> Operation:
    op = _get_open(db, operation_id)
    if op.status != "draft":
        raise AppError(
            409, "INVALID_STATE", f"Only draft operations can be confirmed (this one is {op.status})."
        )
    op.status = "waiting" if _shortages(db, op, lock=False) else "ready"
    db.commit()
    return op


def _add_quantity(db: Session, product_id: int, location: Location, delta: Decimal) -> None:
    if location.type != "internal":
        return  # virtual locations (vendor/customer/adjustment) don't hold stock
    quant = inv.quant_for_update(db, product_id, location.id)
    if quant is None:
        quant = StockQuant(product_id=product_id, location_id=location.id, quantity=Decimal(0))
        db.add(quant)
    quant.quantity = Decimal(quant.quantity) + delta


def apply_validation(db: Session, op: Operation, user: User) -> None:
    """Moves the stock and writes the ledger (no commit)."""
    problems = _shortages(db, op, lock=True)
    if problems:
        raise AppError(409, "INSUFFICIENT_STOCK", "Not enough stock. " + "; ".join(problems) + ".")

    src = inv.get(db, Location, op.source_location_id)
    dst = inv.get(db, Location, op.dest_location_id)
    done_at = _now()

    for line in op.lines:
        qty = Decimal(line.quantity)
        move_from, move_to = src, dst

        if op.type == "adjustment":
            # The line holds the COUNTED quantity; move only the difference.
            on_hand = Decimal(str(inv.quantity_at(db, line.product_id, dst.id)))
            diff = qty - on_hand
            if diff == 0:
                continue
            qty = abs(diff)
            if diff < 0:
                move_from, move_to = dst, src  # stock leaves the shelf (damaged / lost)
        elif qty <= 0:
            raise AppError(400, "INVALID_QUANTITY", "Quantity must be greater than zero.")

        _add_quantity(db, line.product_id, move_from, -qty)
        _add_quantity(db, line.product_id, move_to, qty)
        ops.add_move(
            db,
            StockMove(
                operation_id=op.id,
                product_id=line.product_id,
                from_location_id=move_from.id,
                to_location_id=move_to.id,
                quantity=qty,
                done_by=user.id,
                done_at=done_at,
            ),
        )

    op.status = "done"
    op.validated_at = done_at
    db.flush()


def validate(db: Session, operation_id: int, user: User) -> Operation:
    op = _get_open(db, operation_id, lock=True)
    try:
        apply_validation(db, op, user)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return op


def cancel(db: Session, operation_id: int) -> Operation:
    op = ops.get(db, operation_id)
    if op is None:
        raise not_found("Operation")
    if op.status == "done":
        raise AppError(409, "INVALID_STATE", "A done operation can't be canceled.")
    if op.status == "canceled":
        raise AppError(409, "INVALID_STATE", "This operation is already canceled.")
    op.status = "canceled"
    db.commit()
    return op


# ---------------------------------------------------------------- output


def to_out(db: Session, op: Operation, with_lines: bool = True) -> dict:
    src = inv.get(db, Location, op.source_location_id)
    dst = inv.get(db, Location, op.dest_location_id)
    partner = inv.get(db, Partner, op.partner_id) if op.partner_id else None
    creator = inv.get(db, User, op.created_by)
    lines = []
    if with_lines:
        for line in op.lines:
            product = inv.get(db, Product, line.product_id)
            available = None
            if op.type in ("delivery", "internal"):
                available = inv.quantity_at(db, line.product_id, src.id)
            elif op.type == "adjustment":
                available = inv.quantity_at(db, line.product_id, dst.id)
            lines.append(
                {
                    "product_id": product.id,
                    "product": product.name,
                    "sku": product.sku,
                    "uom": product.uom.name,
                    "quantity": float(line.quantity),
                    "available": available,
                }
            )
    return {
        "id": op.id,
        "reference": op.reference,
        "type": op.type,
        "status": op.status,
        "partner": partner.name if partner else None,
        "source_location_id": src.id,
        "source_location": inv.location_name(src),
        "dest_location_id": dst.id,
        "dest_location": inv.location_name(dst),
        "scheduled_date": op.scheduled_date,
        "validated_at": op.validated_at,
        "created_by": creator.name if creator else "",
        "lines": lines,
    }
