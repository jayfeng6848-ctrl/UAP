-- Platform baseline (STEP 0).
-- Bookkeeping only: no domain or business tables are created here.
CREATE TABLE IF NOT EXISTS platform_metadata (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
