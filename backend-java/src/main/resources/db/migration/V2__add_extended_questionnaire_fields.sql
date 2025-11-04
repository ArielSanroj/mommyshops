-- Migration script to add extended questionnaire fields to user_profiles table
-- Version: 2.0
-- Date: 2025-11-02
-- Description: Adds 18 new fields from the extended questionnaire (22 steps)

-- Add new columns for extended questionnaire data
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS age VARCHAR(50),
ADD COLUMN IF NOT EXISTS skin_reactivity VARCHAR(255),
ADD COLUMN IF NOT EXISTS skin_goals TEXT,
ADD COLUMN IF NOT EXISTS face_shape VARCHAR(100),
ADD COLUMN IF NOT EXISTS hair_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS hair_porosity VARCHAR(100),
ADD COLUMN IF NOT EXISTS scalp_condition VARCHAR(255),
ADD COLUMN IF NOT EXISTS hair_concerns TEXT,
ADD COLUMN IF NOT EXISTS hair_routine TEXT,
ADD COLUMN IF NOT EXISTS fragrance_preference VARCHAR(255),
ADD COLUMN IF NOT EXISTS texture_preferences TEXT,
ADD COLUMN IF NOT EXISTS avoid_ingredients TEXT,
ADD COLUMN IF NOT EXISTS ingredient_focus TEXT,
ADD COLUMN IF NOT EXISTS environment_factors TEXT,
ADD COLUMN IF NOT EXISTS product_preferences VARCHAR(255),
ADD COLUMN IF NOT EXISTS budget VARCHAR(100),
ADD COLUMN IF NOT EXISTS purchase_frequency VARCHAR(100),
ADD COLUMN IF NOT EXISTS information_preference VARCHAR(255);

-- Add comments for documentation
COMMENT ON COLUMN user_profiles.age IS 'User age range from questionnaire';
COMMENT ON COLUMN user_profiles.skin_reactivity IS 'How skin reacts to new products';
COMMENT ON COLUMN user_profiles.skin_goals IS 'Comma-separated list of skin care goals';
COMMENT ON COLUMN user_profiles.face_shape IS 'Face shape for personalized recommendations';
COMMENT ON COLUMN user_profiles.hair_type IS 'Hair type pattern (1A-4C)';
COMMENT ON COLUMN user_profiles.hair_porosity IS 'Hair porosity level';
COMMENT ON COLUMN user_profiles.scalp_condition IS 'Scalp condition description';
COMMENT ON COLUMN user_profiles.hair_concerns IS 'Comma-separated list of hair concerns';
COMMENT ON COLUMN user_profiles.hair_routine IS 'Comma-separated list of hair care habits';
COMMENT ON COLUMN user_profiles.fragrance_preference IS 'Preferred fragrance intensity level';
COMMENT ON COLUMN user_profiles.texture_preferences IS 'Comma-separated list of preferred product textures';
COMMENT ON COLUMN user_profiles.avoid_ingredients IS 'Comma-separated list of ingredients to avoid';
COMMENT ON COLUMN user_profiles.ingredient_focus IS 'Comma-separated list of preferred active ingredients';
COMMENT ON COLUMN user_profiles.environment_factors IS 'Comma-separated list of environmental factors';
COMMENT ON COLUMN user_profiles.product_preferences IS 'Preferred product category';
COMMENT ON COLUMN user_profiles.budget IS 'Budget range for products';
COMMENT ON COLUMN user_profiles.purchase_frequency IS 'How often user updates routine';
COMMENT ON COLUMN user_profiles.information_preference IS 'Preferred information format for recommendations';

