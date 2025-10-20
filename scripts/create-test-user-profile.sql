-- Script para crear un UserProfile de prueba en la base de datos
-- Esto permitirá que el análisis funcione con el usuario mock

INSERT INTO user_profiles (
    id,
    user_id,
    hair_preferences,
    facial_skin_preferences,
    body_skin_preferences,
    budget_preferences,
    brand_preferences,
    email,
    skin_type,
    skin_concerns,
    allergies,
    pregnancy_status,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000001', -- ID del usuario mock
    'Cuidado capilar',
    'Mixta',
    'Normal',
    'Medio ($20-$50)',
    'Naturales y orgánicas',
    'test@example.com',
    'Mixta',
    'Acné, Piel grasa, Poros dilatados',
    'No, no tengo alergias conocidas',
    'not_pregnant',
    NOW(),
    NOW()
) ON CONFLICT (user_id) DO UPDATE SET
    skin_type = EXCLUDED.skin_type,
    skin_concerns = EXCLUDED.skin_concerns,
    allergies = EXCLUDED.allergies,
    budget_preferences = EXCLUDED.budget_preferences,
    updated_at = NOW();