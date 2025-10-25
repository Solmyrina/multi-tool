# Database Schema - Travel Planner

**Purpose**: Complete PostgreSQL database design for travel planning system  
**Status**: Planning Phase

---

## 🗄️ Table Structure

### Core Tables

#### 1. `trips`
Main trip container - one per vacation/journey

```sql
CREATE TABLE trips (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    destination_country VARCHAR(100),
    destination_city VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_budget DECIMAL(10, 2),
    budget_currency VARCHAR(3) DEFAULT 'EUR',
    status VARCHAR(20) DEFAULT 'planning', -- planning, confirmed, in_progress, completed, cancelled
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_dates CHECK (end_date >= start_date),
    CONSTRAINT valid_budget CHECK (total_budget >= 0)
);

CREATE INDEX idx_trips_user_id ON trips(user_id);
CREATE INDEX idx_trips_dates ON trips(start_date, end_date);
CREATE INDEX idx_trips_status ON trips(status);
```

#### 2. `accommodations`
Hotels, hostels, Airbnb, camping, etc.

```sql
CREATE TABLE accommodations (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- hotel, hostel, airbnb, camping, friend, other
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    check_in_date DATE NOT NULL,
    check_in_time TIME DEFAULT '15:00:00',
    check_out_date DATE NOT NULL,
    check_out_time TIME DEFAULT '11:00:00',
    cost_per_night DECIMAL(10, 2),
    total_cost DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'EUR',
    booking_reference VARCHAR(100),
    booking_url TEXT,
    contact_phone VARCHAR(50),
    contact_email VARCHAR(100),
    rating DECIMAL(2, 1), -- 0.0 to 5.0
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_dates CHECK (check_out_date >= check_in_date),
    CONSTRAINT valid_rating CHECK (rating >= 0 AND rating <= 5),
    CONSTRAINT valid_cost CHECK (cost_per_night >= 0 AND total_cost >= 0)
);

CREATE INDEX idx_accommodations_trip_id ON accommodations(trip_id);
CREATE INDEX idx_accommodations_dates ON accommodations(check_in_date, check_out_date);
CREATE INDEX idx_accommodations_location ON accommodations(latitude, longitude);
```

#### 3. `activities`
Things to do, places to visit, meals, travel segments

```sql
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50), -- sightseeing, dining, transport, entertainment, shopping, other
    activity_type VARCHAR(50), -- attraction, restaurant, museum, park, travel, flight, train, etc.
    location_name VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP,
    duration_minutes INTEGER,
    priority VARCHAR(20) DEFAULT 'medium', -- must_see, high, medium, low, optional
    cost DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'EUR',
    booking_required BOOLEAN DEFAULT FALSE,
    booking_reference VARCHAR(100),
    booking_url TEXT,
    opening_hours TEXT, -- JSON or text: "Mon-Fri 9:00-17:00"
    is_booked BOOLEAN DEFAULT FALSE,
    is_completed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    weather_dependent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_datetime CHECK (end_datetime IS NULL OR end_datetime >= start_datetime),
    CONSTRAINT valid_duration CHECK (duration_minutes IS NULL OR duration_minutes > 0),
    CONSTRAINT valid_cost CHECK (cost IS NULL OR cost >= 0)
);

CREATE INDEX idx_activities_trip_id ON activities(trip_id);
CREATE INDEX idx_activities_datetime ON activities(start_datetime, end_datetime);
CREATE INDEX idx_activities_location ON activities(latitude, longitude);
CREATE INDEX idx_activities_category ON activities(category);
CREATE INDEX idx_activities_priority ON activities(priority);
```

#### 4. `routes`
Travel connections between locations

```sql
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    from_activity_id INTEGER REFERENCES activities(id) ON DELETE SET NULL,
    to_activity_id INTEGER REFERENCES activities(id) ON DELETE SET NULL,
    from_accommodation_id INTEGER REFERENCES accommodations(id) ON DELETE SET NULL,
    to_accommodation_id INTEGER REFERENCES accommodations(id) ON DELETE SET NULL,
    transport_mode VARCHAR(50), -- walking, driving, public_transit, flight, train, bus, ferry
    distance_km DECIMAL(10, 2),
    duration_minutes INTEGER,
    cost DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'EUR',
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    booking_reference VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_route CHECK (
        (from_activity_id IS NOT NULL OR from_accommodation_id IS NOT NULL) AND
        (to_activity_id IS NOT NULL OR to_accommodation_id IS NOT NULL)
    ),
    CONSTRAINT valid_distance CHECK (distance_km IS NULL OR distance_km >= 0),
    CONSTRAINT valid_duration CHECK (duration_minutes IS NULL OR duration_minutes > 0)
);

CREATE INDEX idx_routes_trip_id ON routes(trip_id);
CREATE INDEX idx_routes_from_activity ON routes(from_activity_id);
CREATE INDEX idx_routes_to_activity ON routes(to_activity_id);
```

#### 5. `expenses`
Detailed budget tracking

