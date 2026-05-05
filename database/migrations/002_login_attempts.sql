CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    ip_address TEXT,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_email_created_at
ON login_attempts(lower(email), created_at DESC);

CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_created_at
ON login_attempts(ip_address, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_login_attempts_success
ON login_attempts(success);
