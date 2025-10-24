# backend/app/repositories/asset/archive.py
# Repository for archived price data management

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta

from ..base_repository import BaseRepository
from app.models.asset.price_data_archive import PriceDataArchive
from app.models.asset import Asset


class PriceDataArchiveRepository(BaseRepository):
    """
    Repository for archived price data management
    """
    
    def __init__(self, db: Session):
        super().__init__(PriceDataArchive, db)
    
    def get_by_asset(self, asset_id: int, limit: int = 1000) -> List[PriceDataArchive]:
        """Get archived data for an asset"""
        return self.db.query(PriceDataArchive).filter(
            PriceDataArchive.asset_id == asset_id
        ).order_by(PriceDataArchive.timestamp.desc()).limit(limit).all()
    
    def get_by_date_range(self, asset_id: int, start_date: datetime, end_date: datetime) -> List[PriceDataArchive]:
        """Get archived data within date range"""
        return self.db.query(PriceDataArchive).filter(
            PriceDataArchive.asset_id == asset_id,
            PriceDataArchive.timestamp >= start_date,
            PriceDataArchive.timestamp <= end_date
        ).order_by(PriceDataArchive.timestamp.asc()).all()
    
    def get_quality_issues(self, asset_id: int = None) -> List[PriceDataArchive]:
        """Get records with data quality issues"""
        query = self.db.query(PriceDataArchive).filter(
            PriceDataArchive.has_quality_issues == True
        )
        
        if asset_id:
            query = query.filter(PriceDataArchive.asset_id == asset_id)
        
        return query.order_by(PriceDataArchive.timestamp.desc()).all()
    
    def get_archive_statistics(self, asset_id: int = None) -> Dict[str, Any]:
        """Get archive statistics"""
        query = self.db.query(PriceDataArchive)
        
        if asset_id:
            query = query.filter(PriceDataArchive.asset_id == asset_id)
        
        stats = query.with_entities(
            func.count(PriceDataArchive.id).label('total_records'),
            func.min(PriceDataArchive.timestamp).label('oldest_record'),
            func.max(PriceDataArchive.timestamp).label('newest_record'),
            func.sum(func.case((PriceDataArchive.has_quality_issues == True, 1), else_=0)).label('quality_issues'),
            func.avg(PriceDataArchive.price).label('avg_price')
        ).first()
        
        if not stats:
            return {}
        
        return {
            'total_records': stats.total_records or 0,
            'oldest_record': stats.oldest_record.isoformat() if stats.oldest_record else None,
            'newest_record': stats.newest_record.isoformat() if stats.newest_record else None,
            'quality_issues': stats.quality_issues or 0,
            'quality_rate': ((stats.total_records - stats.quality_issues) / stats.total_records * 100) if stats.total_records > 0 else 0,
            'average_price': float(stats.avg_price) if stats.avg_price else 0
        }
    
    def search_by_criteria(self, criteria: Dict[str, Any]) -> List[PriceDataArchive]:
        """Search archived data by multiple criteria"""
        query = self.db.query(PriceDataArchive)
        
        if 'asset_id' in criteria:
            query = query.filter(PriceDataArchive.asset_id == criteria['asset_id'])
        
        if 'min_price' in criteria:
            query = query.filter(PriceDataArchive.price >= criteria['min_price'])
        
        if 'max_price' in criteria:
            query = query.filter(PriceDataArchive.price <= criteria['max_price'])
        
        if 'min_volume' in criteria:
            query = query.filter(PriceDataArchive.volume >= criteria['min_volume'])
        
        if 'quality_only' in criteria and criteria['quality_only']:
            query = query.filter(PriceDataArchive.has_quality_issues == False)
        
        return query.order_by(PriceDataArchive.timestamp.desc()).limit(1000).all()
    
    def bulk_archive_from_main(self, asset_id: int, cutoff_date: datetime) -> int:
        """Bulk transfer data from main price_data to archive"""
        from ...models.asset.price_data import PriceData
        
        # Get old data to archive
        old_data = self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp < cutoff_date
        ).all()
        
        archived_count = 0
        for data in old_data:
            # Create archive record
            archive_record = PriceDataArchive(
                asset_id=data.asset_id,
                timestamp=data.timestamp,
                price=data.price,
                volume=data.volume,
                market_cap=data.market_cap,
                source=data.source,
                raw_data=data.raw_data,
                quality_score=getattr(data, 'quality_score', None),
                has_quality_issues=getattr(data, 'has_quality_issues', False)
            )
            
            self.db.add(archive_record)
            archived_count += 1
        
        # Remove from main table
        self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.timestamp < cutoff_date
        ).delete()
        
        self.db.commit()
        return archived_count
    
    def get_historical_aggregates(self, asset_id: int, period: str = 'daily') -> List[Dict[str, Any]]:
        """Get historical aggregated data by period"""
        # This would need more sophisticated date_trunc based on period
        # For now, implementing daily aggregates
        
        results = self.db.query(
            func.date_trunc('day', PriceDataArchive.timestamp).label('period'),
            func.first_value(PriceDataArchive.price).over(
                partition_by=func.date_trunc('day', PriceDataArchive.timestamp),
                order_by=PriceDataArchive.timestamp
            ).label('open_price'),
            func.last_value(PriceDataArchive.price).over(
                partition_by=func.date_trunc('day', PriceDataArchive.timestamp),
                order_by=PriceDataArchive.timestamp
            ).label('close_price'),
            func.max(PriceDataArchive.price).label('high_price'),
            func.min(PriceDataArchive.price).label('low_price'),
            func.sum(PriceDataArchive.volume).label('total_volume')
        ).filter(
            PriceDataArchive.asset_id == asset_id
        ).group_by(
            func.date_trunc('day', PriceDataArchive.timestamp)
        ).order_by(
            func.date_trunc('day', PriceDataArchive.timestamp).desc()
        ).limit(365).all()
        
        return [{
            'date': result.period.isoformat(),
            'open': float(result.open_price),
            'close': float(result.close_price), 
            'high': float(result.high_price),
            'low': float(result.low_price),
            'volume': float(result.total_volume)
        } for result in results]
    
    def get_multi_timeframe_aggregates(self, asset_id: int, 
                                     timeframes: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get aggregated data for multiple timeframes"""
        if timeframes is None:
            timeframes = ['1h', '4h', '1d', '1w']
        
        timeframe_mapping = {
            '1h': 'hour',
            '4h': 'hour',  # Will group by 4-hour intervals
            '1d': 'day', 
            '1w': 'week',
            '1M': 'month'
        }
        
        results = {}
        
        for tf in timeframes:
            if tf not in timeframe_mapping:
                continue
                
            if tf == '4h':
                # Special handling for 4-hour intervals
                data = self._get_4hour_aggregates(asset_id)
            else:
                trunc_period = timeframe_mapping[tf]
                data = self._get_period_aggregates(asset_id, trunc_period, 
                                                 365 if tf == '1d' else 168 if tf == '1w' else 720)
            
            results[tf] = data
        
        return results
    
    def _get_4hour_aggregates(self, asset_id: int, limit: int = 180) -> List[Dict[str, Any]]:
        """Get 4-hour OHLCV aggregates"""
        # Group by 4-hour intervals
        results = self.db.query(
            func.to_timestamp(
                func.floor(func.extract('epoch', PriceDataArchive.timestamp) / 14400) * 14400
            ).label('period_start'),
            func.min(PriceDataArchive.price).label('low_price'),
            func.max(PriceDataArchive.price).label('high_price'),
            func.sum(PriceDataArchive.volume).label('total_volume'),
            func.count(PriceDataArchive.id).label('data_points')
        ).filter(
            PriceDataArchive.asset_id == asset_id
        ).group_by(
            func.floor(func.extract('epoch', PriceDataArchive.timestamp) / 14400)
        ).order_by(
            func.floor(func.extract('epoch', PriceDataArchive.timestamp) / 14400).desc()
        ).limit(limit).all()
        
        # Get first and last prices for each 4h period
        enhanced_results = []
        for result in results:
            period_data = self.db.query(PriceDataArchive.price).filter(
                PriceDataArchive.asset_id == asset_id,
                PriceDataArchive.timestamp >= result.period_start,
                PriceDataArchive.timestamp < result.period_start + timedelta(hours=4)
            ).order_by(PriceDataArchive.timestamp.asc()).all()
            
            if period_data:
                enhanced_results.append({
                    'timestamp': result.period_start.isoformat(),
                    'open': float(period_data[0].price),
                    'close': float(period_data[-1].price),
                    'high': float(result.high_price),
                    'low': float(result.low_price),
                    'volume': float(result.total_volume),
                    'data_points': result.data_points
                })
        
        return enhanced_results
    
    def _get_period_aggregates(self, asset_id: int, period: str, limit: int) -> List[Dict[str, Any]]:
        """Generic method for period aggregates"""
        results = self.db.query(
            func.date_trunc(period, PriceDataArchive.timestamp).label('period'),
            func.first_value(PriceDataArchive.price).over(
                partition_by=func.date_trunc(period, PriceDataArchive.timestamp),
                order_by=PriceDataArchive.timestamp
            ).label('open_price'),
            func.last_value(PriceDataArchive.price).over(
                partition_by=func.date_trunc(period, PriceDataArchive.timestamp),
                order_by=PriceDataArchive.timestamp
            ).label('close_price'),
            func.max(PriceDataArchive.price).label('high_price'),
            func.min(PriceDataArchive.price).label('low_price'),
            func.sum(PriceDataArchive.volume).label('total_volume')
        ).filter(
            PriceDataArchive.asset_id == asset_id
        ).group_by(
            func.date_trunc(period, PriceDataArchive.timestamp)
        ).order_by(
            func.date_trunc(period, PriceDataArchive.timestamp).desc()
        ).limit(limit).all()
        
        return [{
            'timestamp': result.period.isoformat(),
            'open': float(result.open_price),
            'close': float(result.close_price),
            'high': float(result.high_price),
            'low': float(result.low_price),
            'volume': float(result.total_volume)
        } for result in results]
    
    def get_historical_volatility(self, asset_id: int, days: int = 365) -> Dict[str, Any]:
        """Calculate historical volatility over different periods"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily closes for volatility calculation
        daily_closes = self.db.query(
            func.date_trunc('day', PriceDataArchive.timestamp).label('date'),
            func.last_value(PriceDataArchive.price).over(
                partition_by=func.date_trunc('day', PriceDataArchive.timestamp),
                order_by=PriceDataArchive.timestamp
            ).label('close_price')
        ).filter(
            PriceDataArchive.asset_id == asset_id,
            PriceDataArchive.timestamp >= cutoff_date
        ).group_by(
            func.date_trunc('day', PriceDataArchive.timestamp)
        ).order_by(
            func.date_trunc('day', PriceDataArchive.timestamp).asc()
        ).all()
        
        if len(daily_closes) < 30:
            return {'error': 'Insufficient data for volatility calculation'}
        
        # Calculate returns and volatility
        prices = [float(row.close_price) for row in daily_closes]
        daily_returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        import statistics
        
        volatility_30d = statistics.stdev(daily_returns[-30:]) * (365 ** 0.5) if len(daily_returns) >= 30 else None
        volatility_90d = statistics.stdev(daily_returns[-90:]) * (365 ** 0.5) if len(daily_returns) >= 90 else None
        volatility_365d = statistics.stdev(daily_returns) * (365 ** 0.5) if len(daily_returns) >= 30 else None
        
        return {
            'asset_id': asset_id,
            'data_period_days': len(daily_closes),
            'volatility_30d_annualized': round(volatility_30d * 100, 2) if volatility_30d else None,
            'volatility_90d_annualized': round(volatility_90d * 100, 2) if volatility_90d else None,
            'volatility_365d_annualized': round(volatility_365d * 100, 2) if volatility_365d else None,
            'max_daily_return': round(max(daily_returns) * 100, 2),
            'min_daily_return': round(min(daily_returns) * 100, 2),
            'avg_daily_return': round(statistics.mean(daily_returns) * 100, 4)
        }
    
    def get_price_extremes(self, asset_id: int, period_days: int = 365) -> Dict[str, Any]:
        """Find historical price extremes (all-time highs/lows within period)"""
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        extremes = self.db.query(
            func.max(PriceDataArchive.price).label('max_price'),
            func.min(PriceDataArchive.price).label('min_price')
        ).filter(
            PriceDataArchive.asset_id == asset_id,
            PriceDataArchive.timestamp >= cutoff_date
        ).first()
        
        if not extremes:
            return {}
        
        # Find when these extremes occurred
        max_price_date = self.db.query(PriceDataArchive.timestamp).filter(
            PriceDataArchive.asset_id == asset_id,
            PriceDataArchive.price == extremes.max_price,
            PriceDataArchive.timestamp >= cutoff_date
        ).order_by(PriceDataArchive.timestamp.desc()).first()
        
        min_price_date = self.db.query(PriceDataArchive.timestamp).filter(
            PriceDataArchive.asset_id == asset_id,
            PriceDataArchive.price == extremes.min_price,
            PriceDataArchive.timestamp >= cutoff_date
        ).order_by(PriceDataArchive.timestamp.desc()).first()
        
        return {
            'period_days': period_days,
            'highest_price': float(extremes.max_price),
            'lowest_price': float(extremes.min_price),
            'highest_price_date': max_price_date.timestamp.isoformat() if max_price_date else None,
            'lowest_price_date': min_price_date.timestamp.isoformat() if min_price_date else None,
            'price_range_pct': round((extremes.max_price - extremes.min_price) / extremes.min_price * 100, 2)
        }
    
    def cleanup_duplicate_records(self, asset_id: int = None) -> Dict[str, int]:
        """Remove duplicate archive records"""
        from sqlalchemy import exists
        
        query = self.db.query(PriceDataArchive).filter(
            exists().where(
                and_(
                    PriceDataArchive.asset_id == PriceDataArchive.asset_id,
                    PriceDataArchive.timestamp == PriceDataArchive.timestamp,
                    PriceDataArchive.id > PriceDataArchive.id
                )
            )
        )
        
        if asset_id:
            query = query.filter(PriceDataArchive.asset_id == asset_id)
        
        duplicate_count = query.count()
        query.delete(synchronize_session=False)
        
        self.db.commit()
        
        return {
            'duplicates_removed': duplicate_count,
            'asset_id': asset_id
        }
    
    def get_archive_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive archive health report"""
        total_records = self.db.query(func.count(PriceDataArchive.id)).scalar()
        
        assets_with_data = self.db.query(
            func.count(func.distinct(PriceDataArchive.asset_id))
        ).scalar()
        
        quality_issues = self.db.query(func.count(PriceDataArchive.id)).filter(
            PriceDataArchive.has_quality_issues == True
        ).scalar()
        
        date_range = self.db.query(
            func.min(PriceDataArchive.timestamp).label('oldest'),
            func.max(PriceDataArchive.timestamp).label('newest')
        ).first()
        
        # Storage efficiency (records per day)
        if date_range.oldest and date_range.newest:
            days_span = (date_range.newest - date_range.oldest).days
            records_per_day = total_records / max(days_span, 1)
        else:
            records_per_day = 0
        
        return {
            'total_archive_records': total_records or 0,
            'assets_with_archived_data': assets_with_data or 0,
            'quality_issues_count': quality_issues or 0,
            'quality_rate_pct': round((1 - (quality_issues / total_records)) * 100, 2) if total_records > 0 else 100,
            'oldest_record': date_range.oldest.isoformat() if date_range.oldest else None,
            'newest_record': date_range.newest.isoformat() if date_range.newest else None,
            'archive_span_days': (date_range.newest - date_range.oldest).days if date_range.oldest and date_range.newest else 0,
            'avg_records_per_day': round(records_per_day, 1),
            'estimated_storage_gb': round(total_records * 0.0001, 2)  # Rough estimate
        }