```sql
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    activity_id INTEGER REFERENCES activities(id) ON DELETE SET NULL,
    accommodation_id INTEGER REFERENCES accommodations(id) ON DELETE SET NULL,
    category VARCHAR(50) NOT NULL, -- accommodation, food, transport, activities, shopping, emergency, other
    subcategory VARCHAR(50), -- breakfast, lunch, dinner, taxi, museum_entry, etc.
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    amount_in_base_currency DECIMAL(10, 2), -- converted to trip currency
    exchange_rate DECIMAL(10, 6),
    description TEXT,
    expense_date DATE NOT NULL,
    payment_method VARCHAR(50), -- cash, card, transfer, split
    is_paid BOOLEAN DEFAULT FALSE,
    receipt_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_amount CHECK (amount > 0)
);

CREATE INDEX idx_expenses_trip_id ON expenses(trip_id);
CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_category ON expenses(category);
```

#### 6. `documents`
Store trip-related files and links

```sql
CREATE TABLE trip_documents (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL, -- flight, hotel, passport, visa, insurance, ticket, other
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_path TEXT, -- local storage path or URL
    file_type VARCHAR(50), -- pdf, jpg, png, doc, url
    related_activity_id INTEGER REFERENCES activities(id) ON DELETE SET NULL,
    related_accommodation_id INTEGER REFERENCES accommodations(id) ON DELETE SET NULL,
    expiry_date DATE,
    is_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_file CHECK (file_path IS NOT NULL)
);

CREATE INDEX idx_documents_trip_id ON trip_documents(trip_id);
CREATE INDEX idx_documents_type ON trip_documents(document_type);
```

#### 7. `packing_lists`
Items to pack for the trip

```sql
CREATE TABLE packing_lists (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL, -- clothing, electronics, documents, toiletries, medication, other
    item_name VARCHAR(255) NOT NULL,
    quantity INTEGER DEFAULT 1,
    is_packed BOOLEAN DEFAULT FALSE,
    is_essential BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_quantity CHECK (quantity > 0)
);

CREATE INDEX idx_packing_trip_id ON packing_lists(trip_id);
CREATE INDEX idx_packing_category ON packing_lists(category);
```

#### 8. `trip_participants` (Phase 2 - Collaborative)
Share trips with other users

```sql
CREATE TABLE trip_participants (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'viewer', -- owner, editor, viewer
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, declined
    
    UNIQUE(trip_id, user_id)
);

CREATE INDEX idx_participants_trip_id ON trip_participants(trip_id);
CREATE INDEX idx_participants_user_id ON trip_participants(user_id);
```

#### 9. `trip_comments` (Phase 2 - Collaborative)
Discussion and notes

```sql
CREATE TABLE trip_comments (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_id INTEGER REFERENCES activities(id) ON DELETE CASCADE,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_trip_id ON trip_comments(trip_id);
CREATE INDEX idx_comments_activity_id ON trip_comments(activity_id);
```

---

## 🔗 Relationships

```
users (existing)
  └─► trips (1:many)
       ├─► accommodations (1:many)
       ├─► activities (1:many)
       ├─► routes (1:many)
       ├─► expenses (1:many)
       ├─► trip_documents (1:many)
       ├─► packing_lists (1:many)
       ├─► trip_participants (1:many)
       └─► trip_comments (1:many)

activities
  └─► routes (1:many as from/to)
  
accommodations
  └─► routes (1:many as from/to)
```

---

## 📊 Sample Data Queries

### Get complete trip with all details
```sql
SELECT 
    t.*,
    COUNT(DISTINCT a.id) as activity_count,
    COUNT(DISTINCT ac.id) as accommodation_count,
    SUM(e.amount_in_base_currency) as total_spent
FROM trips t
LEFT JOIN activities a ON t.id = a.trip_id
LEFT JOIN accommodations ac ON t.id = ac.trip_id
LEFT JOIN expenses e ON t.id = e.trip_id
WHERE t.user_id = :user_id
GROUP BY t.id;
```

### Get day-by-day itinerary
```sql
SELECT 
    DATE(start_datetime) as activity_date,
    name,
    start_datetime,
    end_datetime,
    category,
    location_name
FROM activities
WHERE trip_id = :trip_id
ORDER BY start_datetime;
```

### Calculate route distances
```sql
SELECT 
    r.*,
    a1.location_name as from_location,
    a2.location_name as to_location
FROM routes r
LEFT JOIN activities a1 ON r.from_activity_id = a1.id
LEFT JOIN activities a2 ON r.to_activity_id = a2.id
WHERE r.trip_id = :trip_id;
```

---

## 🚀 Migration Strategy

### Step 1: Create tables in order
```bash
# Run SQL scripts in this order:
1. trips table
2. accommodations table
3. activities table
4. routes table
5. expenses table
6. trip_documents table
7. packing_lists table
8. trip_participants table (Phase 2)
9. trip_comments table (Phase 2)
```

### Step 2: Add indexes
All indexes defined with tables

### Step 3: Add triggers (optional)
```sql
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_trips_updated_at BEFORE UPDATE ON trips
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_activities_updated_at BEFORE UPDATE ON activities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accommodations_updated_at BEFORE UPDATE ON accommodations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## 📝 Notes

- All monetary values use DECIMAL(10, 2) for precision
- All costs default to EUR but support multi-currency
- Latitude/Longitude stored with 8/11 decimal precision (~1mm accuracy)
- TimescaleDB not required for this feature (regular PostgreSQL sufficient)
- All foreign keys have CASCADE delete except routes (SET NULL)
- Trip status workflow: planning → confirmed → in_progress → completed

---

*Next: [API Endpoints](./02_API_ENDPOINTS.md)*
