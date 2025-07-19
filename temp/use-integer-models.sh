#!/bin/bash
# File: scripts/use-integer-models.sh
# Switch to Integer models to avoid UUID issues

echo "🔧 Switching to Integer Models"
echo "=============================="

echo "📝 Updating models to use Integer IDs..."

# Backup current models
cp backend/app/models/__init__.py backend/app/models/__init__.py.backup

# Create new models with Integer IDs
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

    # Relationships
    predictions = relationship("Prediction", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")


class Cryptocurrency(Base):
    """Cryptocurrency model for supported coins"""
    __tablename__ = "cryptocurrencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    coingecko_id = Column(String(50), nullable=True)
    binance_symbol = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    price_data = relationship("PriceData", back_populates="cryptocurrency")
    predictions = relationship("Prediction", back_populates="cryptocurrency")
    portfolios = relationship("Portfolio", back_populates="cryptocurrency")


class PriceData(Base):
    """Price data model for historical cryptocurrency prices"""
    __tablename__ = "price_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Numeric(20, 8), nullable=False)
    high_price = Column(Numeric(20, 8), nullable=False)
    low_price = Column(Numeric(20, 8), nullable=False)
    close_price = Column(Numeric(20, 8), nullable=False)
    volume = Column(Numeric(20, 8), nullable=False)
    market_cap = Column(Numeric(20, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="price_data")

    # Indexes for performance
    __table_args__ = (
        Index('idx_price_data_crypto_timestamp', 'crypto_id', 'timestamp'),
        Index('idx_price_data_timestamp', 'timestamp'),
    )


class Prediction(Base):
    """Predictions model for ML predictions"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    predicted_price = Column(Numeric(20, 8), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    model_version = Column(String(50), nullable=True)
    prediction_horizon = Column(Integer, nullable=True)
    prediction_date = Column(DateTime(timezone=True), server_default=func.now())
    target_date = Column(DateTime(timezone=True), nullable=False)
    actual_price = Column(Numeric(20, 8), nullable=True)
    is_accurate = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="predictions")
    cryptocurrency = relationship("Cryptocurrency", back_populates="predictions")

    # Indexes for performance
    __table_args__ = (
        Index('idx_predictions_user_crypto', 'user_id', 'crypto_id'),
        Index('idx_predictions_target_date', 'target_date'),
        Index('idx_predictions_created_at', 'created_at'),
    )


class Portfolio(Base):
    """Portfolio model for user cryptocurrency holdings"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    average_buy_price = Column(Numeric(20, 8), nullable=True)
    total_invested = Column(Numeric(20, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="portfolios")
    cryptocurrency = relationship("Cryptocurrency", back_populates="portfolios")

    # Unique constraint
    __table_args__ = (
        Index('idx_portfolios_user_crypto', 'user_id', 'crypto_id', unique=True),
    )


# Export models
__all__ = [
    "User",
    "Cryptocurrency", 
    "PriceData",
    "Prediction",
    "Portfolio"
]
EOF

echo "✅ Models updated to use Integer IDs!"

echo ""
echo "🏗️ Now creating tables..."
cd backend

# Activate virtual environment
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/cryptopredict"

# Try to create the database first
python -c "
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres123',
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE cryptopredict')
    print('✅ Database created!')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'⚠️ Database creation: {e}')
    print('Database might already exist, continuing...')
"

# Create tables
python -c "
from app.core.database import engine, Base
import app.models
Base.metadata.create_all(bind=engine)
print('✅ Tables created!')
"

# Seed data
python -c "
from app.core.database import SessionLocal
from app.models import Cryptocurrency

db = SessionLocal()
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
db.close()
print('🎉 Database seeding completed!')
"

cd ..

echo ""
echo "🎉 Database setup complete with Integer models!"
echo "=============================================="
echo ""
echo "Changes made:"
echo "  - Models now use Integer IDs instead of UUID"
echo "  - Database created or verified"
echo "  - Tables created"
echo "  - Data seeded"
echo ""
echo "Next: ./scripts/start-backend.sh"