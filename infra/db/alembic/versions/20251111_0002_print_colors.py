from alembic import op
import sqlalchemy as sa

revision = "20251111_0002"
down_revision = "20251111_0003"   # ВАЖЛИВО: спираємось на 0003, бо там product_kinds
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "print_color_schemes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("name_uk", sa.Text, nullable=False),
        sa.Column("name_ru", sa.Text, nullable=False),
        sa.Column("name_en", sa.Text, nullable=False),
        sa.Column("colors_front", sa.SmallInteger, nullable=False),
        sa.Column("colors_back", sa.SmallInteger, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_print_color_schemes_code", "print_color_schemes", ["code"], unique=True)

    op.create_table(
        "product_kind_print_colors",
        sa.Column("product_kind_id", sa.Integer, nullable=False),
        sa.Column("color_scheme_id", sa.BigInteger, nullable=False),
        sa.ForeignKeyConstraint(["product_kind_id"], ["product_kinds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["color_scheme_id"], ["print_color_schemes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("product_kind_id", "color_scheme_id"),
    )
    op.create_index("ix_product_kind_print_colors_kind", "product_kind_print_colors", ["product_kind_id"], unique=False)
    op.create_index("ix_product_kind_print_colors_scheme", "product_kind_print_colors", ["color_scheme_id"], unique=False)

    # сиди схем
    op.execute("""
        INSERT INTO print_color_schemes (code, name_uk, name_ru, name_en, colors_front, colors_back)
        VALUES
          ('0_0', 'Без друку',              'Без печати',              'No print',               0, 0),
          ('1_0', '1+0 (лиць 1 колір)',     '1+0 (лицо 1 цвет)',       '1+0 (front 1 color)',    1, 0),
          ('1_1', '1+1',                    '1+1',                     '1+1',                    1, 1),
          ('2_0', '2+0',                    '2+0',                     '2+0',                    2, 0),
          ('2_2', '2+2',                    '2+2',                     '2+2',                    2, 2),
          ('4_0', '4+0 (CMYK одност.)',     '4+0 (CMYK одност.)',      '4+0 (CMYK simplex)',     4, 0),
          ('4_4', '4+4 (CMYK двост.)',      '4+4 (CMYK двуст.)',       '4+4 (CMYK duplex)',      4, 4)
        ON CONFLICT (code) DO NOTHING;
    """)

    # опціональний сид зв'язків (тільки якщо коди існують)
    op.execute("""
        WITH kinds AS (
            SELECT id, code FROM product_kinds
            WHERE code IN ('business_cards','flyers','brochures','stickers','posters')
        ),
        schemes AS (
            SELECT id, code FROM print_color_schemes
        ),
        pairs AS (
            SELECT k.id AS product_kind_id, s.id AS color_scheme_id
            FROM kinds k JOIN schemes s ON s.code IN ('4_0','4_4','1_0','1_1')
            WHERE k.code = 'business_cards'
            UNION ALL
            SELECT k.id, s.id FROM kinds k JOIN schemes s ON s.code IN ('4_0','4_4') WHERE k.code = 'flyers'
            UNION ALL
            SELECT k.id, s.id FROM kinds k JOIN schemes s ON s.code IN ('4_4') WHERE k.code = 'brochures'
            UNION ALL
            SELECT k.id, s.id FROM kinds k JOIN schemes s ON s.code IN ('4_0','1_0') WHERE k.code = 'stickers'
            UNION ALL
            SELECT k.id, s.id FROM kinds k JOIN schemes s ON s.code IN ('4_0') WHERE k.code = 'posters'
        )
        INSERT INTO product_kind_print_colors(product_kind_id, color_scheme_id)
        SELECT DISTINCT product_kind_id, color_scheme_id FROM pairs
        ON CONFLICT DO NOTHING;
    """)

def downgrade():
    op.drop_index("ix_product_kind_print_colors_scheme", table_name="product_kind_print_colors")
    op.drop_index("ix_product_kind_print_colors_kind", table_name="product_kind_print_colors")
    op.drop_table("product_kind_print_colors")
    op.drop_index("ix_print_color_schemes_code", table_name="print_color_schemes")
    op.drop_table("print_color_schemes")
