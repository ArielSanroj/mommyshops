-- Migration script to add face_shape to users table and create custom_products table
-- Run this manually if Alembic is not configured

-- Add face_shape column to users table (if it doesn't exist)
-- For SQLite
ALTER TABLE users ADD COLUMN face_shape VARCHAR(64) DEFAULT NULL;

-- For PostgreSQL (uncomment if using PostgreSQL)
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS face_shape VARCHAR(64) DEFAULT NULL;

-- Create custom_products table
CREATE TABLE IF NOT EXISTS custom_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    base_product_name VARCHAR(255) NOT NULL,
    safe_ingredients TEXT,  -- JSON stored as TEXT
    substitutions TEXT,     -- JSON stored as TEXT
    profile_snapshot TEXT,  -- JSON stored as TEXT
    price REAL DEFAULT 0.0,
    status VARCHAR(32) DEFAULT 'draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_custom_products_user_id ON custom_products(user_id);

