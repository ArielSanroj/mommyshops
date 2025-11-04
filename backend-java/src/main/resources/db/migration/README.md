# Database Migrations

This directory contains SQL migration scripts for the database schema.

## Migration Files

- `V2__add_extended_questionnaire_fields.sql` - Adds 18 new fields from the extended questionnaire (22 steps) to the `user_profiles` table

## How to Apply Migrations

### Using Flyway (if configured)
```bash
./mvnw flyway:migrate
```

### Manual Application
```bash
# For PostgreSQL
psql -U your_user -d mommyshops -f src/main/resources/db/migration/V2__add_extended_questionnaire_fields.sql
```

### Using Spring Boot with Flyway
If Flyway is configured in your `application.yml`, migrations will run automatically on startup.

## Rollback

If you need to rollback this migration:

```sql
ALTER TABLE user_profiles 
DROP COLUMN IF EXISTS age,
DROP COLUMN IF EXISTS skin_reactivity,
DROP COLUMN IF EXISTS skin_goals,
DROP COLUMN IF EXISTS face_shape,
DROP COLUMN IF EXISTS hair_type,
DROP COLUMN IF EXISTS hair_porosity,
DROP COLUMN IF EXISTS scalp_condition,
DROP COLUMN IF EXISTS hair_concerns,
DROP COLUMN IF EXISTS hair_routine,
DROP COLUMN IF EXISTS fragrance_preference,
DROP COLUMN IF EXISTS texture_preferences,
DROP COLUMN IF EXISTS avoid_ingredients,
DROP COLUMN IF EXISTS ingredient_focus,
DROP COLUMN IF EXISTS environment_factors,
DROP COLUMN IF EXISTS product_preferences,
DROP COLUMN IF EXISTS budget,
DROP COLUMN IF EXISTS purchase_frequency,
DROP COLUMN IF EXISTS information_preference;
```
