from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BookingCreateRequest(BaseModel):
    conversation_id: UUID
    title: Optional[str] = Field(default=None, max_length=140)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class BookingItemCreateRequest(BaseModel):
    item_type: str = Field(default="package", min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=140)
    quantity: int = Field(default=1, ge=1, le=100)
    unit_price_cents: int = Field(ge=0)


class BookingItemResponse(BaseModel):
    id: UUID
    item_type: str
    name: str
    quantity: int
    unit_price_cents: int
    total_price_cents: int
    created_at: datetime


class BookingResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    contact_id: UUID
    title: Optional[str] = None
    status: str
    currency: str
    subtotal_cents: int
    total_cents: int
    created_at: datetime
    updated_at: datetime
    items: List[BookingItemResponse] = Field(default_factory=list)
