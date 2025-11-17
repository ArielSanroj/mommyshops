-- Migration script to create leads table
-- Run this manually if Alembic is not configured

-- Create leads table
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(128) NOT NULL,
    phone VARCHAR(50) DEFAULT NULL,
    country VARCHAR(10) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups by email
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);

-- Create index for faster lookups by created_at
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);

