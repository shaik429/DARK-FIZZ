from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Operation(Base):
    __tablename__ = "operations"
    __table_args__ = (
        CheckConstraint(
            "source_location_id <> dest_location_id",
            name="source_dest_different",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("receipt", "delivery", "internal", "adjustment", name="operation_type"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("draft", "waiting", "ready", "done", "canceled", name="operation_status"),
        nullable=False,
        default="draft",
    )
    partner_id: Mapped[int | None] = mapped_column(ForeignKey("partners.id"), nullable=True)
    source_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"), nullable=False
    )
    dest_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"), nullable=False
    )
    scheduled_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    lines: Mapped[list["OperationLine"]] = relationship(
        back_populates="operation", cascade="all, delete-orphan"
    )


class OperationLine(Base):
    __tablename__ = "operation_lines"
    __table_args__ = (
        UniqueConstraint(
            "operation_id", "product_id", name="uq_operation_lines_operation_id_product_id"
        ),
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[int] = mapped_column(
        ForeignKey("operations.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)

    operation: Mapped["Operation"] = relationship(back_populates="lines")