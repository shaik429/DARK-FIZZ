"""Starter data. Safe to run more than once.

Run from backend/:   python -m app.seed

NO stock is created here: stock only ever enters through operations,
so every unit on hand has a ledger row behind it.
"""

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Category, Location, Partner, Product, ReorderRule, Uom, User, Warehouse


def get_or_create(db, model, lookup: dict, **extra):
    obj = db.scalar(select(model).filter_by(**lookup))
    if obj is None:
        obj = model(**lookup, **extra)
        db.add(obj)
        db.flush()
    return obj


def seed(db) -> None:
    get_or_create(
        db,
        User,
        {"email": "manager@stocksense.com"},
        name="Inventory Manager",
        password_hash=hash_password("Manager@123"),
        role="manager",
    )
    get_or_create(
        db,
        User,
        {"email": "staff@stocksense.com"},
        name="Warehouse Staff",
        password_hash=hash_password("Staff@123"),
        role="staff",
    )

    main = get_or_create(db, Warehouse, {"code": "WH"}, name="Main Warehouse")
    second = get_or_create(db, Warehouse, {"code": "WH2"}, name="Second Warehouse")
    for wh, names in ((main, ("Stock", "Production Rack", "Rack A", "Rack B")), (second, ("Stock",))):
        for name in names:
            get_or_create(db, Location, {"warehouse_id": wh.id, "name": name}, type="internal")

    # Virtual locations: where stock comes from / goes to outside the warehouses
    for name, type_ in (
        ("Vendors", "vendor"),
        ("Customers", "customer"),
        ("Inventory Adjustment", "adjustment"),
    ):
        get_or_create(db, Location, {"name": name, "type": type_}, warehouse_id=None)

    cats = {n: get_or_create(db, Category, {"name": n}) for n in ("Raw Material", "Furniture", "Packaging")}
    uoms = {n: get_or_create(db, Uom, {"name": n}) for n in ("Units", "kg", "m")}

    get_or_create(db, Partner, {"name": "Tata Steel Ltd"}, type="supplier")
    get_or_create(db, Partner, {"name": "Hyderabad Timber Co"}, type="supplier")
    get_or_create(db, Partner, {"name": "Urban Furnish Pvt Ltd"}, type="customer")
    get_or_create(db, Partner, {"name": "OfficeHub Retail"}, type="customer")

    products = [
        ("STL-001", "Steel", "Raw Material", "kg"),
        ("STL-002", "Steel Rods", "Raw Material", "Units"),
        ("WOD-001", "Teak Wood Plank", "Raw Material", "m"),
        ("CHR-001", "Office Chair", "Furniture", "Units"),
        ("TBL-001", "Office Table", "Furniture", "Units"),
        ("FRM-001", "Steel Frame", "Furniture", "Units"),
        ("SCR-001", "Screws (box of 100)", "Raw Material", "Units"),
        ("BOX-001", "Cardboard Box", "Packaging", "Units"),
        ("WRP-001", "Bubble Wrap Roll", "Packaging", "m"),
        ("PNT-001", "Paint (1L)", "Raw Material", "Units"),
    ]
    by_sku = {}
    for sku, name, cat, uom in products:
        by_sku[sku] = get_or_create(
            db,
            Product,
            {"sku": sku},
            name=name,
            category_id=cats[cat].id,
            uom_id=uoms[uom].id,
            is_active=True,
        )

    # Reorder rules: Steel goes "low" after the demo flow (77 kg <= 80 kg minimum)
    get_or_create(
        db,
        ReorderRule,
        {"product_id": by_sku["STL-001"].id, "warehouse_id": main.id},
        min_qty=80,
        max_qty=200,
    )
    get_or_create(
        db, ReorderRule, {"product_id": by_sku["CHR-001"].id, "warehouse_id": main.id}, min_qty=10, max_qty=50
    )

    db.commit()


def run() -> None:
    db = SessionLocal()
    try:
        seed(db)
        print("Seed complete. Logins: manager@stocksense.com / Manager@123, staff@stocksense.com / Staff@123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
