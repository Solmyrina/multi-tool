-- Create table for storing user's favorite weather locations
CREATE TABLE IF NOT EXISTS weather_locations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    city_name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, city_name, country)
);

-- Index for faster queries by user
CREATE INDEX IF NOT EXISTS idx_weather_locations_user_id ON weather_locations(user_id);

-- Index for location queries
CREATE INDEX IF NOT EXISTS idx_weather_locations_coords ON weather_locations(latitude, longitude);

-- Comments for documentation
COMMENT ON TABLE weather_locations IS 'Stores favorite weather locations for users';
COMMENT ON COLUMN weather_locations.latitude IS 'Latitude coordinate (decimal degrees)';
COMMENT ON COLUMN weather_locations.longitude IS 'Longitude coordinate (decimal degrees)';
COMMENT ON COLUMN weather_locations.city_name IS 'Name of the city or town';
COMMENT ON COLUMN weather_locations.country IS 'Country name';