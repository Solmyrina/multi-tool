-- Add user levels to existing database
-- Run this script to upgrade the database schema

-- Create user levels table
CREATE TABLE IF NOT EXISTS user_levels (
    id SERIAL PRIMARY KEY,
    level_name VARCHAR(50) UNIQUE NOT NULL,
    level_code VARCHAR(20) UNIQUE NOT NULL,
    permissions TEXT[],
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default user levels
INSERT INTO user_levels (level_name, level_code, permissions, description) VALUES 
('Super Admin', 'super_admin', ARRAY['all'], 'Full system access with all permissions'),
('Admin', 'admin', ARRAY['user_management', 'system_settings', 'view_logs'], 'Administrative access with user management'),
('Moderator', 'moderator', ARRAY['user_moderation', 'content_management'], 'Moderate users and content'),
('User', 'user', ARRAY['basic_access'], 'Standard user access'),
('Guest', 'guest', ARRAY['limited_access'], 'Limited guest access')
ON CONFLICT (level_code) DO NOTHING;

-- Add user_level_id column to users table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'user_level_id'
    ) THEN
        ALTER TABLE users ADD COLUMN user_level_id INTEGER REFERENCES user_levels(id) DEFAULT 4;
    END IF;
END $$;

-- Update existing admin user to super admin level
UPDATE users SET user_level_id = 1 WHERE username = 'admin';

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_user_level_id ON users(user_level_id);
CREATE INDEX IF NOT EXISTS idx_user_levels_level_code ON user_levels(level_code);