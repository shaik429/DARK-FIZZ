from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_manager
from app.database import get_db
from app.models import User
from app.schemas.inventory import ProductIn, ProductOut, ProductUpdate, StockLine
from app.services import inventory_service

router = APIRouter(prefix="/products", tags=["products"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ProductOut])
def list_products(
    q: str | None = Query(default=None, max_length=100, description="Search SKU or name"),
    category_id: int | None = None,
    db: Session = Depends(get_db),
):
    return inventory_service.product_rows(db, q=q, category_id=category_id)


@router.post("", response_model=ProductOut, status_code=201)
def create_product(body: ProductIn, user: User = Depends(require_manager), db: Session = Depends(get_db)):
    return inventory_service.create_product(db, body, user)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return inventory_service.get_product_row(db, product_id)


@router.put("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_manager)])
def update_product(product_id: int, body: ProductUpdate, db: Session = Depends(get_db)):
    return inventory_service.update_product(db, product_id, body)


@router.get("/{product_id}/stock", response_model=list[StockLine])
def product_stock(product_id: int, db: Session = Depends(get_db)):
    return inventory_service.product_stock(db, product_id)
