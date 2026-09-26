from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.schemas.inventory import KpisOut, LowStockOut
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/kpis", response_model=KpisOut)
def kpis(warehouse_id: int | None = None, category_id: int | None = None, db: Session = Depends(get_db)):
    return dashboard_service.kpis(db, warehouse_id, category_id)


@router.get("/low-stock", response_model=list[LowStockOut])
def low_stock(warehouse_id: int | None = None, db: Session = Depends(get_db)):
    return dashboard_service.low_stock(db, warehouse_id)
