-- Table for storing hourly current weather data from yr.no API
CREATE TABLE IF NOT EXISTS current_weather_data (
    id SERIAL PRIMARY KEY,
    weather_location_id INTEGER NOT NULL REFERENCES weather_locations(id) ON DELETE CASCADE,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    temperature DECIMAL(5,2), -- Current temperature in Celsius
    humidity INTEGER, -- Relative humidity percentage
    pressure DECIMAL(7,2), -- Air pressure in hPa
    wind_speed DECIMAL(5,2), -- Wind speed in m/s
    wind_direction INTEGER, -- Wind direction in degrees
    wind_gust DECIMAL(5,2), -- Wind gust speed in m/s
    precipitation DECIMAL(6,2), -- Precipitation in mm
    cloud_cover INTEGER, -- Cloud cover percentage
    visibility DECIMAL(5,1), -- Visibility in km
    weather_symbol VARCHAR(10), -- Weather symbol code from yr.no
    weather_description TEXT, -- Human readable weather description
    feels_like DECIMAL(5,2), -- Feels like temperature
    uv_index DECIMAL(3,1), -- UV index
    data_source VARCHAR(20) NOT NULL DEFAULT 'yr.no',
    api_response_time INTEGER, -- API response time in milliseconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique records per location per hour
    UNIQUE(weather_location_id, recorded_at)
);

-- Index for efficient queries by location and time
CREATE INDEX IF NOT EXISTS idx_current_weather_location_time 
ON current_weather_data(weather_location_id, recorded_at DESC);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_current_weather_recorded_at 
ON current_weather_data(recorded_at DESC);

-- View to join current weather data with location information
CREATE OR REPLACE VIEW current_weather_with_location AS
SELECT 
    cwd.*,
    wl.city_name,
    wl.country,
    wl.latitude,
    wl.longitude,
    wl.user_id
FROM current_weather_data cwd
JOIN weather_locations wl ON cwd.weather_location_id = wl.id;

-- Table to track current weather collection status and errors
CREATE TABLE IF NOT EXISTS current_weather_collection_log (
    id SERIAL PRIMARY KEY,
    weather_location_id INTEGER REFERENCES weather_locations(id) ON DELETE CASCADE,
    collection_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'started')),
    records_collected INTEGER DEFAULT 0,
    error_message TEXT,
    api_response_time INTEGER,
    yr_no_api_status INTEGER -- HTTP status code from yr.no API
);

-- Index for status monitoring on collection log
CREATE INDEX IF NOT EXISTS idx_current_weather_collection_log_time_status 
ON current_weather_collection_log(collection_time DESC, status);

-- Function to clean up old current weather data (keep only last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_current_weather_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM current_weather_data 
    WHERE recorded_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    INSERT INTO current_weather_collection_log (
        weather_location_id, 
        status, 
        records_collected, 
        error_message
    ) VALUES (
        NULL, 
        'success', 
        deleted_count, 
        'Cleanup: Removed old current weather data older than 30 days'
    );
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON current_weather_data TO root;
GRANT ALL PRIVILEGES ON current_weather_collection_log TO root;
GRANT SELECT ON current_weather_with_location TO root;
GRANT ALL PRIVILEGES ON SEQUENCE current_weather_data_id_seq TO root;
GRANT ALL PRIVILEGES ON SEQUENCE current_weather_collection_log_id_seq TO root;