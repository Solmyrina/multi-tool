-- Travel Planner Database Schema
-- Created: 2025-10-25
-- Purpose: Add tables for travel planning feature (trips, accommodations, activities, routes, expenses, documents, packing)

-- =============================================================================
-- 1. TRIPS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS trips (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'planning' CHECK (status IN ('planning', 'booked', 'in_progress', 'completed', 'cancelled')),
    budget_total DECIMAL(10,2),
    budget_currency VARCHAR(3) DEFAULT 'EUR',
    destination_country VARCHAR(100),
    destination_city VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_dates CHECK (end_date >= start_date),
    CONSTRAINT valid_budget CHECK (budget_total IS NULL OR budget_total >= 0)
);

-- Indexes for trips
CREATE INDEX idx_trips_user_id ON trips(user_id);
CREATE INDEX idx_trips_dates ON trips(start_date, end_date);
CREATE INDEX idx_trips_status ON trips(status);
CREATE INDEX idx_trips_destination ON trips(destination_country, destination_city);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_trips_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trips_updated_at_trigger
    BEFORE UPDATE ON trips
    FOR EACH ROW
    EXECUTE FUNCTION update_trips_updated_at();

COMMENT ON TABLE trips IS 'Main trip/vacation planning container';


-- =============================================================================
-- 2. ACCOMMODATIONS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS accommodations (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) DEFAULT 'hotel' CHECK (type IN ('hotel', 'hostel', 'apartment', 'airbnb', 'resort', 'camping', 'other')),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    check_in_date DATE NOT NULL,
    check_in_time TIME DEFAULT '15:00:00',
    check_out_date DATE NOT NULL,
    check_out_time TIME DEFAULT '11:00:00',
    booking_reference VARCHAR(100),
    booking_url TEXT,
    cost_per_night DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_accommodation_dates CHECK (check_out_date >= check_in_date),
    CONSTRAINT valid_costs CHECK (
        (cost_per_night IS NULL OR cost_per_night >= 0) AND
        (total_cost IS NULL OR total_cost >= 0)
    )
);

-- Indexes for accommodations
CREATE INDEX idx_accommodations_trip_id ON accommodations(trip_id);
CREATE INDEX idx_accommodations_dates ON accommodations(check_in_date, check_out_date);
CREATE INDEX idx_accommodations_location ON accommodations(latitude, longitude);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_accommodations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER accommodations_updated_at_trigger
    BEFORE UPDATE ON accommodations
    FOR EACH ROW
    EXECUTE FUNCTION update_accommodations_updated_at();

COMMENT ON TABLE accommodations IS 'Hotels, hostels, Airbnbs and other lodging';


-- =============================================================================
-- 3. ACTIVITIES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'other' CHECK (category IN ('sightseeing', 'dining', 'transport', 'entertainment', 'shopping', 'outdoor', 'cultural', 'other')),
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP,
    duration_minutes INTEGER,
    location_name VARCHAR(200),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('must_see', 'high', 'medium', 'low', 'optional')),
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'booked', 'completed', 'cancelled', 'skipped')),
    cost DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    booking_reference VARCHAR(100),
    booking_url TEXT,
    opening_hours VARCHAR(100),
    contact_info TEXT,
    notes TEXT,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_activity_times CHECK (
        end_datetime IS NULL OR end_datetime >= start_datetime
    ),
    CONSTRAINT valid_duration CHECK (
        duration_minutes IS NULL OR duration_minutes > 0
    ),
    CONSTRAINT valid_activity_cost CHECK (
        cost IS NULL OR cost >= 0
    )
);

-- Indexes for activities
CREATE INDEX idx_activities_trip_id ON activities(trip_id);
CREATE INDEX idx_activities_datetime ON activities(start_datetime);
CREATE INDEX idx_activities_category ON activities(category);
CREATE INDEX idx_activities_priority ON activities(priority);
CREATE INDEX idx_activities_status ON activities(status);
CREATE INDEX idx_activities_location ON activities(latitude, longitude);
CREATE INDEX idx_activities_display_order ON activities(trip_id, display_order);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_activities_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER activities_updated_at_trigger
    BEFORE UPDATE ON activities
    FOR EACH ROW
    EXECUTE FUNCTION update_activities_updated_at();

COMMENT ON TABLE activities IS 'Sightseeing, dining, events and other trip activities';


