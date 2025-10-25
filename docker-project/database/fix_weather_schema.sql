-- Fix Weather Schema Inconsistencies
-- This script fixes the data type mismatches in weather tables

-- Begin transaction
BEGIN;

-- 1. First, let's check what we're working with
\echo 'Current schema analysis:'
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name IN ('users', 'weather_locations', 'historic_weather_data', 'current_weather_data')
    AND column_name IN ('id', 'user_id', 'weather_location_id')
ORDER BY table_name, column_name;

-- 2. Drop foreign key constraints that will be affected
\echo 'Dropping foreign key constraints...'
ALTER TABLE weather_locations DROP CONSTRAINT IF EXISTS weather_locations_user_id_fkey;
ALTER TABLE historic_weather_data DROP CONSTRAINT IF EXISTS historic_weather_data_weather_location_id_fkey;
ALTER TABLE current_weather_data DROP CONSTRAINT IF EXISTS current_weather_data_weather_location_id_fkey;
ALTER TABLE historic_weather_collection_log DROP CONSTRAINT IF EXISTS historic_weather_collection_log_weather_location_id_fkey;
ALTER TABLE current_weather_collection_log DROP CONSTRAINT IF EXISTS current_weather_collection_log_weather_location_id_fkey;

-- 3. Fix weather_locations.user_id to be UUID to match users.id
\echo 'Converting weather_locations.user_id from INTEGER to UUID...'
ALTER TABLE weather_locations ALTER COLUMN user_id TYPE UUID USING user_id::text::uuid;

-- 4. Fix historic_weather_data.weather_location_id to be INTEGER to match weather_locations.id
\echo 'Converting historic_weather_data.weather_location_id from UUID to INTEGER...'
ALTER TABLE historic_weather_data ALTER COLUMN weather_location_id TYPE INTEGER USING weather_location_id::text::integer;

-- 5. Fix historic_weather_collection_log.weather_location_id to be INTEGER
\echo 'Converting historic_weather_collection_log.weather_location_id from UUID to INTEGER...'
ALTER TABLE historic_weather_collection_log ALTER COLUMN weather_location_id TYPE INTEGER USING weather_location_id::text::integer;

-- 6. Recreate foreign key constraints with correct types
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

ALTER TABLE historic_weather_collection_log 
    ADD CONSTRAINT historic_weather_collection_log_weather_location_id_fkey 
    FOREIGN KEY (weather_location_id) REFERENCES weather_locations(id) ON DELETE CASCADE;

ALTER TABLE current_weather_collection_log 
    ADD CONSTRAINT current_weather_collection_log_weather_location_id_fkey 
    FOREIGN KEY (weather_location_id) REFERENCES weather_locations(id) ON DELETE CASCADE;

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

-- 8. Verify the final schema
\echo 'Final schema verification:'
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name IN ('users', 'weather_locations', 'historic_weather_data', 'current_weather_data')
    AND column_name IN ('id', 'user_id', 'weather_location_id')
ORDER BY table_name, column_name;

-- 9. Show summary of current data
\echo 'Data summary after fix:'
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
FROM historic_weather_data
UNION ALL
SELECT 
    'current_weather_data' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT weather_location_id) as unique_locations,
    COUNT(DISTINCT recorded_at) as unique_timestamps
FROM current_weather_data;

COMMIT;

\echo 'Weather schema fix completed successfully!'