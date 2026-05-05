ALTER TABLE users
ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP(0);

CREATE INDEX IF NOT EXISTS idx_users_locked_until
ON users(locked_until);
