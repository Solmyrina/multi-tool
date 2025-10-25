-- User Actions Audit System
-- This replaces the technical database audit with user-friendly action tracking

-- Create user_actions table for tracking actual user actions
CREATE TABLE IF NOT EXISTS user_actions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(100), -- Store username for easier display
    session_id VARCHAR(255),
    
    -- User-friendly action details
    category VARCHAR(50) NOT NULL, -- 'Authentication', 'Dashboard', 'Widgets', 'Settings', 'Admin'
    action VARCHAR(100) NOT NULL, -- 'Login', 'Add Widget', 'Change Password', etc.
    description TEXT NOT NULL, -- Human-readable description
    
    -- Technical details (optional)
    target_type VARCHAR(50), -- 'widget', 'user', 'settings', etc.
    target_id VARCHAR(100), -- ID of affected item
    details JSONB, -- Additional context
    
    -- Metadata
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT true, -- Whether the action succeeded
    error_message TEXT -- If action failed
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_timestamp ON user_actions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_actions_category ON user_actions(category);
CREATE INDEX IF NOT EXISTS idx_user_actions_action ON user_actions(action);
CREATE INDEX IF NOT EXISTS idx_user_actions_success ON user_actions(success);

-- Function to clean up old action logs (keep last 6 months)
CREATE OR REPLACE FUNCTION cleanup_old_user_actions()
RETURNS void AS $$
BEGIN
    DELETE FROM user_actions 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '6 months';
END;
$$ LANGUAGE plpgsql;

-- Sample user actions for reference
INSERT INTO user_actions (user_id, username, category, action, description, ip_address, success) VALUES
(NULL, 'system', 'System', 'Database Migration', 'User actions audit system initialized', '127.0.0.1', true)
ON CONFLICT DO NOTHING;