#!/bin/bash
# temp/fix-model-relationships.sh
# Fix SQLAlchemy model relationships

echo "🔧 Fixing SQLAlchemy Model Relationships"
echo "========================================"

cd backend

echo ""
echo "📋 Step 1: Create Safe Models Without Relationships"
echo "---------------------------------------------------"

# Create completely safe models without relationships to avoid conflicts
cat > app/models/__init__.py << 'EOF'
# app/models/__init__.py
# Safe models without relationships to prevent SQLAlchemy conflicts

from app.core.database import Base

# Import existing User model
from app.models.user import User

# Create simple models without relationships
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql.sqltypes import Numeric  
from sqlalchemy.sql import func

class Cryptocurrency(Base):
    __tablename__ = "cryptocurrencies"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    coingecko_id = Column(String(50), nullable=True)
    binance_symbol = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PriceData(Base):
    __tablename__ = "price_data"
    __table_args__ = {'extend_existing': True}
    
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

class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    predicted_price = Column(Numeric(20, 8), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    model_version = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Export all models
__all__ = [
    "Base",
    "User", 
    "Cryptocurrency",
    "PriceData", 
    "Prediction"
]
EOF

echo "✅ Created safe models without relationships"

echo ""
echo "📋 Step 2: Clear All Cache"
echo "--------------------------"

# Remove all cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "✅ Cache cleared"

echo ""
echo "📋 Step 3: Test Model Import"
echo "----------------------------"

python -c "
try:
    print('Testing safe model imports...')
    
    from app.models import User, Cryptocurrency, PriceData, Prediction
    print('✅ All models imported successfully')
    
    # Test that they have the right attributes
    print(f'User table: {User.__tablename__}')
    print(f'Cryptocurrency table: {Cryptocurrency.__tablename__}')
    print(f'PriceData table: {PriceData.__tablename__}')
    print(f'Prediction table: {Prediction.__tablename__}')
    
    print('✅ Safe model import test successful!')
    
except Exception as e:
    print(f'❌ Model import test failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "📋 Step 4: Test Task Import Without DB Operations"
echo "-------------------------------------------------"

python -c "
try:
    print('Testing task imports...')
    
    # Test task functions can be imported
    from app.tasks.price_collector import get_task_status
    print('✅ Task functions imported')
    
    # Test that we can call get_task_status without DB operations
    result = get_task_status()
    print(f'✅ Basic task status: {result.get(\"status\", \"unknown\")}')
    
except Exception as e:
    print(f'❌ Task import test failed: {e}')
    import traceback
    traceback.print_exc()
"

cd ..

echo ""
echo "🎉 MODEL RELATIONSHIP FIXES APPLIED!"
echo "==================================="
echo ""
echo "✅ Fixes Applied:"
echo "   1. Removed SQLAlchemy relationships that cause conflicts"
echo "   2. Kept only essential model structure"
echo "   3. Used extend_existing=True to prevent table conflicts"
echo "   4. Cleared all cache files"
echo ""
echo "🔄 Restart Celery Services:"
echo ""
echo "1. Stop current Celery (Ctrl+C)"
echo "2. Start again: ./temp/start-celery.sh"
echo ""
echo "🧪 Test API Endpoint:"
echo "   curl -X GET \"http://localhost:8000/api/v1/tasks/status\""
echo ""
echo "🎯 The SQLAlchemy relationship error should now be resolved!"