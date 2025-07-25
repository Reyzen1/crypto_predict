-- Quick fix for prediction table issues
-- File: temp/fix_prediction_table.sql

-- Add model_version column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'predictions' 
        AND column_name = 'model_version'
    ) THEN
        ALTER TABLE predictions 
        ADD COLUMN model_version VARCHAR(20) NOT NULL DEFAULT '1.0';
        
        COMMENT ON COLUMN predictions.model_version IS 'Version of the ML model used';
        
        RAISE NOTICE 'Added model_version column to predictions table';
    ELSE
        RAISE NOTICE 'model_version column already exists';
    END IF;
END $$;

-- Verify the fix
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'predictions' 
AND column_name = 'model_version';
