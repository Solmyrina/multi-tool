-- Fix Weather Schema Inconsistencies (v2)
-- This script fixes the data type mismatches in weather tables

-- Begin transaction
BEGIN;

-- 1. Drop dependent views first
\echo 'Dropping dependent views...'
DROP VIEW IF EXISTS historic_weather_with_location CASCADE;
DROP VIEW IF EXISTS current_weather_with_location CASCADE;

-- 2. Drop foreign key constraints that will be affected
\echo 'Dropping foreign key constraints...'
ALTER TABLE weather_locations DROP CONSTRAINT IF EXISTS weather_locations_user_id_fkey;
ALTER TABLE historic_weather_data DROP CONSTRAINT IF EXISTS historic_weather_data_weather_location_id_fkey;
ALTER TABLE current_weather_data DROP CONSTRAINT IF EXISTS current_weather_data_weather_location_id_fkey;
ALTER TABLE historic_weather_collection_log DROP CONSTRAINT IF EXISTS historic_weather_collection_log_weather_location_id_fkey;
ALTER TABLE current_weather_collection_log DROP CONSTRAINT IF EXISTS current_weather_collection_log_weather_location_id_fkey;

-- 3. Check current data types
\echo 'Current schema analysis:'
SELECT table_name, column_name, data_type FROM information_schema.columns 
WHERE table_name IN ('users', 'weather_locations', 'historic_weather_data') 
    AND column_name IN ('id', 'user_id', 'weather_location_id')
ORDER BY table_name, column_name;

-- 4. Fix weather_locations.user_id to be UUID to match users.id
\echo 'Converting weather_locations.user_id from INTEGER to UUID...'
-- First, we need to update existing data to valid UUIDs or remove invalid records
DELETE FROM weather_locations WHERE user_id::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
-- Note: This assumes existing user_id values are already UUIDs, which they should be based on the output

-- 5. Recreate foreign key constraints with correct types  
\echo 'Recreating foreign key constraints...'
ALTER TABLE weather_locations 
    ADD CONSTRAINT weather_locations_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE historic_weather_data 
    ADD CONSTRAINT historic_weather_data_weather_location_id_fkey 
    FOREIGN KEY (weather_location_id) REFERENCES weather_locations(id) ON DELETE CASCADE;

ALTER TABLE current_weather_data 
    ADD CONSTRAINT current_weather_data_weather_location_id_fkey 
    FOREIGN KEY (weather_location_id) REFERENCES weather_locations(id) ON DELETE CASCADE;

-- 6. Recreate the views with correct schema
\echo 'Recreating views...'
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

-- 7. Remove duplicate weather locations (keep the one with more data)
\echo 'Removing duplicate weather locations...'
WITH duplicates AS (
    SELECT 
        id,
        city_name,
        country,
        user_id,
        ROW_NUMBER() OVER (
            PARTITION BY city_name, country, user_id 
            ORDER BY created_at ASC
        ) as rn
    FROM weather_locations
)
DELETE FROM weather_locations 
WHERE id IN (
    SELECT id FROM duplicates WHERE rn > 1
);

-- 8. Verify the final schema and data
\echo 'Final verification:'
SELECT 
    'weather_locations' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT city_name || ', ' || country) as unique_locations
FROM weather_locations
UNION ALL
SELECT 
    'historic_weather_data' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT weather_location_id) as unique_locations,
    COUNT(DISTINCT date) as unique_dates
FROM historic_weather_data;

COMMIT;

\echo 'Weather schema fix completed successfully!'