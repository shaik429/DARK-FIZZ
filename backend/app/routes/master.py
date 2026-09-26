"""Categories, units, warehouses, locations, partners and reorder rules."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_manager
from app.database import get_db
from app.models import Category
from app.repositories import inventory_repository as inv
from app.schemas.inventory import (
    IdName,
    LocationIn,
    LocationOut,
    NamedIn,
    PartnerOut,
    ReorderRuleIn,
    ReorderRuleOut,
    WarehouseIn,
    WarehouseOut,
)
from app.services import inventory_service

router = APIRouter(tags=["master data"], dependencies=[Depends(get_current_user)])


@router.get("/categories", response_model=list[IdName])
def categories(db: Session = Depends(get_db)):
    return inv.list_categories(db)


@router.post("/categories", response_model=IdName, status_code=201, dependencies=[Depends(require_manager)])
def create_category(body: NamedIn, db: Session = Depends(get_db)):
    category = inv.add(db, Category(name=body.name))
    db.commit()
    return category


@router.get("/uoms", response_model=list[IdName])
def uoms(db: Session = Depends(get_db)):
    return inv.list_uoms(db)


@router.get("/warehouses", response_model=list[WarehouseOut])
def warehouses(db: Session = Depends(get_db)):
    return inv.list_warehouses(db)


@router.post(
    "/warehouses", response_model=WarehouseOut, status_code=201, dependencies=[Depends(require_manager)]
)
def create_warehouse(body: WarehouseIn, db: Session = Depends(get_db)):
    return inventory_service.create_warehouse(db, body)


@router.get("/locations", response_model=list[LocationOut])
def locations(
    type: str | None = Query(default=None, pattern="^(internal|vendor|customer|adjustment)$"),
    warehouse_id: int | None = None,
    db: Session = Depends(get_db),
):
    return [inventory_service.location_out(loc) for loc in inv.list_locations(db, type, warehouse_id)]


@router.post(
    "/locations", response_model=LocationOut, status_code=201, dependencies=[Depends(require_manager)]
)
def create_location(body: LocationIn, db: Session = Depends(get_db)):
    return inventory_service.create_location(db, body)


@router.get("/partners", response_model=list[PartnerOut])
def partners(
    type: str | None = Query(default=None, pattern="^(supplier|customer)$"),
    db: Session = Depends(get_db),
):
    return inv.list_partners(db, type)


@router.get("/reorder-rules", response_model=list[ReorderRuleOut])
def reorder_rules(db: Session = Depends(get_db)):
    return [inventory_service.reorder_rule_out(r, p, w) for r, p, w in inv.list_reorder_rules(db)]


@router.put("/reorder-rules", response_model=ReorderRuleOut, dependencies=[Depends(require_manager)])
def upsert_reorder_rule(body: ReorderRuleIn, db: Session = Depends(get_db)):
    return inventory_service.upsert_reorder_rule(db, body)
