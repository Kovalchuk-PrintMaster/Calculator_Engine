from alembic import op

revision = "20251111_0005"
down_revision = "20251111_0003"
branch_labels = None
depends_on = None


def upgrade():
    # --- print_color_schemes ---
    op.execute("""
    INSERT INTO print_color_schemes(code, name_uk, name_ru, name_en, colors_front, colors_back)
    VALUES
      ('0_0','Без друку','Без печати','No print',0,0),
      ('1_0','1+0 (лиць 1 колір)','1+0 (лицо 1 цвет)','1+0 (front 1 color)',1,0),
      ('1_1','1+1','1+1','1+1',1,1),
      ('2_0','2+0','2+0','2+0',2,0),
      ('2_2','2+2','2+2','2+2',2,2),
      ('4_0','4+0 (CMYK одност.)','4+0 (CMYK одност.)','4+0 (CMYK simplex)',4,0),
      ('4_4','4+4 (CMYK двост.)','4+4 (CMYK двуст.)','4+4 (CMYK duplex)',4,4)
    ON CONFLICT (code) DO NOTHING;
    """)

    # --- finishing_kinds / finishing_options (базові) ---
    op.execute("""
    INSERT INTO finishing_kinds(code, name_uk) VALUES
      ('lamination','Ламінування'),
      ('uv','УФ-лак')
    ON CONFLICT (code) DO NOTHING;
    """)

    op.execute("""
    WITH kinds AS (
      SELECT id, code FROM finishing_kinds
    )
    INSERT INTO finishing_options(kind_id, code, name_uk, created_at, updated_at)
    SELECT k.id, v.code, v.name_uk, now(), now()
    FROM (VALUES
      ('lamination','lam_gloss','Ламінування глянець'),
      ('lamination','lam_matte','Ламінування матове'),
      ('uv','uv_spot','УФ-лак вибірковий')
    ) AS v(kind_code, code, name_uk)
    JOIN kinds k ON k.code = v.kind_code
    ON CONFLICT (code) DO NOTHING;
    """)

    # --- product_kinds (мінімальний набір) ---
    op.execute("""
    INSERT INTO product_kinds(code, name_uk, name_ru, name_en, created_at, updated_at, group_code)
    VALUES
      ('business_cards','Візитки','Визитки','Business cards', now(), now(), 'print/smb'),
      ('flyers','Флаєри','Флаеры','Flyers', now(), now(), 'print/promo'),
      ('brochures','Брошури','Брошюры','Brochures', now(), now(), 'print/promo'),
      ('stickers','Наліпки','Наклейки','Stickers', now(), now(), 'print/sign'),
      ('posters','Постери','Плакаты','Posters', now(), now(), 'print/large')
    ON CONFLICT (code) DO NOTHING;
    """)

    # локалізовані назви (опційно)
    op.execute("""
    WITH pk AS (SELECT id, code FROM product_kinds)
    INSERT INTO product_kind_names(product_kind_id, lang, name)
    SELECT pk.id, v.lang, v.name
    FROM (VALUES
      ('business_cards','uk','Візитки'),
      ('business_cards','ru','Визитки'),
      ('business_cards','en','Business cards'),
      ('flyers','uk','Флаєри'),
      ('flyers','ru','Флаеры'),
      ('flyers','en','Flyers'),
      ('brochures','uk','Брошури'),
      ('brochures','ru','Брошюры'),
      ('brochures','en','Brochures'),
      ('stickers','uk','Наліпки'),
      ('stickers','ru','Наклейки'),
      ('stickers','en','Stickers'),
      ('posters','uk','Постери'),
      ('posters','ru','Плакаты'),
      ('posters','en','Posters')
    ) AS v(code, lang, name)
    JOIN pk ON pk.code = v.code
    ON CONFLICT (product_kind_id, lang) DO NOTHING;
    """)

    # --- sizes (по одному-два типові розміри) ---
    op.execute("""
    WITH pk AS (SELECT id, code FROM product_kinds)
    INSERT INTO sizes(kind_id, width_mm, height_mm, label_uk, label_ru, label_en,
                      created_at, updated_at, code, name_uk, name_ru, name_en, is_vertical)
    SELECT pk.id, v.w, v.h, v.label_uk, v.label_ru, v.label_en,
           now(), now(), v.code, v.name_uk, v.name_ru, v.name_en, v.is_vertical
    FROM (VALUES
      -- візитка 90x50
      ('business_cards', 90, 50, '90×50 мм', '90×50 мм', '90×50 mm', 'bc_90x50',
         '90×50 мм', '90×50 мм', '90×50 mm', TRUE),
      -- флаєр A6 105x148
      ('flyers', 105, 148, 'A6 (105×148 мм)', 'A6 (105×148 мм)', 'A6 (105×148 mm)', 'fly_a6',
         'A6', 'A6', 'A6', TRUE),
      -- постер A3 297x420
      ('posters', 297, 420, 'A3 (297×420 мм)', 'A3 (297×420 мм)', 'A3 (297×420 mm)', 'pos_a3',
         'A3', 'A3', 'A3', TRUE)
    ) AS v(kind_code, w, h, label_uk, label_ru, label_en, code, name_uk, name_ru, name_en, is_vertical)
    LEFT JOIN pk ON pk.code = v.kind_code
    ON CONFLICT (label_uk, width_mm, height_mm) DO NOTHING;
    """)

    # --- product_kind_print_colors (дозволені схеми) ---
    op.execute("""
    WITH kinds AS (SELECT id, code FROM product_kinds),
         schemes AS (SELECT id, code FROM print_color_schemes),
         pairs AS (
           SELECT k.id, s.id FROM kinds k JOIN schemes s ON s.code IN ('4_0','4_4','1_0','1_1') WHERE k.code='business_cards'
           UNION ALL
           SELECT k.id, s.id FROM kinds k JOIN schemes s ON s.code IN ('4_0','4_4') WHERE k.code='flyers'
           UNION ALL
           SELECT k.id, s.id FROM kinds k JOIN schemes s ON s.code IN ('4_4') WHERE k.code='brochures'
           UNION ALL
           SELECT k.id, s.id FROM kinds k JOIN schemes s ON s.code IN ('4_0','1_0') WHERE k.code='stickers'
           UNION ALL
           SELECT k.id, s.id FROM kinds k JOIN schemes s ON s.code IN ('4_0') WHERE k.code='posters'
         )
    INSERT INTO product_kind_print_colors(product_kind_id, color_scheme_id)
    SELECT DISTINCT * FROM pairs
    ON CONFLICT DO NOTHING;
    """)

    # --- materials (мінімум, щоб адмінка відкривалась) ---
    op.execute("""
    INSERT INTO materials(code, name, price_per_unit, created_at, updated_at)
    VALUES
      ('paper_coated_250','Папір крейдований 250', 0.50, now(), now()),
      ('paper_coated_350','Папір крейдований 350', 0.75, now(), now())
    ON CONFLICT (code) DO NOTHING;
    """)


def downgrade():
    # тільки чистимо введені сид-дані (схеми/зв'язки/довідники залишаємо якщо вже використовуються)
    op.execute(
        "DELETE FROM product_kind_print_colors WHERE product_kind_id IN (SELECT id FROM product_kinds WHERE code IN ('business_cards','flyers','brochures','stickers','posters'));"
    )
    op.execute("DELETE FROM sizes WHERE code IN ('bc_90x50','fly_a6','pos_a3');")
    op.execute(
        "DELETE FROM product_kind_names WHERE product_kind_id IN (SELECT id FROM product_kinds WHERE code IN ('business_cards','flyers','brochures','stickers','posters'));"
    )
    op.execute(
        "DELETE FROM product_kinds WHERE code IN ('business_cards','flyers','brochures','stickers','posters');"
    )
    op.execute("DELETE FROM finishing_options WHERE code IN ('lam_gloss','lam_matte','uv_spot');")
    op.execute("DELETE FROM finishing_kinds WHERE code IN ('lamination','uv');")
    op.execute("DELETE FROM materials WHERE code IN ('paper_coated_250','paper_coated_350');")
    # print_color_schemes залишаємо (можуть уже використовуватись іншими зв’язками)
