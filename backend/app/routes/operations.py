from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.repositories import operation_repository as ops
from app.repositories.inventory_repository import location_name
from app.schemas.inventory import MoveOut, OperationIn, OperationOut
from app.services import operation_service as svc

router = APIRouter(tags=["operations"], dependencies=[Depends(get_current_user)])

TYPE = "^(receipt|delivery|internal|adjustment)$"
STATUS = "^(draft|waiting|ready|done|canceled)$"


@router.get("/operations", response_model=list[OperationOut])
def list_operations(
    type: str | None = Query(default=None, pattern=TYPE),
    status: str | None = Query(default=None, pattern=STATUS),
    warehouse_id: int | None = None,
    db: Session = Depends(get_db),
):
    return [
        svc.to_out(db, op, with_lines=False) for op in ops.list_operations(db, type, status, warehouse_id)
    ]


@router.post("/operations", response_model=OperationOut, status_code=201)
def create_operation(
    body: OperationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return svc.to_out(db, svc.create(db, body, user))


@router.get("/operations/{operation_id}", response_model=OperationOut)
def get_operation(operation_id: int, db: Session = Depends(get_db)):
    op = ops.get(db, operation_id)
    if op is None:
        raise not_found("Operation")
    return svc.to_out(db, op)


@router.post("/operations/{operation_id}/confirm", response_model=OperationOut)
def confirm(operation_id: int, db: Session = Depends(get_db)):
    return svc.to_out(db, svc.confirm(db, operation_id))


@router.post("/operations/{operation_id}/validate", response_model=OperationOut)
def validate(operation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.to_out(db, svc.validate(db, operation_id, user))


@router.post("/operations/{operation_id}/cancel", response_model=OperationOut)
def cancel(operation_id: int, db: Session = Depends(get_db)):
    return svc.to_out(db, svc.cancel(db, operation_id))


@router.get("/moves", response_model=list[MoveOut])
def moves(
    product_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return [
        {
            "id": m.id,
            "done_at": m.done_at,
            "reference": op.reference,
            "type": op.type,
            "product": p.name,
            "sku": p.sku,
            "from_location": location_name(src),
            "to_location": location_name(dst),
            "quantity": float(m.quantity),
            "done_by": who,
        }
        for m, op, p, src, dst, who in ops.list_moves(db, product_id, limit, offset)
    ]
