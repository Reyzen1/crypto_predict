# File: ./backend/app/repositories/price_data.py
# Price data repository with specialized operations for historical price data

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from decimal import Decimal

from app.models import PriceData
from backend.app.repositories.base_repository import BaseRepository


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

    def get_by_timestamp(
        self, 
        db: Session, 
        crypto_id: int, 
        timestamp: datetime
    ) -> Optional[PriceData]:
        """
        Get price data for a specific timestamp
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            timestamp: Exact timestamp to search for
            
        Returns:
            PriceData object if found, None otherwise
        """
        return (
            db.query(PriceData)
            .filter(PriceData.crypto_id == crypto_id)
            .filter(PriceData.timestamp == timestamp)
            .first()
        )
    
    def get_by_crypto_and_timestamp(
        self, 
        db: Session, 
        crypto_id: int, 
        timestamp: datetime
    ) -> Optional[PriceData]:
        """
        Get price data for specific crypto and timestamp - alternative name
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            timestamp: Exact timestamp to search for
            
        Returns:
            PriceData object if found, None otherwise
        """
        return self.get_by_timestamp(db, crypto_id, timestamp)
    
    def exists_by_timestamp(
        self, 
        db: Session, 
        crypto_id: int, 
        timestamp: datetime
    ) -> bool:
        """
        Check if price data exists for specific timestamp
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            timestamp: Target timestamp
            
        Returns:
            True if data exists, False otherwise
        """
        return (
            db.query(PriceData)
            .filter(PriceData.crypto_id == crypto_id)
            .filter(PriceData.timestamp == timestamp)
            .first()
        ) is not None

# Create global instance
price_data_repository = PriceDataRepository()
