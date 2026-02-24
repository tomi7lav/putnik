from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MessageEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "message_events"
    __table_args__ = (
        Index("ix_message_events_provider_external", "provider", "external_event_id"),
        Index("ix_message_events_tenant_created", "tenant_id", "created_at"),
    )

    tenant_id: Mapped[Optional[UUID]] = mapped_column(Uuid, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    conversation_id: Mapped[Optional[UUID]] = mapped_column(
        Uuid,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    external_event_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant = relationship("Tenant")
    conversation = relationship("Conversation", back_populates="message_events")
