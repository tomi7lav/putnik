"""add contacts conversations and message events

Revision ID: 20260224_0002
Revises: 20260224_0001
Create Date: 2026-02-24 00:15:00.000000
"""

from collections.abc import Sequence
from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260224_0002"
down_revision: Optional[str] = "20260224_0001"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("wa_contact_id", sa.String(length=64), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_tenant_phone", "contacts", ["tenant_id", "phone_number"], unique=True)

    op.create_table(
        "conversations",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("external_thread_id", sa.String(length=128), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_tenant_contact", "conversations", ["tenant_id", "contact_id"], unique=False)
    op.create_index("ix_conversations_tenant_external", "conversations", ["tenant_id", "external_thread_id"], unique=True)

    op.create_table(
        "message_events",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("external_event_id", sa.String(length=120), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_message_events_provider_external", "message_events", ["provider", "external_event_id"], unique=False)
    op.create_index("ix_message_events_tenant_created", "message_events", ["tenant_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_message_events_tenant_created", table_name="message_events")
    op.drop_index("ix_message_events_provider_external", table_name="message_events")
    op.drop_table("message_events")
    op.drop_index("ix_conversations_tenant_external", table_name="conversations")
    op.drop_index("ix_conversations_tenant_contact", table_name="conversations")
    op.drop_table("conversations")
    op.drop_index("ix_contacts_tenant_phone", table_name="contacts")
    op.drop_table("contacts")
