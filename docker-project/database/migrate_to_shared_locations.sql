-- Migration script to implement shared weather locations system
-- This prevents duplicate weather locations and allows multiple users to favorite the same location

-- Step 1: Create new shared weather locations table (without user_id)
CREATE TABLE IF NOT EXISTS shared_weather_locations (
    id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude NUMERIC(10,8) NOT NULL,
    longitude NUMERIC(11,8) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city_name, country, latitude, longitude)
);

-- Step 2: Create user favorites table to link users to shared locations
CREATE TABLE IF NOT EXISTS user_favorite_weather_locations (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    weather_location_id INTEGER NOT NULL REFERENCES shared_weather_locations(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, weather_location_id)
);

-- Step 3: Migrate existing data to shared system
-- Insert unique locations into shared table
INSERT INTO shared_weather_locations (city_name, country, latitude, longitude, created_at)
SELECT DISTINCT 
    city_name, 
    country, 
    latitude, 
    longitude,
    MIN(created_at) as created_at
FROM weather_locations 
GROUP BY city_name, country, latitude, longitude
ON CONFLICT (city_name, country, latitude, longitude) DO NOTHING;

-- Step 4: Create user favorites based on existing data
INSERT INTO user_favorite_weather_locations (user_id, weather_location_id, added_at)
SELECT DISTINCT 
    wl.user_id,
    swl.id,
    wl.created_at
FROM weather_locations wl
JOIN shared_weather_locations swl ON (
    wl.city_name = swl.city_name AND 
    wl.country = swl.country AND 
    wl.latitude = swl.latitude AND 
    wl.longitude = swl.longitude
)
ON CONFLICT (user_id, weather_location_id) DO NOTHING;

-- Step 5: Update weather data references
-- First, add new column to current_weather_data
ALTER TABLE current_weather_data 
ADD COLUMN IF NOT EXISTS shared_weather_location_id INTEGER REFERENCES shared_weather_locations(id);

-- Update the references
UPDATE current_weather_data cwd
SET shared_weather_location_id = swl.id
FROM weather_locations wl
JOIN shared_weather_locations swl ON (
    wl.city_name = swl.city_name AND 
    wl.country = swl.country AND 
    wl.latitude = swl.latitude AND 
    wl.longitude = swl.longitude
)
WHERE cwd.weather_location_id = wl.id;

-- Step 6: Update historic weather data references
ALTER TABLE historic_weather_data 
ADD COLUMN IF NOT EXISTS shared_weather_location_id INTEGER REFERENCES shared_weather_locations(id);

UPDATE historic_weather_data hwd
SET shared_weather_location_id = swl.id
FROM weather_locations wl
JOIN shared_weather_locations swl ON (
    wl.city_name = swl.city_name AND 
    wl.country = swl.country AND 
    wl.latitude = swl.latitude AND 
    wl.longitude = swl.longitude
)
WHERE hwd.weather_location_id = wl.id;

-- Step 7: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_shared_weather_locations_name ON shared_weather_locations(city_name, country);
CREATE INDEX IF NOT EXISTS idx_shared_weather_locations_coords ON shared_weather_locations(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorite_weather_locations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_location_id ON user_favorite_weather_locations(weather_location_id);
CREATE INDEX IF NOT EXISTS idx_current_weather_shared_location ON current_weather_data(shared_weather_location_id);
CREATE INDEX IF NOT EXISTS idx_historic_weather_shared_location ON historic_weather_data(shared_weather_location_id);

-- Step 8: Add constraints to ensure data integrity
ALTER TABLE current_weather_data 
ADD CONSTRAINT chk_weather_location_reference 
CHECK (
    (weather_location_id IS NOT NULL AND shared_weather_location_id IS NULL) OR
    (weather_location_id IS NULL AND shared_weather_location_id IS NOT NULL) OR
    (weather_location_id IS NOT NULL AND shared_weather_location_id IS NOT NULL)
);

ALTER TABLE historic_weather_data 
ADD CONSTRAINT chk_historic_weather_location_reference 
CHECK (
    (weather_location_id IS NOT NULL AND shared_weather_location_id IS NULL) OR
    (weather_location_id IS NULL AND shared_weather_location_id IS NOT NULL) OR
    (weather_location_id IS NOT NULL AND shared_weather_location_id IS NOT NULL)
);

-- Note: We keep the old tables and columns for now to ensure backward compatibility
-- They can be dropped later after confirming everything works correctly

COMMIT;