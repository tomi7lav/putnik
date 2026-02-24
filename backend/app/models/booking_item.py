from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BookingItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "booking_items"
    __table_args__ = (Index("ix_booking_items_booking", "booking_id"),)

    tenant_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    booking_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(30), default="package", nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    quantity: Mapped[int] = mapped_column(default=1, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(nullable=False)
    total_price_cents: Mapped[int] = mapped_column(nullable=False)

    tenant = relationship("Tenant")
    booking = relationship("Booking", back_populates="items")
