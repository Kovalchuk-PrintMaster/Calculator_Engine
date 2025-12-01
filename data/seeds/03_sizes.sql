-- приклад кількох універсальних форматів
INSERT INTO sizes(kind_id, width_mm, height_mm, label_uk, code, is_vertical, created_at, updated_at)
SELECT pk.id, s.w, s.h, s.label_uk, s.code, s.is_vertical, now(), now()
FROM product_kinds pk
JOIN (
  VALUES
  -- A6 (візитки часто інші, але для прикладу):
  ('flyers',105,148,'A6','A6',TRUE),
  ('flyers',148,210,'A5','A5',TRUE),
  ('posters',420,594,'A2','A2',TRUE),
  -- візитки 90x50, 85x55
  ('business_cards',90,50,'90×50','BC_90x50',FALSE),
  ('business_cards',85,55,'85×55','BC_85x55',FALSE)
) as s(kind_code,w,h,label_uk,code,is_vertical)
ON pk.code = s.kind_code
ON CONFLICT (code) DO NOTHING;
