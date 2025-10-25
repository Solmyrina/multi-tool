-- Security Features: User Activity Logging, Session Management, and Audit Trail
-- This script creates tables and triggers for comprehensive security monitoring

-- 1. User Activity Logging Table
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    activity_type VARCHAR(50) NOT NULL, -- 'login', 'logout', 'page_view', 'widget_action', 'settings_change', etc.
    activity_description TEXT,
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10), -- GET, POST, PUT, DELETE
    request_url TEXT,
    request_data JSONB, -- Store request parameters/body as JSON
    response_status INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER, -- Request processing time in milliseconds
    additional_data JSONB -- Any extra context data
);

-- 2. Enhanced Session Management Table (extends existing user_sessions)
-- First, let's see what the current user_sessions table looks like and enhance it
ALTER TABLE user_sessions 
ADD COLUMN IF NOT EXISTS ip_address INET,
ADD COLUMN IF NOT EXISTS user_agent TEXT,
ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS login_method VARCHAR(50) DEFAULT 'password', -- 'password', 'remember_me', etc.
ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(255),
ADD COLUMN IF NOT EXISTS location_info JSONB; -- Geolocation data if available

-- 3. Audit Trail Table
CREATE TABLE IF NOT EXISTS audit_trail (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Allow NULL for system actions
    session_id VARCHAR(255),
    table_name VARCHAR(100) NOT NULL, -- Which table was affected
    record_id VARCHAR(100), -- ID of the affected record (as string to handle different ID types)
    action VARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_values JSONB, -- Previous values (for UPDATE and DELETE)
    new_values JSONB, -- New values (for INSERT and UPDATE)
    changed_fields TEXT[], -- Array of field names that changed
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    additional_context JSONB -- Extra context like reason for change, bulk operation ID, etc.
);

-- 4. Security Events Table (for suspicious activity detection)
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL, -- 'failed_login', 'unusual_location', 'rapid_requests', etc.
    severity VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'
    description TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    additional_data JSONB
);

-- 5. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_timestamp ON user_activity_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_activity_type ON user_activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_ip_address ON user_activity_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_session_id ON user_activity_logs(session_id);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity DESC);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_ip_address ON user_sessions(ip_address);

CREATE INDEX IF NOT EXISTS idx_audit_trail_user_id ON audit_trail(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp ON audit_trail(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_trail_table_name ON audit_trail(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_trail_action ON audit_trail(action);
CREATE INDEX IF NOT EXISTS idx_audit_trail_record_id ON audit_trail(record_id);

CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_events_resolved ON security_events(resolved);

-- 6. Create a view for active sessions
CREATE OR REPLACE VIEW active_user_sessions AS
SELECT 
    us.id,
    us.user_id,
    u.username,
    u.email,
    us.session_token,
    us.ip_address,
    us.user_agent,
    us.created_at as login_time,
    us.last_activity,
    us.login_method,
    us.device_fingerprint,
    us.location_info,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - us.last_activity))/60 as idle_minutes
FROM user_sessions us
JOIN users u ON us.user_id = u.id
WHERE us.is_active = TRUE
ORDER BY us.last_activity DESC;

-- 7. Create a view for recent user activity summary
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    COUNT(ual.id) as total_activities,
    COUNT(CASE WHEN ual.activity_type = 'login' THEN 1 END) as login_count,
    COUNT(CASE WHEN ual.activity_type = 'page_view' THEN 1 END) as page_views,
    COUNT(CASE WHEN ual.activity_type = 'widget_action' THEN 1 END) as widget_actions,
    MAX(ual.timestamp) as last_activity,
    COUNT(DISTINCT ual.ip_address) as unique_ips,
    AVG(ual.duration_ms) as avg_response_time_ms
FROM users u
LEFT JOIN user_activity_logs ual ON u.id = ual.user_id 
    AND ual.timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY u.id, u.username, u.email
ORDER BY last_activity DESC NULLS LAST;

-- 8. Create functions for automatic audit trail triggers
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert audit record for any changes to monitored tables
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_trail (
            table_name, 
            record_id, 
            action, 
            old_values,
            timestamp
        ) VALUES (
            TG_TABLE_NAME,
            OLD.id::TEXT,
            'DELETE',
            row_to_json(OLD),
            CURRENT_TIMESTAMP
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_trail (
            table_name, 
            record_id, 
            action, 
            old_values,
            new_values,
            changed_fields,
            timestamp
        ) VALUES (
            TG_TABLE_NAME,
            NEW.id::TEXT,
            'UPDATE',
            row_to_json(OLD),
            row_to_json(NEW),
            ARRAY(
                SELECT key FROM jsonb_each(row_to_json(OLD)::jsonb) old_row
                JOIN jsonb_each(row_to_json(NEW)::jsonb) new_row USING(key)
                WHERE old_row.value IS DISTINCT FROM new_row.value
            ),
            CURRENT_TIMESTAMP
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_trail (
            table_name, 
            record_id, 
            action, 
            new_values,
            timestamp
        ) VALUES (
            TG_TABLE_NAME,
            NEW.id::TEXT,
            'INSERT',
            row_to_json(NEW),
            CURRENT_TIMESTAMP
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 9. Create triggers for important tables
-- Users table audit
DROP TRIGGER IF EXISTS users_audit_trigger ON users;
CREATE TRIGGER users_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- User widget settings audit
DROP TRIGGER IF EXISTS user_widget_settings_audit_trigger ON user_widget_settings;
CREATE TRIGGER user_widget_settings_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON user_widget_settings
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Weather locations audit (both old and new tables)
DROP TRIGGER IF EXISTS weather_locations_audit_trigger ON weather_locations;
CREATE TRIGGER weather_locations_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON weather_locations
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

DROP TRIGGER IF EXISTS shared_weather_locations_audit_trigger ON shared_weather_locations;
CREATE TRIGGER shared_weather_locations_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON shared_weather_locations
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

DROP TRIGGER IF EXISTS user_favorite_weather_locations_audit_trigger ON user_favorite_weather_locations;
CREATE TRIGGER user_favorite_weather_locations_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON user_favorite_weather_locations
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- 10. Create cleanup function for old logs (to prevent infinite growth)
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS void AS $$
BEGIN
    -- Keep only last 90 days of activity logs
    DELETE FROM user_activity_logs 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
    -- Keep only last 1 year of audit trail
    DELETE FROM audit_trail 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 year';
    
    -- Keep resolved security events for 6 months, unresolved indefinitely
    DELETE FROM security_events 
    WHERE resolved = TRUE AND timestamp < CURRENT_TIMESTAMP - INTERVAL '6 months';
    
    -- Clean up inactive sessions older than 30 days
    DELETE FROM user_sessions 
    WHERE is_active = FALSE AND last_activity < CURRENT_TIMESTAMP - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

COMMIT;