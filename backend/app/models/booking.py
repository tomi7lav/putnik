from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Booking(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_tenant_status", "tenant_id", "status"),
        Index("ix_bookings_conversation_unique", "conversation_id", unique=True),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    contact_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(140), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal_cents: Mapped[int] = mapped_column(default=0, nullable=False)
    total_cents: Mapped[int] = mapped_column(default=0, nullable=False)

    tenant = relationship("Tenant")
    conversation = relationship("Conversation", back_populates="booking")
    contact = relationship("Contact")
    items = relationship("BookingItem", back_populates="booking", cascade="all, delete-orphan")
