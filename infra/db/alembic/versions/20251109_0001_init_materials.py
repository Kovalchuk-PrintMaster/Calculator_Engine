"""init materials

Створює таблицю materials.

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# Ідентифікатори міграції
revision = "20251109_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("price_per_unit", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_materials_code", "materials", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_materials_code", table_name="materials")
    op.drop_table("materials")