-- =============================================================================
-- 4. ROUTES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    from_location VARCHAR(200) NOT NULL,
    to_location VARCHAR(200) NOT NULL,
    from_latitude DECIMAL(10,8),
    from_longitude DECIMAL(11,8),
    to_latitude DECIMAL(10,8),
    to_longitude DECIMAL(11,8),
    transport_mode VARCHAR(50) DEFAULT 'car' CHECK (transport_mode IN ('flight', 'train', 'bus', 'car', 'ferry', 'walking', 'cycling', 'other')),
    departure_datetime TIMESTAMP,
    arrival_datetime TIMESTAMP,
    duration_minutes INTEGER,
    distance_km DECIMAL(8,2),
    cost DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    booking_reference VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_route_times CHECK (
        (departure_datetime IS NULL OR arrival_datetime IS NULL) OR 
        (arrival_datetime >= departure_datetime)
    ),
    CONSTRAINT valid_route_distance CHECK (
        distance_km IS NULL OR distance_km >= 0
    ),
    CONSTRAINT valid_route_cost CHECK (
        cost IS NULL OR cost >= 0
    )
);

-- Indexes for routes
CREATE INDEX idx_routes_trip_id ON routes(trip_id);
CREATE INDEX idx_routes_datetime ON routes(departure_datetime);
CREATE INDEX idx_routes_mode ON routes(transport_mode);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_routes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER routes_updated_at_trigger
    BEFORE UPDATE ON routes
    FOR EACH ROW
    EXECUTE FUNCTION update_routes_updated_at();

COMMENT ON TABLE routes IS 'Transportation between locations (flights, trains, etc.)';


-- =============================================================================
-- 5. EXPENSES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    activity_id INTEGER REFERENCES activities(id) ON DELETE SET NULL,
    accommodation_id INTEGER REFERENCES accommodations(id) ON DELETE SET NULL,
    route_id INTEGER REFERENCES routes(id) ON DELETE SET NULL,
    category VARCHAR(50) DEFAULT 'other' CHECK (category IN ('accommodation', 'transport', 'food', 'activities', 'shopping', 'other')),
    description VARCHAR(200) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    expense_date DATE NOT NULL,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_expense_amount CHECK (amount >= 0)
);

-- Indexes for expenses
CREATE INDEX idx_expenses_trip_id ON expenses(trip_id);
CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_category ON expenses(category);
CREATE INDEX idx_expenses_activity ON expenses(activity_id);
CREATE INDEX idx_expenses_accommodation ON expenses(accommodation_id);
CREATE INDEX idx_expenses_route ON expenses(route_id);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_expenses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER expenses_updated_at_trigger
    BEFORE UPDATE ON expenses
    FOR EACH ROW
    EXECUTE FUNCTION update_expenses_updated_at();

COMMENT ON TABLE expenses IS 'Track all trip-related spending';


