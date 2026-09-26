from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Uom(Base):
    __tablename__ = "uoms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="uom")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    uom_id: Mapped[int] = mapped_column(ForeignKey("uoms.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    category: Mapped["Category"] = relationship(back_populates="products")
    uom: Mapped["Uom"] = relationship(back_populates="products")
    reorder_rules: Mapped[list["ReorderRule"]] = relationship(back_populates="product")


class ReorderRule(Base):
    __tablename__ = "reorder_rules"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "warehouse_id", name="uq_reorder_rules_product_id_warehouse_id"
        ),
        CheckConstraint(
            "min_qty >= 0 AND min_qty <= max_qty",
            name="min_qty_within_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    min_qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    max_qty: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="reorder_rules")