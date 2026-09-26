from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StockQuant(Base):
    __tablename__ = "stock_quants"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), primary_key=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"), primary_key=True
    )
    quantity: Mapped[float] = mapped_column(
        Numeric(12, 3), nullable=False, default=0
    )


class StockMove(Base):
    __tablename__ = "stock_moves"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        Index("ix_stock_moves_product_id_done_at", "product_id", "done_at"),  # move history
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[int] = mapped_column(
        ForeignKey("operations.id"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )
    from_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"), nullable=False
    )
    to_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    done_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    done_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

