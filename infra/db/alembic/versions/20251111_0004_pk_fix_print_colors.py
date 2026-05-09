import sqlalchemy as sa
from alembic import op

revision = "20251111_0004"
down_revision = "20251111_0002"
branch_labels = None
depends_on = None


def upgrade():
    # зняти композитний PK
    op.execute(
        "ALTER TABLE product_kind_print_colors DROP CONSTRAINT product_kind_print_colors_pkey;"
    )
    # додати id та required
    op.add_column(
        "product_kind_print_colors",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
    )
    op.add_column(
        "product_kind_print_colors",
        sa.Column("required", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
    )
    # забезпечити унікальність пари
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_product_kind_print_colors_pair
        ON product_kind_print_colors(product_kind_id, color_scheme_id);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_product_kind_print_colors_pair;")
    op.drop_column("product_kind_print_colors", "required")
    op.drop_column("product_kind_print_colors", "id")
    op.execute("""
        ALTER TABLE product_kind_print_colors
        ADD PRIMARY KEY (product_kind_id, color_scheme_id);
    """)
