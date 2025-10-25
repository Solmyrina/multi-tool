-- Historic Weather Data Tables
-- This file creates tables for storing daily historic weather data

-- Table for storing daily historic weather records
CREATE TABLE IF NOT EXISTS historic_weather_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    weather_location_id UUID NOT NULL REFERENCES weather_locations(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    temperature_min DECIMAL(5,2), -- Minimum temperature in Celsius
    temperature_max DECIMAL(5,2), -- Maximum temperature in Celsius
    temperature_avg DECIMAL(5,2), -- Average temperature in Celsius
    humidity_avg DECIMAL(5,2), -- Average humidity percentage
    pressure_avg DECIMAL(8,2), -- Average pressure in hPa
    wind_speed_avg DECIMAL(6,2), -- Average wind speed in m/s
    wind_speed_max DECIMAL(6,2), -- Maximum wind speed in m/s
    wind_direction_avg INTEGER, -- Average wind direction in degrees
    precipitation_total DECIMAL(8,2), -- Total precipitation in mm
    cloud_cover_avg DECIMAL(5,2), -- Average cloud cover percentage
    weather_symbol VARCHAR(50), -- Primary weather symbol for the day
    sunrise_time TIME, -- Sunrise time (local)
    sunset_time TIME, -- Sunset time (local)
    data_source VARCHAR(100) NOT NULL DEFAULT 'unknown', -- Source of the weather data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one record per location per date
    UNIQUE(weather_location_id, date)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_historic_weather_location_id ON historic_weather_data(weather_location_id);
CREATE INDEX IF NOT EXISTS idx_historic_weather_date ON historic_weather_data(date);
CREATE INDEX IF NOT EXISTS idx_historic_weather_location_date ON historic_weather_data(weather_location_id, date);
CREATE INDEX IF NOT EXISTS idx_historic_weather_date_range ON historic_weather_data(date DESC, weather_location_id);

-- Table for tracking data collection progress
CREATE TABLE IF NOT EXISTS historic_weather_collection_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    weather_location_id UUID NOT NULL REFERENCES weather_locations(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, failed
    records_collected INTEGER DEFAULT 0,
    error_message TEXT,
    data_source VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for collection log
CREATE INDEX IF NOT EXISTS idx_collection_log_location ON historic_weather_collection_log(weather_location_id);
CREATE INDEX IF NOT EXISTS idx_collection_log_status ON historic_weather_collection_log(status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic updated_at timestamps
CREATE TRIGGER update_historic_weather_updated_at 
    BEFORE UPDATE ON historic_weather_data 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collection_log_updated_at 
    BEFORE UPDATE ON historic_weather_collection_log 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View for easy querying of historic weather with location details
CREATE OR REPLACE VIEW historic_weather_with_location AS
SELECT 
    hwd.*,
    wl.city_name,
    wl.country,
    wl.latitude,
    wl.longitude,
    wl.user_id
FROM historic_weather_data hwd
JOIN weather_locations wl ON hwd.weather_location_id = wl.id;

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON historic_weather_data TO root;
GRANT SELECT, INSERT, UPDATE, DELETE ON historic_weather_collection_log TO root;
GRANT SELECT ON historic_weather_with_location TO root;