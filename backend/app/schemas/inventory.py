from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class NamedIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty.")
        return v.strip()


class IdName(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


# ---- warehouses & locations -------------------------------------------------


class WarehouseIn(NamedIn):
    code: str = Field(min_length=1, max_length=10, pattern=r"^[A-Za-z0-9]+$")


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str


class LocationIn(NamedIn):
    warehouse_id: int


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: str
    warehouse_id: int | None
    full_name: str


class PartnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: str


# ---- products ---------------------------------------------------------------


class ProductIn(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    category_id: int
    uom_id: int
    initial_qty: float | None = Field(default=None, ge=0)
    initial_location_id: int | None = None

    @field_validator("sku", "name")
    @classmethod
    def strip(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Cannot be empty.")
        return v.strip()

    @model_validator(mode="after")
    def location_needed_for_stock(self):
        if self.initial_qty and not self.initial_location_id:
            raise ValueError("Choose a location for the initial stock.")
        return self


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    category_id: int | None = None
    uom_id: int | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    category_id: int
    uom: str
    uom_id: int
    is_active: bool
    on_hand: float
    min_qty: float | None
    max_qty: float | None
    stock_status: Literal["ok", "low", "out"]


class StockLine(BaseModel):
    location_id: int
    location: str
    quantity: float


class ReorderRuleIn(BaseModel):
    product_id: int
    warehouse_id: int
    min_qty: float = Field(ge=0)
    max_qty: float = Field(ge=0)

    @model_validator(mode="after")
    def min_below_max(self):
        if self.min_qty > self.max_qty:
            raise ValueError("Minimum quantity cannot be greater than maximum quantity.")
        return self


class ReorderRuleOut(BaseModel):
    id: int
    product_id: int
    product: str
    warehouse_id: int
    warehouse: str
    min_qty: float
    max_qty: float


# ---- operations -------------------------------------------------------------

OperationType = Literal["receipt", "delivery", "internal", "adjustment"]
OperationStatus = Literal["draft", "waiting", "ready", "done", "canceled"]


class LineIn(BaseModel):
    product_id: int
    quantity: float = Field(ge=0)


class OperationIn(BaseModel):
    type: OperationType
    partner_id: int | None = None
    source_location_id: int | None = None
    dest_location_id: int | None = None
    scheduled_date: datetime | None = None
    lines: list[LineIn] = Field(min_length=1)

    @model_validator(mode="after")
    def check_shape(self):
        ids = [line.product_id for line in self.lines]
        if len(ids) != len(set(ids)):
            raise ValueError("Each product can appear only once per operation.")
        if self.type != "adjustment" and any(line.quantity <= 0 for line in self.lines):
            raise ValueError("Quantity must be greater than zero.")
        if self.type in ("receipt", "adjustment") and not self.dest_location_id:
            raise ValueError("Choose the destination location.")
        if self.type in ("delivery", "internal") and not self.source_location_id:
            raise ValueError("Choose the source location.")
        if self.type == "internal" and not self.dest_location_id:
            raise ValueError("Choose the destination location.")
        return self


class LineOut(BaseModel):
    product_id: int
    product: str
    sku: str
    uom: str
    quantity: float
    available: float | None = None


class OperationOut(BaseModel):
    id: int
    reference: str
    type: str
    status: str
    partner: str | None
    source_location_id: int
    source_location: str
    dest_location_id: int
    dest_location: str
    scheduled_date: datetime | None
    validated_at: datetime | None
    created_by: str
    lines: list[LineOut] = []


class MoveOut(BaseModel):
    id: int
    done_at: datetime
    reference: str
    type: str
    product: str
    sku: str
    from_location: str
    to_location: str
    quantity: float
    done_by: str


class KpisOut(BaseModel):
    total_products_in_stock: int
    low_stock: int
    out_of_stock: int
    pending_receipts: int
    pending_deliveries: int
    internal_scheduled: int


class LowStockOut(BaseModel):
    product_id: int
    sku: str
    product: str
    on_hand: float
    min_qty: float
    max_qty: float
    suggested_order_qty: float
