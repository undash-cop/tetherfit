"""Phase 6: session pause timestamp

Revision ID: 0007_phase6
Revises: 0006_phase5
Create Date: 2026-07-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_phase6"
down_revision: Union[str, Sequence[str], None] = "0006_phase5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pt_sessions",
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pt_sessions", "paused_at")
