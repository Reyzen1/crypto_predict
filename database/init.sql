-- File: ./database/init.sql
-- Database initialization script for CryptoPredict MVP
-- Creates necessary tables and initial data

-- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create cryptocurrencies table for supported coins
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    coingecko_id VARCHAR(50),
    binance_symbol VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create price_data table for historical crypto prices
CREATE TABLE IF NOT EXISTS price_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crypto_id UUID NOT NULL REFERENCES cryptocurrencies(id),
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    high_price DECIMAL(20, 8) NOT NULL,
    low_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on crypto_id and timestamp for faster queries
CREATE INDEX IF NOT EXISTS idx_price_data_crypto_timestamp ON price_data(crypto_id, timestamp);

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    crypto_id UUID NOT NULL REFERENCES cryptocurrencies(id),
    predicted_price DECIMAL(20, 8) NOT NULL,
    confidence_score DECIMAL(5, 4),
    model_version VARCHAR(50),
    prediction_horizon INTEGER, -- hours into the future
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_date TIMESTAMP NOT NULL,
    actual_price DECIMAL(20, 8), -- filled when target_date is reached
    is_accurate BOOLEAN, -- calculated after target_date
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for predictions
CREATE INDEX IF NOT EXISTS idx_predictions_user_crypto ON predictions(user_id, crypto_id);
CREATE INDEX IF NOT EXISTS idx_predictions_target_date ON predictions(target_date);

-- Create portfolio table for user holdings
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    crypto_id UUID NOT NULL REFERENCES cryptocurrencies(id),
    quantity DECIMAL(20, 8) NOT NULL,
    average_buy_price DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create unique constraint on user_id and crypto_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_portfolios_user_crypto ON portfolios(user_id, crypto_id);

-- Insert initial cryptocurrency data
INSERT INTO cryptocurrencies (symbol, name, coingecko_id, binance_symbol) VALUES
('BTC', 'Bitcoin', 'bitcoin', 'BTCUSDT'),
('ETH', 'Ethereum', 'ethereum', 'ETHUSDT'),
('ADA', 'Cardano', 'cardano', 'ADAUSDT'),
('DOT', 'Polkadot', 'polkadot', 'DOTUSDT'),
('LINK', 'Chainlink', 'chainlink', 'LINKUSDT')
ON CONFLICT (symbol) DO NOTHING;

-- Create a trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cryptocurrencies_updated_at BEFORE UPDATE ON cryptocurrencies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();