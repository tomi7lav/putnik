from uuid import UUID
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_tenant_external", "tenant_id", "external_thread_id", unique=True),
        Index("ix_conversations_tenant_contact", "tenant_id", "contact_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    contact_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="whatsapp", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    external_thread_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    tenant = relationship("Tenant", back_populates="conversations")
    contact = relationship("Contact", back_populates="conversations")
    message_events = relationship("MessageEvent", back_populates="conversation", cascade="all, delete-orphan")
    booking = relationship("Booking", back_populates="conversation", uselist=False, cascade="all, delete-orphan")
