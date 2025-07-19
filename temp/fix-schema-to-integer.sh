# File: ./scripts/fix-schema-to-integer.sh
# Fix schema conflict by standardizing everything to Integer IDs

#!/bin/bash

set -e

echo "🔧 Fixing Schema Conflict → Integer IDs"
echo "======================================="

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi

echo "⚠️  This will:"
echo "   1. Drop all existing tables"
echo "   2. Recreate with Integer IDs" 
echo "   3. Update init.sql file"
echo "   4. Reseed initial data"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

cd backend

# Activate virtual environment
if [ -f "venv/Scripts/activate" ]; then
    echo "🔧 Activating virtual environment (Windows)..."
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment (Linux/Mac)..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    exit 1
fi

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/cryptopredict"

echo "🗑️  Step 1: Dropping existing tables..."
python -c "
from app.core.database import engine, Base
try:
    # Import all models to ensure they're registered
    import app.models
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print('✅ All tables dropped successfully!')
except Exception as e:
    print(f'⚠️  Drop tables error (might be OK): {e}')
"

echo "📝 Step 2: Creating new Integer-based models..."
cd ..

# Update the models file to ensure Integer IDs
cat > backend/app/models/__init__.py << 'EOF'
# File: ./backend/app/models/__init__.py
# Database models for CryptoPredict MVP - Integer ID version

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User model for authentication and user management"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - One user can have many predictions and portfolios
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Cryptocurrency(Base):
    """Cryptocurrency model for supported coins"""
    __tablename__ = "cryptocurrencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    coingecko_id = Column(String(50), nullable=True)  # For CoinGecko API integration
    binance_symbol = Column(String(20), nullable=True)  # For Binance API integration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - One crypto can have many price data, predictions, and portfolio entries
    price_data = relationship("PriceData", back_populates="cryptocurrency", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="cryptocurrency", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="cryptocurrency", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cryptocurrency(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"


class PriceData(Base):
    """Price data model for historical cryptocurrency prices"""
    __tablename__ = "price_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Numeric(20, 8), nullable=False)  # Opening price
    high_price = Column(Numeric(20, 8), nullable=False)  # Highest price
    low_price = Column(Numeric(20, 8), nullable=False)   # Lowest price
    close_price = Column(Numeric(20, 8), nullable=False) # Closing price
    volume = Column(Numeric(30, 8), nullable=True)       # Trading volume
    market_cap = Column(Numeric(30, 2), nullable=True)   # Market capitalization
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="price_data")

    # Indexes for performance optimization
    __table_args__ = (
        Index('idx_price_data_crypto_timestamp', 'crypto_id', 'timestamp'),
        Index('idx_price_data_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<PriceData(crypto_id={self.crypto_id}, timestamp='{self.timestamp}', close=${self.close_price})>"


class Prediction(Base):
    """Prediction model for ML model predictions"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    model_name = Column(String(50), nullable=False)        # Name of ML model used
    predicted_price = Column(Numeric(20, 8), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=True) # Confidence percentage (0-1)
    target_date = Column(DateTime(timezone=True), nullable=False) # When prediction is for
    features_used = Column(Text, nullable=True)            # JSON string of features used
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="predictions")
    cryptocurrency = relationship("Cryptocurrency", back_populates="predictions")

    # Indexes for performance optimization
    __table_args__ = (
        Index('idx_predictions_user_crypto', 'user_id', 'crypto_id'),
        Index('idx_predictions_target_date', 'target_date'),
        Index('idx_predictions_created_at', 'created_at'),
        Index('idx_predictions_model_name', 'model_name'),
    )

    def __repr__(self):
        return f"<Prediction(user_id={self.user_id}, crypto_id={self.crypto_id}, price=${self.predicted_price})>"


class Portfolio(Base):
    """Portfolio model for user cryptocurrency holdings"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)       # Amount of crypto held
    average_buy_price = Column(Numeric(20, 8), nullable=True) # Average purchase price
    total_invested = Column(Numeric(20, 2), nullable=True)   # Total amount invested
    notes = Column(Text, nullable=True)                      # User notes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="portfolios")
    cryptocurrency = relationship("Cryptocurrency", back_populates="portfolios")

    # Unique constraint - One portfolio entry per user per crypto
    __table_args__ = (
        Index('idx_portfolios_user_crypto', 'user_id', 'crypto_id', unique=True),
    )

    def __repr__(self):
        return f"<Portfolio(user_id={self.user_id}, crypto_id={self.crypto_id}, quantity={self.quantity})>"


# Export all models for easy importing
__all__ = [
    "User",
    "Cryptocurrency", 
    "PriceData",
    "Prediction",
    "Portfolio"
]
EOF

echo "📝 Step 3: Updating database init.sql..."

# Create new database/init.sql with Integer IDs
cat > database/init.sql << 'EOF'
-- File: ./database/init.sql
-- Database initialization script for CryptoPredict MVP
-- Using Integer IDs for better performance and simplicity

-- Create database if it doesn't exist (handled by Docker)
-- This file runs when the database container starts for the first time

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create cryptocurrencies table
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    coingecko_id VARCHAR(50),
    binance_symbol VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create price_data table
CREATE TABLE IF NOT EXISTS price_data (
    id SERIAL PRIMARY KEY,
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    high_price DECIMAL(20, 8) NOT NULL,
    low_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(30, 8),
    market_cap DECIMAL(30, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    model_name VARCHAR(50) NOT NULL,
    predicted_price DECIMAL(20, 8) NOT NULL,
    confidence_score DECIMAL(5, 4),
    target_date TIMESTAMP WITH TIME ZONE NOT NULL,
    features_used TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    quantity DECIMAL(20, 8) NOT NULL,
    average_buy_price DECIMAL(20, 8),
    total_invested DECIMAL(20, 2),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, crypto_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_symbol ON cryptocurrencies(symbol);
CREATE INDEX IF NOT EXISTS idx_price_data_crypto_timestamp ON price_data(crypto_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_user_crypto ON predictions(user_id, crypto_id);
CREATE INDEX IF NOT EXISTS idx_predictions_target_date ON predictions(target_date);
CREATE INDEX IF NOT EXISTS idx_portfolios_user_crypto ON portfolios(user_id, crypto_id);

-- Insert initial cryptocurrency data
INSERT INTO cryptocurrencies (symbol, name, coingecko_id, binance_symbol) VALUES
    ('BTC', 'Bitcoin', 'bitcoin', 'BTCUSDT'),
    ('ETH', 'Ethereum', 'ethereum', 'ETHUSDT'),
    ('ADA', 'Cardano', 'cardano', 'ADAUSDT'),
    ('DOT', 'Polkadot', 'polkadot', 'DOTUSDT'),
    ('LINK', 'Chainlink', 'chainlink', 'LINKUSDT')
ON CONFLICT (symbol) DO NOTHING;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DO $$
BEGIN
    -- Drop triggers if they exist
    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    DROP TRIGGER IF EXISTS update_cryptocurrencies_updated_at ON cryptocurrencies;
    DROP TRIGGER IF EXISTS update_portfolios_updated_at ON portfolios;
    
    -- Create triggers
    CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
    CREATE TRIGGER update_cryptocurrencies_updated_at BEFORE UPDATE ON cryptocurrencies
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        
    CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
END
$$;
EOF

echo "🏗️  Step 4: Recreating tables with Integer IDs..."
cd backend

python -c "
from app.core.database import engine, Base
import app.models

# Create all tables with Integer IDs
Base.metadata.create_all(bind=engine)
print('✅ Tables recreated with Integer IDs!')
"

echo "🌱 Step 5: Seeding initial data..."
python -c "
from app.core.database import SessionLocal
from app.models import Cryptocurrency

db = SessionLocal()

try:
    # Check if data already exists
    existing_count = db.query(Cryptocurrency).count()
    if existing_count > 0:
        print('⚠️  Data already exists. Skipping seeding.')
    else:
        cryptos = [
            {'symbol': 'BTC', 'name': 'Bitcoin', 'coingecko_id': 'bitcoin', 'binance_symbol': 'BTCUSDT'},
            {'symbol': 'ETH', 'name': 'Ethereum', 'coingecko_id': 'ethereum', 'binance_symbol': 'ETHUSDT'},
            {'symbol': 'ADA', 'name': 'Cardano', 'coingecko_id': 'cardano', 'binance_symbol': 'ADAUSDT'},
            {'symbol': 'DOT', 'name': 'Polkadot', 'coingecko_id': 'polkadot', 'binance_symbol': 'DOTUSDT'},
            {'symbol': 'LINK', 'name': 'Chainlink', 'coingecko_id': 'chainlink', 'binance_symbol': 'LINKUSDT'}
        ]
        
        for crypto_data in cryptos:
            crypto = Cryptocurrency(**crypto_data)
            db.add(crypto)
            print(f'✅ Added {crypto_data[\"name\"]} ({crypto_data[\"symbol\"]})')
        
        db.commit()
        print('🎉 Database seeding completed!')
finally:
    db.close()
"

cd ..

echo ""
echo "🎉 Schema Conflict Fixed!"
echo "========================"
echo ""
echo "✅ Database schema: Integer IDs"
echo "✅ Models schema: Integer IDs" 
echo "✅ Init.sql: Integer IDs"
echo "✅ Initial data: Seeded"
echo ""
echo "🚀 Ready to continue Day 3 development!"