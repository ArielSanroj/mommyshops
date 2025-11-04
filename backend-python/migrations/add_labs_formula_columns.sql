-- Adds storage for labs formulation payloads
ALTER TABLE custom_products ADD COLUMN IF NOT EXISTS labs_formula JSON;
ALTER TABLE custom_products ADD COLUMN IF NOT EXISTS labs_summary JSON;
ALTER TABLE custom_products ADD COLUMN IF NOT EXISTS labs_mockup JSON;
