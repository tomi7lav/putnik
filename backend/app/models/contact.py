from uuid import UUID
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Contact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "contacts"
    __table_args__ = (Index("ix_contacts_tenant_phone", "tenant_id", "phone_number", unique=True),)

    tenant_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    wa_contact_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    tenant = relationship("Tenant", back_populates="contacts")
    conversations = relationship("Conversation", back_populates="contact", cascade="all, delete-orphan")
