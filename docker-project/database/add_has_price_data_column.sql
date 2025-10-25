-- Add has_price_data column to cryptocurrencies table for performance optimization
-- This avoids expensive EXISTS queries against the compressed TimescaleDB hypertable

-- Step 1: Add the column
ALTER TABLE cryptocurrencies 
ADD COLUMN IF NOT EXISTS has_price_data BOOLEAN DEFAULT false;

-- Step 2: Populate the column with current data
-- This may take a few minutes due to the compressed hypertable
UPDATE cryptocurrencies c
SET has_price_data = true
WHERE EXISTS (
    SELECT 1 FROM crypto_prices cp 
    WHERE cp.crypto_id = c.id 
    LIMIT 1
);

-- Step 3: Create index for fast filtering
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_has_price_data 
ON cryptocurrencies(is_active, has_price_data) 
WHERE is_active = true AND has_price_data = true;

-- Step 4: Create function to update the flag when prices are inserted
CREATE OR REPLACE FUNCTION update_crypto_has_price_data()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the cryptocurrency to mark it as having price data
    UPDATE cryptocurrencies 
    SET has_price_data = true 
    WHERE id = NEW.crypto_id AND has_price_data = false;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 5: Create trigger to automatically maintain the flag
DROP TRIGGER IF EXISTS trigger_update_crypto_has_price_data ON crypto_prices;

CREATE TRIGGER trigger_update_crypto_has_price_data
    AFTER INSERT ON crypto_prices
    FOR EACH ROW
    EXECUTE FUNCTION update_crypto_has_price_data();

-- Verification query
SELECT 
    COUNT(*) FILTER (WHERE has_price_data = true) as cryptos_with_data,
    COUNT(*) FILTER (WHERE has_price_data = false) as cryptos_without_data,
    COUNT(*) as total_cryptos
FROM cryptocurrencies
WHERE is_active = true;
