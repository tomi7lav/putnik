"""add tenant whatsapp phone number mapping

Revision ID: 20260224_0003
Revises: 20260224_0002
Create Date: 2026-02-24 00:30:00.000000
"""

from collections.abc import Sequence
from typing import Optional

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260224_0003"
down_revision: Optional[str] = "20260224_0002"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("whatsapp_phone_number_id", sa.String(length=64), nullable=True))
    op.create_unique_constraint(
        "uq_tenants_whatsapp_phone_number_id",
        "tenants",
        ["whatsapp_phone_number_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_tenants_whatsapp_phone_number_id", "tenants", type_="unique")
    op.drop_column("tenants", "whatsapp_phone_number_id")
