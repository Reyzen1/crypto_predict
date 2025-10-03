# backend/app/repositories/asset/price_data.py
# Repository for price data management

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta

from ..base import BaseRepository
from ...models.asset.price_data import PriceData
from ...models.asset import Asset


class PriceDataRepository(BaseRepository):
    """
    Repository for cryptocurrency price data management
    """
    
    def __init__(self, db: Session):
        super().__init__(PriceData, db)
    
    def get_by_asset(self, asset_id: int, limit: int = 100) -> List[PriceData]:
        """Get recent price data for an asset"""
        return self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id
        ).order_by(PriceData.timestamp.desc()).limit(limit).all()
    
    def get_by_symbol(self, symbol: str, limit: int = 100) -> List[PriceData]:
        """Get recent price data by symbol"""
        return self.db.query(PriceData).join(Asset).filter(
            Asset.symbol == symbol
        ).order_by(PriceData.timestamp.desc()).limit(limit).all()
    
    def get_price_range(self, asset_id: int, start_date: datetime, end_date: datetime) -> List[PriceData]:
        """Get price data within date range"""
        return self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= start_date,
            PriceData.timestamp <= end_date
        ).order_by(PriceData.timestamp.asc()).all()
    
    def get_latest_by_asset(self, asset_id: int) -> Optional[PriceData]:
        """Get latest price for an asset"""
        return self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id
        ).order_by(PriceData.timestamp.desc()).first()
    
    def get_ohlc_data(self, asset_id: int, hours: int = 24) -> List[PriceData]:
        """Get OHLC data for specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= cutoff_time
        ).order_by(PriceData.timestamp.asc()).all()
    
    def get_price_statistics(self, asset_id: int, days: int = 30) -> Dict[str, Any]:
        """Get price statistics for an asset"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stats = self.db.query(
            func.max(PriceData.price).label('max_price'),
            func.min(PriceData.price).label('min_price'),
            func.avg(PriceData.price).label('avg_price'),
            func.sum(PriceData.volume).label('total_volume'),
            func.count(PriceData.id).label('data_points')
        ).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= cutoff_date
        ).first()
        
        if not stats:
            return {}
        
        return {
            'max_price': float(stats.max_price) if stats.max_price else 0,
            'min_price': float(stats.min_price) if stats.min_price else 0,
            'avg_price': float(stats.avg_price) if stats.avg_price else 0,
            'total_volume': float(stats.total_volume) if stats.total_volume else 0,
            'data_points': stats.data_points or 0,
            'price_volatility': self._calculate_volatility(asset_id, days)
        }
    
    def _calculate_volatility(self, asset_id: int, days: int) -> float:
        """Calculate price volatility"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        prices = self.db.query(PriceData.price).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= cutoff_date
        ).order_by(PriceData.timestamp.asc()).all()
        
        if len(prices) < 2:
            return 0.0
        
        price_list = [float(p.price) for p in prices]
        returns = [(price_list[i] - price_list[i-1]) / price_list[i-1] for i in range(1, len(price_list))]
        
        if not returns:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return variance ** 0.5
    
    def get_missing_data_gaps(self, asset_id: int, expected_interval_minutes: int = 5) -> List[Dict[str, Any]]:
        """Identify gaps in price data"""
        recent_data = self.db.query(PriceData.timestamp).filter(
            PriceData.asset_id == asset_id
        ).order_by(PriceData.timestamp.desc()).limit(1000).all()
        
        if len(recent_data) < 2:
            return []
        
        gaps = []
        timestamps = [d.timestamp for d in reversed(recent_data)]
        expected_delta = timedelta(minutes=expected_interval_minutes)
        
        for i in range(1, len(timestamps)):
            actual_gap = timestamps[i] - timestamps[i-1]
            if actual_gap > expected_delta * 1.5:  # Allow 50% tolerance
                gaps.append({
                    'start': timestamps[i-1].isoformat(),
                    'end': timestamps[i].isoformat(),
                    'duration_minutes': actual_gap.total_seconds() / 60,
                    'expected_minutes': expected_interval_minutes
                })
        
        return gaps
    
    def bulk_insert(self, price_data_list: List[Dict[str, Any]]) -> bool:
        """Bulk insert price data with conflict handling"""
        try:
            for data in price_data_list:
                # Check for existing data to avoid duplicates
                existing = self.db.query(PriceData).filter(
                    PriceData.asset_id == data['asset_id'],
                    PriceData.timestamp == data['timestamp']
                ).first()
                
                if not existing:
                    price_data = PriceData(**data)
                    self.db.add(price_data)
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """Remove old price data beyond retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted_count = self.db.query(PriceData).filter(
            PriceData.timestamp < cutoff_date
        ).delete()
        
        self.db.commit()
        return deleted_count
    
    def get_price_changes(self, asset_id: int, timeframes: List[str] = None) -> Dict[str, Any]:
        """Calculate price changes for different timeframes"""
        if timeframes is None:
            timeframes = ['1h', '24h', '7d', '30d']
        
        current_price = self.get_latest_by_asset(asset_id)
        if not current_price:
            return {}
        
        changes = {'current_price': float(current_price.price)}
        
        timeframe_hours = {'1h': 1, '24h': 24, '7d': 168, '30d': 720}
        
        for tf in timeframes:
            if tf not in timeframe_hours:
                continue
            
            past_time = datetime.utcnow() - timedelta(hours=timeframe_hours[tf])
            past_price = self.db.query(PriceData).filter(
                PriceData.asset_id == asset_id,
                PriceData.timestamp <= past_time
            ).order_by(PriceData.timestamp.desc()).first()
            
            if past_price:
                change = (float(current_price.price) - float(past_price.price)) / float(past_price.price) * 100
                changes[f'{tf}_change_pct'] = round(change, 2)
            else:
                changes[f'{tf}_change_pct'] = None
        
        return changes
    
    def get_volume_analysis(self, asset_id: int, days: int = 7) -> Dict[str, Any]:
        """Analyze volume patterns"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        volume_data = self.db.query(
            func.avg(PriceData.volume).label('avg_volume'),
            func.max(PriceData.volume).label('max_volume'),
            func.min(PriceData.volume).label('min_volume'),
            func.sum(PriceData.volume).label('total_volume'),
            func.count(PriceData.id).label('data_points')
        ).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= cutoff_date,
            PriceData.volume.isnot(None)
        ).first()
        
        if not volume_data or not volume_data.avg_volume:
            return {}
        
        # Calculate volume trend (last 24h vs previous period)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_volume = self.db.query(func.avg(PriceData.volume)).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= last_24h
        ).scalar()
        
        prev_24h = last_24h - timedelta(hours=24)
        prev_volume = self.db.query(func.avg(PriceData.volume)).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= prev_24h,
            PriceData.timestamp < last_24h
        ).scalar()
        
        volume_trend = None
        if recent_volume and prev_volume:
            volume_trend = (recent_volume - prev_volume) / prev_volume * 100
        
        return {
            'avg_volume': float(volume_data.avg_volume),
            'max_volume': float(volume_data.max_volume),
            'min_volume': float(volume_data.min_volume),
            'total_volume': float(volume_data.total_volume),
            'data_points': volume_data.data_points,
            'volume_trend_24h_pct': round(volume_trend, 2) if volume_trend else None
        }
    
    def get_support_resistance_levels(self, asset_id: int, days: int = 30, 
                                    sensitivity: float = 0.02) -> Dict[str, List[float]]:
        """Identify potential support and resistance levels"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        prices = self.db.query(PriceData.price).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= cutoff_date
        ).order_by(PriceData.timestamp.asc()).all()
        
        if len(prices) < 10:
            return {'support_levels': [], 'resistance_levels': []}
        
        price_list = [float(p.price) for p in prices]
        
        # Simple pivot point detection
        supports = []
        resistances = []
        
        for i in range(2, len(price_list) - 2):
            current = price_list[i]
            
            # Check for local minimum (support)
            if (price_list[i] < price_list[i-1] and price_list[i] < price_list[i+1] and
                price_list[i] < price_list[i-2] and price_list[i] < price_list[i+2]):
                supports.append(current)
            
            # Check for local maximum (resistance)
            if (price_list[i] > price_list[i-1] and price_list[i] > price_list[i+1] and
                price_list[i] > price_list[i-2] and price_list[i] > price_list[i+2]):
                resistances.append(current)
        
        # Group similar levels together
        def group_levels(levels, sensitivity_pct):
            if not levels:
                return []
            
            sorted_levels = sorted(levels)
            grouped = []
            current_group = [sorted_levels[0]]
            
            for level in sorted_levels[1:]:
                if abs(level - current_group[-1]) / current_group[-1] <= sensitivity_pct:
                    current_group.append(level)
                else:
                    grouped.append(sum(current_group) / len(current_group))
                    current_group = [level]
            
            grouped.append(sum(current_group) / len(current_group))
            return [round(level, 2) for level in grouped]
        
        return {
            'support_levels': group_levels(supports, sensitivity)[-5:],  # Last 5 levels
            'resistance_levels': group_levels(resistances, sensitivity)[-5:]
        }
    
    def get_correlation_data(self, asset1_id: int, asset2_id: int, days: int = 30) -> Dict[str, Any]:
        """Calculate price correlation between two assets"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get aligned price data for both assets
        prices1 = self.db.query(PriceData.timestamp, PriceData.price).filter(
            PriceData.asset_id == asset1_id,
            PriceData.timestamp >= cutoff_date
        ).order_by(PriceData.timestamp.asc()).all()
        
        prices2 = self.db.query(PriceData.timestamp, PriceData.price).filter(
            PriceData.asset_id == asset2_id,
            PriceData.timestamp >= cutoff_date
        ).order_by(PriceData.timestamp.asc()).all()
        
        if len(prices1) < 10 or len(prices2) < 10:
            return {'correlation': None, 'data_points': 0}
        
        # Align timestamps (simple approach - could be improved)
        price1_dict = {p.timestamp: float(p.price) for p in prices1}
        price2_dict = {p.timestamp: float(p.price) for p in prices2}
        
        aligned_prices1 = []
        aligned_prices2 = []
        
        for ts in price1_dict:
            if ts in price2_dict:
                aligned_prices1.append(price1_dict[ts])
                aligned_prices2.append(price2_dict[ts])
        
        if len(aligned_prices1) < 10:
            return {'correlation': None, 'data_points': len(aligned_prices1)}
        
        # Calculate Pearson correlation
        import statistics
        
        mean1 = statistics.mean(aligned_prices1)
        mean2 = statistics.mean(aligned_prices2)
        
        numerator = sum((p1 - mean1) * (p2 - mean2) for p1, p2 in zip(aligned_prices1, aligned_prices2))
        
        sum_sq1 = sum((p1 - mean1) ** 2 for p1 in aligned_prices1)
        sum_sq2 = sum((p2 - mean2) ** 2 for p2 in aligned_prices2)
        
        denominator = (sum_sq1 * sum_sq2) ** 0.5
        
        correlation = numerator / denominator if denominator != 0 else 0
        
        return {
            'correlation': round(correlation, 4),
            'data_points': len(aligned_prices1),
            'period_days': days
        }
    
    def get_data_quality_report(self, asset_id: int, days: int = 7) -> Dict[str, Any]:
        """Generate data quality report for an asset"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        total_records = self.db.query(func.count(PriceData.id)).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= cutoff_date
        ).scalar()
        
        # Check for missing required fields
        missing_price = self.db.query(func.count(PriceData.id)).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= cutoff_date,
            PriceData.price.is_(None)
        ).scalar()
        
        missing_volume = self.db.query(func.count(PriceData.id)).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= cutoff_date,
            PriceData.volume.is_(None)
        ).scalar()
        
        # Check for suspicious values (e.g., zero prices)
        zero_prices = self.db.query(func.count(PriceData.id)).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp >= cutoff_date,
            PriceData.price <= 0
        ).scalar()
        
        # Check data gaps
        gaps = self.get_missing_data_gaps(asset_id, 5)
        
        quality_score = 100
        if total_records > 0:
            quality_score -= (missing_price / total_records * 30)  # 30% penalty for missing prices
            quality_score -= (missing_volume / total_records * 20)  # 20% penalty for missing volume
            quality_score -= (zero_prices / total_records * 25)     # 25% penalty for zero prices
            quality_score -= min(len(gaps), 5) * 5                  # 5% penalty per gap (max 25%)
        
        return {
            'asset_id': asset_id,
            'period_days': days,
            'total_records': total_records or 0,
            'missing_price': missing_price or 0,
            'missing_volume': missing_volume or 0,
            'zero_prices': zero_prices or 0,
            'data_gaps': len(gaps),
            'quality_score': max(0, round(quality_score, 1)),
            'quality_grade': 'A' if quality_score >= 90 else 'B' if quality_score >= 80 else 'C' if quality_score >= 70 else 'D' if quality_score >= 60 else 'F'
        }