-- =============================================================================
-- 6. TRIP_DOCUMENTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS trip_documents (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    document_type VARCHAR(50) DEFAULT 'other' CHECK (document_type IN ('passport', 'visa', 'ticket', 'reservation', 'insurance', 'map', 'other')),
    file_path TEXT,
    file_url TEXT,
    description TEXT,
    expiry_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for trip_documents
CREATE INDEX idx_trip_documents_trip_id ON trip_documents(trip_id);
CREATE INDEX idx_trip_documents_type ON trip_documents(document_type);
CREATE INDEX idx_trip_documents_expiry ON trip_documents(expiry_date);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_trip_documents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trip_documents_updated_at_trigger
    BEFORE UPDATE ON trip_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_trip_documents_updated_at();

COMMENT ON TABLE trip_documents IS 'Store references to important documents (passports, tickets, etc.)';


-- =============================================================================
-- 7. PACKING_LISTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS packing_lists (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    category VARCHAR(50) DEFAULT 'general' CHECK (category IN ('clothing', 'toiletries', 'electronics', 'documents', 'medication', 'general', 'other')),
    item_name VARCHAR(200) NOT NULL,
    quantity INTEGER DEFAULT 1,
    is_packed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_quantity CHECK (quantity > 0)
);

-- Indexes for packing_lists
CREATE INDEX idx_packing_lists_trip_id ON packing_lists(trip_id);
CREATE INDEX idx_packing_lists_category ON packing_lists(category);
CREATE INDEX idx_packing_lists_packed ON packing_lists(is_packed);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_packing_lists_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER packing_lists_updated_at_trigger
    BEFORE UPDATE ON packing_lists
    FOR EACH ROW
    EXECUTE FUNCTION update_packing_lists_updated_at();

COMMENT ON TABLE packing_lists IS 'Track what to pack for the trip';


-- =============================================================================
-- PHASE 2 TABLES (Collaborative Features)
-- =============================================================================
-- These tables will be created in Phase 2
-- Uncomment when ready to implement collaborative features

/*
CREATE TABLE IF NOT EXISTS trip_participants (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'viewer' CHECK (role IN ('owner', 'editor', 'viewer')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(trip_id, user_id)
);

CREATE INDEX idx_trip_participants_trip ON trip_participants(trip_id);
CREATE INDEX idx_trip_participants_user ON trip_participants(user_id);

COMMENT ON TABLE trip_participants IS 'Share trips with other users (Phase 2)';


CREATE TABLE IF NOT EXISTS trip_comments (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_id INTEGER REFERENCES activities(id) ON DELETE CASCADE,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trip_comments_trip ON trip_comments(trip_id);
CREATE INDEX idx_trip_comments_activity ON trip_comments(activity_id);

COMMENT ON TABLE trip_comments IS 'Discussion threads on trips and activities (Phase 2)';
*/


-- =============================================================================
-- SAMPLE DATA (For Testing)
-- =============================================================================

-- Insert sample trip (only if a user exists)
DO $$
DECLARE
    v_user_id UUID;
    v_trip_id INTEGER;
BEGIN
    -- Get first user
    SELECT id INTO v_user_id FROM users LIMIT 1;
    
    IF v_user_id IS NOT NULL THEN
        INSERT INTO trips (user_id, name, description, start_date, end_date, status, budget_total, destination_country, destination_city, timezone)
        VALUES (
            v_user_id,
            'Summer in Italy 2025',
            'Two weeks exploring Rome, Florence, and Venice',
            '2025-07-01',
            '2025-07-14',
            'planning',
            3000.00,
            'Italy',
            'Rome',
            'Europe/Rome'
        ) ON CONFLICT DO NOTHING
        RETURNING id INTO v_trip_id;
        
        -- If trip was created, add sample data
        IF v_trip_id IS NOT NULL THEN
                -- Sample accommodation
                INSERT INTO accommodations (trip_id, name, type, address, city, country, check_in_date, check_out_date, cost_per_night, total_cost, latitude, longitude)
                VALUES (
                    v_trip_id,
                    'Hotel Colosseo',
                    'hotel',
                    'Via del Colosseo, 123',
                    'Rome',
                    'Italy',
                    '2025-07-01',
                    '2025-07-05',
                    120.00,
                    480.00,
                    41.8902,
                    12.4922
                );
                
                -- Sample activities
                INSERT INTO activities (trip_id, name, description, category, start_datetime, duration_minutes, location_name, city, priority, latitude, longitude)
                VALUES 
                (
                    v_trip_id,
                    'Visit the Colosseum',
                    'Explore the ancient Roman amphitheater',
                    'sightseeing',
                    '2025-07-02 09:00:00',
                    180,
                    'Colosseum',
                    'Rome',
                    'must_see',
                    41.8902,
                    12.4922
                ),
                (
                    v_trip_id,
                    'Vatican Museums',
                    'See the Sistine Chapel and Vatican art collection',
                    'cultural',
                    '2025-07-03 10:00:00',
                    240,
                    'Vatican Museums',
                    'Vatican City',
                    'must_see',
                    41.9029,
                    12.4534
                );
                
                -- Sample packing list
                INSERT INTO packing_lists (trip_id, category, item_name, quantity)
                VALUES 
                (v_trip_id, 'clothing', 'T-shirts', 7),
                (v_trip_id, 'clothing', 'Shorts', 3),
                (v_trip_id, 'toiletries', 'Sunscreen', 1),
                (v_trip_id, 'electronics', 'Phone charger', 1),
                (v_trip_id, 'documents', 'Passport', 1);
            END IF;
        END IF;
    END IF;
END $$;


-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================

-- Grant access to webapp and api users (if they exist)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'webapp') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON trips, accommodations, activities, routes, expenses, trip_documents, packing_lists TO webapp;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO webapp;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON trips, accommodations, activities, routes, expenses, trip_documents, packing_lists TO api;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api;
    END IF;
END $$;


-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify tables created
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_name IN ('trips', 'accommodations', 'activities', 'routes', 'expenses', 'trip_documents', 'packing_lists')
ORDER BY table_name;

-- Show sample data counts
SELECT 
    'trips' as table_name, COUNT(*) as row_count FROM trips
UNION ALL
SELECT 'accommodations', COUNT(*) FROM accommodations
UNION ALL
SELECT 'activities', COUNT(*) FROM activities
UNION ALL
SELECT 'routes', COUNT(*) FROM routes
UNION ALL
SELECT 'expenses', COUNT(*) FROM expenses
UNION ALL
SELECT 'trip_documents', COUNT(*) FROM trip_documents
UNION ALL
SELECT 'packing_lists', COUNT(*) FROM packing_lists;

-- Done!
SELECT 'Travel Planner database schema created successfully! ✅' as status;
