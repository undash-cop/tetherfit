"""Phase 7: solo trainer CRM, geo start, business/GST fields

Revision ID: 0008_phase7
Revises: 0007_phase6
Create Date: 2026-07-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_phase7"
down_revision: Union[str, Sequence[str], None] = "0007_phase6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("pt_start_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("clients", sa.Column("pt_end_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("organizations", sa.Column("business_address", sa.Text(), nullable=True))
    op.add_column("organizations", sa.Column("business_phone", sa.String(length=32), nullable=True))
    op.add_column("organizations", sa.Column("upi_vpa", sa.String(length=128), nullable=True))
    op.add_column(
        "organizations",
        sa.Column("default_gst_pct", sa.Float(), nullable=False, server_default="0"),
    )

    op.add_column("pt_sessions", sa.Column("start_latitude", sa.Float(), nullable=True))
    op.add_column("pt_sessions", sa.Column("start_longitude", sa.Float(), nullable=True))
    op.add_column("pt_sessions", sa.Column("start_accuracy_m", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("pt_sessions", "start_accuracy_m")
    op.drop_column("pt_sessions", "start_longitude")
    op.drop_column("pt_sessions", "start_latitude")
    op.drop_column("organizations", "default_gst_pct")
    op.drop_column("organizations", "upi_vpa")
    op.drop_column("organizations", "business_phone")
    op.drop_column("organizations", "business_address")
    op.drop_column("clients", "pt_end_at")
    op.drop_column("clients", "pt_start_at")
