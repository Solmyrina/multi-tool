-- Trip Sharing and Permissions System
-- Created: 2025-10-25
-- Purpose: Enable multi-user trip sharing with granular category-based permissions

-- =============================================================================
-- 1. TRIP_SHARES TABLE - Links users to shared trips
-- =============================================================================

CREATE TABLE IF NOT EXISTS trip_shares (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'viewer' CHECK (role IN ('viewer', 'editor', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate shares
    CONSTRAINT unique_trip_user_share UNIQUE (trip_id, shared_with_user_id),
    -- Prevent self-sharing
    CONSTRAINT no_self_share CHECK (shared_with_user_id != shared_by_user_id)
);

-- Indexes for trip_shares
CREATE INDEX idx_trip_shares_trip_id ON trip_shares(trip_id);
CREATE INDEX idx_trip_shares_shared_with_user ON trip_shares(shared_with_user_id);
CREATE INDEX idx_trip_shares_shared_by_user ON trip_shares(shared_by_user_id);

COMMENT ON TABLE trip_shares IS 'Tracks which users have access to which trips';
COMMENT ON COLUMN trip_shares.role IS 'General role level: viewer (read-only), editor (can modify), admin (can share)';

-- =============================================================================
-- 2. TRIP_PERMISSIONS TABLE - Granular category-based permissions
-- =============================================================================

CREATE TABLE IF NOT EXISTS trip_permissions (
    id SERIAL PRIMARY KEY,
    share_id INTEGER NOT NULL REFERENCES trip_shares(id) ON DELETE CASCADE,
    category VARCHAR(30) NOT NULL CHECK (category IN (
        'budget',
        'accommodations', 
        'activities',
        'packing_list',
        'timeline',
        'routes',
        'documents'
    )),
    can_read BOOLEAN DEFAULT true,
    can_write BOOLEAN DEFAULT false,
    can_delete BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Each share can only have one permission set per category
    CONSTRAINT unique_share_category UNIQUE (share_id, category),
    -- Write requires read, delete requires write
    CONSTRAINT valid_permission_hierarchy CHECK (
        (NOT can_write OR can_read) AND 
        (NOT can_delete OR can_write)
    )
);

-- Indexes for trip_permissions
CREATE INDEX idx_trip_permissions_share_id ON trip_permissions(share_id);
CREATE INDEX idx_trip_permissions_category ON trip_permissions(category);

COMMENT ON TABLE trip_permissions IS 'Granular permissions for each trip category per shared user';
COMMENT ON COLUMN trip_permissions.category IS 'Trip data category: budget, accommodations, activities, packing_list, timeline, routes, documents';

-- =============================================================================
-- 3. AUTO-UPDATE TIMESTAMP TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_trip_shares_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trip_shares_updated_at_trigger
    BEFORE UPDATE ON trip_shares
    FOR EACH ROW
    EXECUTE FUNCTION update_trip_shares_updated_at();

CREATE OR REPLACE FUNCTION update_trip_permissions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trip_permissions_updated_at_trigger
    BEFORE UPDATE ON trip_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_trip_permissions_updated_at();

-- =============================================================================
-- 4. HELPER VIEWS FOR EASY PERMISSION CHECKING
-- =============================================================================

-- View to see all permissions for a user on a trip (combines all categories)
CREATE OR REPLACE VIEW trip_user_permissions AS
SELECT 
    ts.trip_id,
    ts.shared_with_user_id as user_id,
    ts.shared_by_user_id,
    ts.role,
    tp.category,
    tp.can_read,
    tp.can_write,
    tp.can_delete,
    t.user_id as trip_owner_id,
    CASE 
        WHEN t.user_id = ts.shared_with_user_id THEN true 
        ELSE false 
    END as is_owner
FROM trip_shares ts
JOIN trips t ON ts.trip_id = t.id
LEFT JOIN trip_permissions tp ON ts.id = tp.share_id;

COMMENT ON VIEW trip_user_permissions IS 'Consolidated view of all user permissions on trips';

-- =============================================================================
-- 5. PERMISSION CHECK FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION check_trip_permission(
    p_trip_id INTEGER,
    p_user_id UUID,
    p_category VARCHAR(30),
    p_action VARCHAR(10) -- 'read', 'write', or 'delete'
)
RETURNS BOOLEAN AS $$
DECLARE
    v_is_owner BOOLEAN;
    v_can_perform BOOLEAN := false;
BEGIN
    -- Check if user is the trip owner (owners have full access)
    SELECT EXISTS (
        SELECT 1 FROM trips 
        WHERE id = p_trip_id AND user_id = p_user_id
    ) INTO v_is_owner;
    
    IF v_is_owner THEN
        RETURN true;
    END IF;
    
    -- Check if user has shared access with required permission
    SELECT 
        CASE p_action
            WHEN 'read' THEN COALESCE(tp.can_read, false)
            WHEN 'write' THEN COALESCE(tp.can_write, false)
            WHEN 'delete' THEN COALESCE(tp.can_delete, false)
            ELSE false
        END
    INTO v_can_perform
    FROM trip_shares ts
    LEFT JOIN trip_permissions tp ON ts.id = tp.share_id AND tp.category = p_category
    WHERE ts.trip_id = p_trip_id 
    AND ts.shared_with_user_id = p_user_id;
    
    RETURN COALESCE(v_can_perform, false);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION check_trip_permission IS 'Check if a user has specific permission on a trip category';

-- =============================================================================
-- 6. DEFAULT PERMISSION PRESETS
-- =============================================================================

-- Function to create default permissions when sharing a trip
CREATE OR REPLACE FUNCTION create_default_trip_permissions(p_share_id INTEGER, p_role VARCHAR(20))
RETURNS VOID AS $$
BEGIN
    -- Viewer role: read-only access to all categories
    IF p_role = 'viewer' THEN
        INSERT INTO trip_permissions (share_id, category, can_read, can_write, can_delete)
        VALUES 
            (p_share_id, 'budget', true, false, false),
            (p_share_id, 'accommodations', true, false, false),
            (p_share_id, 'activities', true, false, false),
            (p_share_id, 'packing_list', true, false, false),
            (p_share_id, 'timeline', true, false, false),
            (p_share_id, 'routes', true, false, false),
            (p_share_id, 'documents', true, false, false);
    
    -- Editor role: read + write access to all categories except budget
    ELSIF p_role = 'editor' THEN
        INSERT INTO trip_permissions (share_id, category, can_read, can_write, can_delete)
        VALUES 
            (p_share_id, 'budget', true, false, false),
            (p_share_id, 'accommodations', true, true, true),
            (p_share_id, 'activities', true, true, true),
            (p_share_id, 'packing_list', true, true, true),
            (p_share_id, 'timeline', true, true, false),
            (p_share_id, 'routes', true, true, true),
            (p_share_id, 'documents', true, true, true);
    
    -- Admin role: full access to all categories
    ELSIF p_role = 'admin' THEN
        INSERT INTO trip_permissions (share_id, category, can_read, can_write, can_delete)
        VALUES 
            (p_share_id, 'budget', true, true, true),
            (p_share_id, 'accommodations', true, true, true),
            (p_share_id, 'activities', true, true, true),
            (p_share_id, 'packing_list', true, true, true),
            (p_share_id, 'timeline', true, true, true),
            (p_share_id, 'routes', true, true, true),
            (p_share_id, 'documents', true, true, true);
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_default_trip_permissions IS 'Creates default permission set based on role when sharing a trip';

-- =============================================================================
-- 7. TRIGGER TO AUTO-CREATE DEFAULT PERMISSIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION auto_create_trip_permissions()
RETURNS TRIGGER AS $$
BEGIN
    -- Automatically create default permissions when a new share is created
    PERFORM create_default_trip_permissions(NEW.id, NEW.role);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_create_permissions_trigger
    AFTER INSERT ON trip_shares
    FOR EACH ROW
    EXECUTE FUNCTION auto_create_trip_permissions();

COMMENT ON TRIGGER auto_create_permissions_trigger ON trip_shares IS 'Automatically creates default permissions when a trip is shared';

-- =============================================================================
-- 8. EXAMPLE QUERIES FOR COMMON OPERATIONS
-- =============================================================================

-- Get all trips a user has access to (owned + shared)
-- SELECT DISTINCT t.* 
-- FROM trips t
-- LEFT JOIN trip_shares ts ON t.id = ts.trip_id
-- WHERE t.user_id = '<user_id>' OR ts.shared_with_user_id = '<user_id>';

-- Get all users who have access to a specific trip
-- SELECT 
--     u.id, u.username, u.email,
--     ts.role,
--     ts.created_at as shared_at
-- FROM trip_shares ts
-- JOIN users u ON ts.shared_with_user_id = u.id
-- WHERE ts.trip_id = <trip_id>;

-- Get all permissions a user has on a specific trip
-- SELECT 
--     tp.category,
--     tp.can_read,
--     tp.can_write,
--     tp.can_delete
-- FROM trip_shares ts
-- JOIN trip_permissions tp ON ts.id = tp.share_id
-- WHERE ts.trip_id = <trip_id> AND ts.shared_with_user_id = '<user_id>';

-- Check if user can perform action
-- SELECT check_trip_permission(<trip_id>, '<user_id>', 'activities', 'write');
