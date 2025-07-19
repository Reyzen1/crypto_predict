# File: ./scripts/setup-repositories.sh
# Setup repository pattern structure and create all repository files

#!/bin/bash

set -e

echo "🏗️ Setting Up Repository Pattern Structure"
echo "=========================================="

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi

echo "📁 Creating repositories directory structure..."
mkdir -p backend/app/repositories

echo "✅ Repository directory created"

echo ""
echo "📝 Creating repository files..."

# Create base repository
echo "Creating base repository..."
cat > backend/app/repositories/base.py << 'EOF'
# File: ./backend/app/repositories/base.py
# Base repository class with common CRUD operations

from typing import Type, TypeVar, Generic, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from pydantic import BaseModel

from app.core.database import Base

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository class providing common CRUD operations
    
    This implements the Repository Pattern to abstract database operations
    and provide a clean interface for data access
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with the model class
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "id",
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and ordering
        
        Args:
            db: Database session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            order_by: Column name to order by
            order_desc: Whether to order in descending order
            
        Returns:
            List of model instances
        """
        query = db.query(self.model)
        
        # Apply ordering
        if hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))
        
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record
        
        Args:
            db: Database session
            obj_in: Pydantic schema with data to create
            
        Returns:
            Created model instance
        """
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump(exclude_unset=True)
        
        db_obj = self.model(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """
        Update an existing record
        
        Args:
            db: Database session
            db_obj: Existing model instance to update
            obj_in: Pydantic schema or dict with update data
            
        Returns:
            Updated model instance
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Delete a record by ID
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            Deleted model instance or None if not found
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def get_by_field(
        self, 
        db: Session, 
        field_name: str, 
        field_value: Any
    ) -> Optional[ModelType]:
        """
        Get a single record by any field
        
        Args:
            db: Database session
            field_name: Name of the field to filter by
            field_value: Value to filter for
            
        Returns:
            Model instance or None if not found
        """
        if hasattr(self.model, field_name):
            field = getattr(self.model, field_name)
            return db.query(self.model).filter(field == field_value).first()
        return None

    def count(self, db: Session) -> int:
        """
        Get total count of records
        
        Args:
            db: Database session
            
        Returns:
            Total number of records
        """
        return db.query(self.model).count()

    def exists(self, db: Session, id: int) -> bool:
        """
        Check if a record exists by ID
        
        Args:
            db: Database session
            id: Primary key value
            
        Returns:
            True if record exists, False otherwise
        """
        return db.query(self.model).filter(self.model.id == id).first() is not None
EOF

# Create user repository
echo "Creating user repository..."
cat > backend/app/repositories/user.py << 'EOF'
# File: ./backend/app/repositories/user.py
# User repository with specialized user operations

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, dict, dict]):
    """
    User repository with specialized operations for user management
    """

    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email address"""
        return db.query(User).filter(User.email == email).first()

    def get_active_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        return (
            db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_user(
        self, 
        db: Session, 
        *, 
        email: str, 
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False
    ) -> User:
        """Create a new user with validation"""
        # Check if email already exists
        existing_user = self.get_by_email(db, email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")
        
        user_data = {
            "email": email,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": is_active,
            "is_verified": is_verified
        }
        
        return self.create(db, obj_in=user_data)

    def verify_user(self, db: Session, user_id: int) -> Optional[User]:
        """Mark user as verified"""
        user = self.get(db, user_id)
        if user:
            return self.update(db, db_obj=user, obj_in={"is_verified": True})
        return None

    def count_active_users(self, db: Session) -> int:
        """Count total number of active users"""
        return db.query(User).filter(User.is_active == True).count()

    def search_users(self, db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by email, first name, or last name"""
        return (
            db.query(User)
            .filter(
                User.email.ilike(f"%{search_term}%") |
                User.first_name.ilike(f"%{search_term}%") |
                User.last_name.ilike(f"%{search_term}%")
            )
            .offset(skip)
            .limit(limit)
            .all()
        )


# Create global instance
user_repository = UserRepository()
EOF

# Create cryptocurrency repository
echo "Creating cryptocurrency repository..."
cat > backend/app/repositories/cryptocurrency.py << 'EOF'
# File: ./backend/app/repositories/cryptocurrency.py
# Cryptocurrency repository with specialized crypto operations

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import Cryptocurrency, PriceData
from app.repositories.base import BaseRepository


class CryptocurrencyRepository(BaseRepository[Cryptocurrency, dict, dict]):
    """
    Cryptocurrency repository with specialized operations for crypto management
    """

    def __init__(self):
        super().__init__(Cryptocurrency)

    def get_by_symbol(self, db: Session, symbol: str) -> Optional[Cryptocurrency]:
        """Get cryptocurrency by symbol (e.g., 'BTC', 'ETH')"""
        return db.query(Cryptocurrency).filter(
            Cryptocurrency.symbol.upper() == symbol.upper()
        ).first()

    def get_active_cryptos(self, db: Session, skip: int = 0, limit: int = 100) -> List[Cryptocurrency]:
        """Get all active cryptocurrencies"""
        return (
            db.query(Cryptocurrency)
            .filter(Cryptocurrency.is_active == True)
            .order_by(Cryptocurrency.symbol)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_coingecko_id(self, db: Session, coingecko_id: str) -> Optional[Cryptocurrency]:
        """Get cryptocurrency by CoinGecko ID"""
        return db.query(Cryptocurrency).filter(
            Cryptocurrency.coingecko_id == coingecko_id
        ).first()

    def create_crypto(
        self, 
        db: Session, 
        *, 
        symbol: str,
        name: str,
        coingecko_id: Optional[str] = None,
        binance_symbol: Optional[str] = None,
        is_active: bool = True
    ) -> Cryptocurrency:
        """Create a new cryptocurrency with validation"""
        # Check if symbol already exists
        existing_crypto = self.get_by_symbol(db, symbol)
        if existing_crypto:
            raise ValueError(f"Cryptocurrency with symbol {symbol} already exists")
        
        crypto_data = {
            "symbol": symbol.upper(),
            "name": name,
            "coingecko_id": coingecko_id,
            "binance_symbol": binance_symbol,
            "is_active": is_active
        }
        
        return self.create(db, obj_in=crypto_data)

    def deactivate_crypto(self, db: Session, crypto_id: int) -> Optional[Cryptocurrency]:
        """Deactivate cryptocurrency"""
        crypto = self.get(db, crypto_id)
        if crypto:
            return self.update(db, db_obj=crypto, obj_in={"is_active": False})
        return None

    def get_crypto_with_latest_price(self, db: Session, crypto_id: int) -> Optional[dict]:
        """Get cryptocurrency with its latest price data"""
        crypto = self.get(db, crypto_id)
        if not crypto:
            return None
        
        # Get latest price data
        latest_price = (
            db.query(PriceData)
            .filter(PriceData.crypto_id == crypto_id)
            .order_by(desc(PriceData.timestamp))
            .first()
        )
        
        return {
            "cryptocurrency": crypto,
            "latest_price": latest_price
        }

    def count_active_cryptos(self, db: Session) -> int:
        """Count total number of active cryptocurrencies"""
        return db.query(Cryptocurrency).filter(Cryptocurrency.is_active == True).count()

    def search_cryptos(self, db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[Cryptocurrency]:
        """Search cryptocurrencies by symbol or name"""
        return (
            db.query(Cryptocurrency)
            .filter(
                Cryptocurrency.symbol.ilike(f"%{search_term}%") |
                Cryptocurrency.name.ilike(f"%{search_term}%")
            )
            .offset(skip)
            .limit(limit)
            .all()
        )


# Create global instance
cryptocurrency_repository = CryptocurrencyRepository()
EOF

# Create price data repository
echo "Creating price data repository..."
cat > backend/app/repositories/price_data.py << 'EOF'
# File: ./backend/app/repositories/price_data.py
# Price data repository with specialized operations for historical price data

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from decimal import Decimal

from app.models import PriceData
from app.repositories.base import BaseRepository


class PriceDataRepository(BaseRepository[PriceData, dict, dict]):
    """
    Price data repository with specialized operations for price data management
    """

    def __init__(self):
        super().__init__(PriceData)

    def get_latest_price(self, db: Session, crypto_id: int) -> Optional[PriceData]:
        """Get the most recent price data for a cryptocurrency"""
        return (
            db.query(PriceData)
            .filter(PriceData.crypto_id == crypto_id)
            .order_by(desc(PriceData.timestamp))
            .first()
        )

    def get_price_history(
        self, 
        db: Session, 
        crypto_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[PriceData]:
        """Get historical price data for a cryptocurrency within date range"""
        query = db.query(PriceData).filter(PriceData.crypto_id == crypto_id)
        
        if start_date:
            query = query.filter(PriceData.timestamp >= start_date)
        if end_date:
            query = query.filter(PriceData.timestamp <= end_date)
        
        return (
            query.order_by(asc(PriceData.timestamp))
            .limit(limit)
            .all()
        )

    def add_price_data(
        self, 
        db: Session,
        crypto_id: int,
        timestamp: datetime,
        open_price: Decimal,
        high_price: Decimal,
        low_price: Decimal,
        close_price: Decimal,
        volume: Optional[Decimal] = None,
        market_cap: Optional[Decimal] = None
    ) -> PriceData:
        """Add new price data entry"""
        price_data = {
            "crypto_id": crypto_id,
            "timestamp": timestamp,
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "close_price": close_price,
            "volume": volume,
            "market_cap": market_cap
        }
        
        return self.create(db, obj_in=price_data)

    def get_daily_statistics(self, db: Session, crypto_id: int, days: int = 30) -> Dict[str, Any]:
        """Get daily statistics for a cryptocurrency"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get aggregated statistics
        stats = (
            db.query(
                func.avg(PriceData.close_price).label('avg_price'),
                func.min(PriceData.low_price).label('min_price'),
                func.max(PriceData.high_price).label('max_price'),
                func.sum(PriceData.volume).label('total_volume'),
                func.count(PriceData.id).label('data_points')
            )
            .filter(PriceData.crypto_id == crypto_id)
            .filter(PriceData.timestamp >= start_date)
            .first()
        )
        
        latest_price = self.get_latest_price(db, crypto_id)
        
        return {
            "period_days": days,
            "avg_price": float(stats.avg_price) if stats.avg_price else 0.0,
            "min_price": float(stats.min_price) if stats.min_price else 0.0,
            "max_price": float(stats.max_price) if stats.max_price else 0.0,
            "total_volume": float(stats.total_volume) if stats.total_volume else 0.0,
            "data_points": stats.data_points or 0,
            "latest_price": float(latest_price.close_price) if latest_price else 0.0
        }

    def get_price_data_for_ml(self, db: Session, crypto_id: int, days_back: int = 365) -> List[Dict[str, Any]]:
        """Get price data formatted for ML model training"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        price_data = self.get_price_history(db, crypto_id, start_date, end_date)
        
        ml_data = []
        for data in price_data:
            ml_data.append({
                "timestamp": data.timestamp,
                "open": float(data.open_price),
                "high": float(data.high_price),
                "low": float(data.low_price),
                "close": float(data.close_price),
                "volume": float(data.volume) if data.volume else 0.0,
                "market_cap": float(data.market_cap) if data.market_cap else 0.0
            })
        
        return ml_data

    def count_by_crypto(self, db: Session, crypto_id: int) -> int:
        """Count total price data records for a cryptocurrency"""
        return db.query(PriceData).filter(PriceData.crypto_id == crypto_id).count()

    def check_data_availability(self, db: Session, crypto_id: int) -> Dict[str, Any]:
        """Check data availability and quality for a cryptocurrency"""
        total_count = self.count_by_crypto(db, crypto_id)
        
        if total_count == 0:
            return {
                "total_records": 0,
                "date_range": None,
                "data_quality": "No data available"
            }
        
        # Get date range
        first_record = (
            db.query(PriceData)
            .filter(PriceData.crypto_id == crypto_id)
            .order_by(asc(PriceData.timestamp))
            .first()
        )
        
        last_record = self.get_latest_price(db, crypto_id)
        
        return {
            "total_records": total_count,
            "date_range": {
                "start": first_record.timestamp if first_record else None,
                "end": last_record.timestamp if last_record else None
            },
            "data_quality": "Good" if total_count > 100 else "Limited"
        }


# Create global instance
price_data_repository = PriceDataRepository()
EOF

# Create repository package init
echo "Creating repository package __init__.py..."
cat > backend/app/repositories/__init__.py << 'EOF'
# File: ./backend/app/repositories/__init__.py
# Repository package initialization - exports all repositories

from app.repositories.base import BaseRepository
from app.repositories.user import UserRepository, user_repository
from app.repositories.cryptocurrency import CryptocurrencyRepository, cryptocurrency_repository
from app.repositories.price_data import PriceDataRepository, price_data_repository

# Export all repository classes
__all__ = [
    # Base repository
    "BaseRepository",
    
    # Repository classes
    "UserRepository",
    "CryptocurrencyRepository", 
    "PriceDataRepository",
    
    # Repository instances (ready to use)
    "user_repository",
    "cryptocurrency_repository",
    "price_data_repository"
]
EOF

echo ""
echo "✅ All repository files created successfully!"

echo ""
echo "📋 Created Files:"
echo "   ✅ backend/app/repositories/base.py"
echo "   ✅ backend/app/repositories/user.py"
echo "   ✅ backend/app/repositories/cryptocurrency.py"
echo "   ✅ backend/app/repositories/price_data.py"
echo "   ✅ backend/app/repositories/__init__.py"

echo ""
echo "🎯 Next Steps:"
echo "1. Run verification script: ./scripts/verify-schema-fix.sh"
echo "2. Run repository tests: ./scripts/test-repositories.sh"

echo ""
echo "🎉 Repository Pattern Implementation Complete!"