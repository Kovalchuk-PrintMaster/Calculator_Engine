import sqlalchemy as sa
from alembic import op

revision = "20251111_0003"
down_revision = "20251109_0001"  # materials уже існує з 0001
branch_labels = None
depends_on = None


def upgrade():
    # product_kinds
    op.create_table(
        "product_kinds",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("parent_id", sa.Integer, nullable=True),
        sa.Column("name_uk", sa.String(255), nullable=False),
        sa.Column("name_ru", sa.String(255), nullable=True),
        sa.Column("name_en", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("group_code", sa.Text, nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["product_kinds.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("code", name="uq_product_kinds_code"),
    )
    op.create_index("ix_product_kinds_parent", "product_kinds", ["parent_id"], unique=False)

    # product_kind_names
    op.create_table(
        "product_kind_names",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("product_kind_id", sa.BigInteger, nullable=False),
        sa.Column("lang", sa.String(8), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(["product_kind_id"], ["product_kinds.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "product_kind_id", "lang", name="product_kind_names_product_kind_id_lang_key"
        ),
    )

    # sizes
    op.create_table(
        "sizes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("kind_id", sa.Integer, nullable=True),
        sa.Column("width_mm", sa.Integer, nullable=False),
        sa.Column("height_mm", sa.Integer, nullable=False),
        sa.Column("label_uk", sa.String(255), nullable=False),
        sa.Column("label_ru", sa.String(255), nullable=True),
        sa.Column("label_en", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("code", sa.Text, nullable=True),
        sa.Column("name_uk", sa.Text, nullable=True),
        sa.Column("name_ru", sa.Text, nullable=True),
        sa.Column("name_en", sa.Text, nullable=True),
        sa.Column("is_vertical", sa.Boolean, nullable=True),
        sa.ForeignKeyConstraint(["kind_id"], ["product_kinds.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_sizes_kind", "sizes", ["kind_id"], unique=False)
    op.create_index("ix_sizes_dims", "sizes", ["width_mm", "height_mm"], unique=False)
    op.create_unique_constraint(
        "uq_sizes_label_dim", "sizes", ["label_uk", "width_mm", "height_mm"]
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_sizes_code ON sizes (code) WHERE code IS NOT NULL;"
    )
    op.execute(
        "ALTER TABLE sizes ADD CONSTRAINT ck_sizes_positive CHECK (width_mm > 0 AND height_mm > 0);"
    )

    # finishing_kinds
    op.create_table(
        "finishing_kinds",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name_uk", sa.String(255), nullable=False),
        sa.Column("name_ru", sa.String(255), nullable=True),
        sa.Column("name_en", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # finishing_options
    op.create_table(
        "finishing_options",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("kind_id", sa.Integer, nullable=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name_uk", sa.String(255), nullable=False),
        sa.Column("name_ru", sa.String(255), nullable=True),
        sa.Column("name_en", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["kind_id"], ["finishing_kinds.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_finishing_options_kind", "finishing_options", ["kind_id"], unique=False)
    op.create_unique_constraint("uq_finishing_options_code", "finishing_options", ["code"])

    # material_aliases
    op.create_table(
        "material_aliases",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("material_id", sa.Integer, nullable=False),
        sa.Column("alias", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("material_id", "alias", name="uq_material_alias"),
    )

    # сиди для finishing_kinds
    op.execute("""
        INSERT INTO finishing_kinds (code, name_uk, created_at, updated_at)
        VALUES ('lamination', 'Ламінування', now(), now()),
               ('uv',         'УФ-лак',      now(), now())
        ON CONFLICT (code) DO NOTHING;
    """)


def downgrade():
    op.drop_table("material_aliases")
    op.drop_index("ix_finishing_options_kind", table_name="finishing_options")
    op.drop_constraint("uq_finishing_options_code", "finishing_options", type_="unique")
    op.drop_table("finishing_options")
    op.drop_table("finishing_kinds")
    op.execute("DROP INDEX IF EXISTS ix_sizes_code;")
    op.drop_constraint("uq_sizes_label_dim", "sizes", type_="unique")
    op.drop_index("ix_sizes_dims", table_name="sizes")
    op.drop_index("ix_sizes_kind", table_name="sizes")
    op.drop_table("sizes")
    op.drop_table("product_kind_names")
    op.drop_index("ix_product_kinds_parent", table_name="product_kinds")
    op.drop_table("product_kinds")
