# backend/app/repositories/asset/price_data.py
# Repository for price data management

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from datetime import datetime, timedelta

from ..base_repository import BaseRepository
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

    def get_timeframe_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Get timeframe hierarchy and aggregation rules"""
        return {
            '1m': {'minutes': 1, 'base_timeframe': None},
            '5m': {'minutes': 5, 'base_timeframe': '1m'},
            '15m': {'minutes': 15, 'base_timeframe': '5m'},
            '1h': {'minutes': 60, 'base_timeframe': '15m'},
            '4h': {'minutes': 240, 'base_timeframe': '1h'},
            '1d': {'minutes': 1440, 'base_timeframe': '4h'},
            '1w': {'minutes': 10080, 'base_timeframe': '1d'},
            '1M': {'minutes': 43200, 'base_timeframe': '1w'}  # Approximate 30 days
        }

    def get_aggregatable_timeframes(self, source_timeframe: str) -> List[str]:
        """Get list of timeframes that can be aggregated from source timeframe"""
        hierarchy = self.get_timeframe_hierarchy()
        source_minutes = hierarchy.get(source_timeframe, {}).get('minutes', 0)
        
        if not source_minutes:
            return []
        
        aggregatable = []
        for tf, info in hierarchy.items():
            tf_minutes = info['minutes']
            if tf_minutes > source_minutes and tf_minutes % source_minutes == 0:
                aggregatable.append(tf)
        
        return sorted(aggregatable, key=lambda x: hierarchy[x]['minutes'])

    def aggregate_to_higher_timeframe(self, asset_id: int, source_timeframe: str, 
                                    target_timeframe: str, start_time: datetime = None, 
                                    end_time: datetime = None) -> List[Dict[str, Any]]:
        """
        Aggregate price data from source timeframe to higher target timeframe using SQL
        
        Args:
            asset_id: Asset ID to aggregate data for
            source_timeframe: Source timeframe (e.g., '1h')
            target_timeframe: Target timeframe (e.g., '4h', '1d')
            start_time: Start time for aggregation (optional)
            end_time: End time for aggregation (optional)
            
        Returns:
            List of aggregated OHLCV data
        """
        hierarchy = self.get_timeframe_hierarchy()
        
        # Validate timeframes
        if source_timeframe not in hierarchy or target_timeframe not in hierarchy:
            raise ValueError(f"Invalid timeframes: {source_timeframe} or {target_timeframe}")
        
        source_minutes = hierarchy[source_timeframe]['minutes']
        target_minutes = hierarchy[target_timeframe]['minutes']
        
        if target_minutes <= source_minutes:
            raise ValueError(f"Target timeframe {target_timeframe} must be higher than source {source_timeframe}")
        
        if target_minutes % source_minutes != 0:
            raise ValueError(f"Target timeframe {target_timeframe} must be divisible by source {source_timeframe}")
        
        # Calculate time grouping interval
        interval_expression = self._get_time_grouping_expression(target_timeframe)
        
        # Build base query
        base_conditions = [
            PriceData.asset_id == asset_id,
            PriceData.timeframe == source_timeframe
        ]
        
        if start_time:
            base_conditions.append(PriceData.candle_time >= start_time)
        if end_time:
            base_conditions.append(PriceData.candle_time <= end_time)
        
        # SQL aggregation query with proper VWAP calculation
        aggregation_query = self.db.query(
            func.date_trunc(interval_expression, PriceData.candle_time).label('period_start'),
            func.first_value(PriceData.open_price).over(
                partition_by=func.date_trunc(interval_expression, PriceData.candle_time),
                order_by=PriceData.candle_time.asc()
            ).label('open_price'),
            func.max(PriceData.high_price).label('high_price'),
            func.min(PriceData.low_price).label('low_price'),
            func.last_value(PriceData.close_price).over(
                partition_by=func.date_trunc(interval_expression, PriceData.candle_time),
                order_by=PriceData.candle_time.asc(),
                range_=(None, None)
            ).label('close_price'),
            func.sum(PriceData.volume).label('volume'),
            func.avg(PriceData.market_cap).label('avg_market_cap'),
            func.sum(PriceData.trade_count).label('total_trades'),
            # Calculate volume-weighted average price properly
            (func.sum(PriceData.close_price * PriceData.volume) / 
             func.nullif(func.sum(PriceData.volume), 0)).label('vwap'),
            func.count(PriceData.id).label('source_records')
        ).filter(
            and_(*base_conditions)
        ).group_by(
            func.date_trunc(interval_expression, PriceData.candle_time)
        ).order_by(
            func.date_trunc(interval_expression, PriceData.candle_time).asc()
        )
        
        results = aggregation_query.all()
        
        # Convert to dictionary format
        aggregated_data = []
        for row in results:
            aggregated_data.append({
                'asset_id': asset_id,
                'timeframe': target_timeframe,
                'candle_time': row.period_start,
                'open_price': float(row.open_price) if row.open_price else 0,
                'high_price': float(row.high_price) if row.high_price else 0,
                'low_price': float(row.low_price) if row.low_price else 0,
                'close_price': float(row.close_price) if row.close_price else 0,
                'volume': float(row.volume) if row.volume else 0,
                'market_cap': float(row.avg_market_cap) if row.avg_market_cap else None,
                'trade_count': int(row.total_trades) if row.total_trades else None,
                'vwap': float(row.vwap) if row.vwap else None,
                'source_records': row.source_records,
                'is_validated': False  # Aggregated data needs validation
            })
        
        return aggregated_data

    def _get_time_grouping_expression(self, timeframe: str) -> str:
        """Get PostgreSQL date_trunc expression for timeframe"""
        grouping_map = {
            '5m': '5 minutes',
            '15m': '15 minutes', 
            '1h': 'hour',
            '4h': '4 hours',
            '1d': 'day',
            '1w': 'week',
            '1M': 'month'
        }
        
        if timeframe not in grouping_map:
            raise ValueError(f"Unsupported timeframe for grouping: {timeframe}")
        
        return grouping_map[timeframe]

    def bulk_aggregate_and_store(self, asset_id: int, source_timeframe: str, 
                                target_timeframes: List[str] = None,
                                start_time: datetime = None, 
                                end_time: datetime = None) -> Dict[str, int]:
        """
        Bulk aggregate from source timeframe to multiple target timeframes and store results
        
        Returns:
            Dictionary with timeframe -> count of records created
        """
        if target_timeframes is None:
            target_timeframes = self.get_aggregatable_timeframes(source_timeframe)
        
        results = {}
        
        for target_tf in target_timeframes:
            try:
                # Get aggregated data
                aggregated_data = self.aggregate_to_higher_timeframe(
                    asset_id=asset_id,
                    source_timeframe=source_timeframe,
                    target_timeframe=target_tf,
                    start_time=start_time,
                    end_time=end_time
                )
                
                # Store aggregated data
                stored_count = 0
                for data in aggregated_data:
                    # Check if record already exists
                    existing = self.db.query(PriceData).filter(
                        PriceData.asset_id == data['asset_id'],
                        PriceData.timeframe == data['timeframe'],
                        PriceData.candle_time == data['candle_time']
                    ).first()
                    
                    if not existing:
                        price_data = PriceData(**data)
                        self.db.add(price_data)
                        stored_count += 1
                    else:
                        # Update existing record with aggregated data
                        for key, value in data.items():
                            if key not in ['asset_id', 'timeframe', 'candle_time']:
                                setattr(existing, key, value)
                        stored_count += 1
                
                self.db.commit()
                results[target_tf] = stored_count
                
            except Exception as e:
                self.db.rollback()
                results[target_tf] = f"Error: {str(e)}"
        
        return results

    def get_aggregation_status(self, asset_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Get aggregation status showing available data for each timeframe
        
        Returns:
            Dictionary with timeframe -> {count, latest_time, earliest_time}
        """
        hierarchy = self.get_timeframe_hierarchy()
        status = {}
        
        for timeframe in hierarchy.keys():
            data_stats = self.db.query(
                func.count(PriceData.id).label('count'),
                func.max(PriceData.candle_time).label('latest'),
                func.min(PriceData.candle_time).label('earliest')
            ).filter(
                PriceData.asset_id == asset_id,
                PriceData.timeframe == timeframe
            ).first()
            
            status[timeframe] = {
                'count': data_stats.count if data_stats else 0,
                'latest_time': data_stats.latest.isoformat() if data_stats.latest else None,
                'earliest_time': data_stats.earliest.isoformat() if data_stats.earliest else None,
                'can_aggregate_to': self.get_aggregatable_timeframes(timeframe)
            }
        
        return status

    def optimize_storage_with_aggregation(self, asset_id: int, source_timeframe: str = '1h',
                                        keep_days: int = 30) -> Dict[str, Any]:
        """
        Optimize storage by aggregating older data to higher timeframes
        
        Strategy:
        - Keep recent data in original timeframe
        - Aggregate older data to higher timeframes
        - Remove original data after aggregation
        """
        cutoff_date = datetime.utcnow() - timedelta(days=keep_days)
        
        # Get aggregatable timeframes
        target_timeframes = self.get_aggregatable_timeframes(source_timeframe)
        
        if not target_timeframes:
            return {'message': f'No aggregatable timeframes found for {source_timeframe}'}
        
        # Aggregate old data
        aggregation_results = {}
        for target_tf in target_timeframes:
            results = self.bulk_aggregate_and_store(
                asset_id=asset_id,
                source_timeframe=source_timeframe,
                target_timeframes=[target_tf],
                end_time=cutoff_date
            )
            aggregation_results.update(results)
        
        # Remove old source data after successful aggregation
        deleted_count = self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.timeframe == source_timeframe,
            PriceData.candle_time < cutoff_date
        ).delete()
        
        self.db.commit()
        
        return {
            'source_timeframe': source_timeframe,
            'cutoff_date': cutoff_date.isoformat(),
            'aggregated_records': aggregation_results,
            'deleted_source_records': deleted_count,
            'storage_optimization': 'completed'
        }

    def parallel_aggregate_multiple_assets(self, asset_ids: List[int], 
                                         source_timeframe: str = '1h',
                                         target_timeframes: List[str] = None,
                                         batch_size: int = 10) -> Dict[int, Dict[str, Any]]:
        """
        Efficiently aggregate multiple assets in parallel batches
        
        Args:
            asset_ids: List of asset IDs to process
            source_timeframe: Source timeframe for aggregation
            target_timeframes: Target timeframes (auto-detected if None)
            batch_size: Number of assets to process in each batch
            
        Returns:
            Dictionary with asset_id -> aggregation results
        """
        if target_timeframes is None:
            target_timeframes = self.get_aggregatable_timeframes(source_timeframe)
        
        results = {}
        
        # Process assets in batches
        for i in range(0, len(asset_ids), batch_size):
            batch = asset_ids[i:i + batch_size]
            
            for asset_id in batch:
                try:
                    asset_results = self.bulk_aggregate_and_store(
                        asset_id=asset_id,
                        source_timeframe=source_timeframe,
                        target_timeframes=target_timeframes
                    )
                    results[asset_id] = {
                        'status': 'success',
                        'timeframe_results': asset_results
                    }
                except Exception as e:
                    results[asset_id] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Commit after each batch
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                # Mark batch as failed
                for asset_id in batch:
                    if results.get(asset_id, {}).get('status') == 'success':
                        results[asset_id] = {
                            'status': 'error',
                            'error': f'Batch commit failed: {str(e)}'
                        }
        
        return results


# Example usage for timeframe aggregation:
"""
# Initialize repository
repo = PriceDataRepository(db_session)

# 1. Check what timeframes can be aggregated from 1h data
aggregatable = repo.get_aggregatable_timeframes('1h')
# Returns: ['4h', '1d', '1w', '1M']

# 2. Aggregate 1h data to 4h timeframe
aggregated_4h = repo.aggregate_to_higher_timeframe(
    asset_id=1, 
    source_timeframe='1h', 
    target_timeframe='4h',
    start_time=datetime(2025, 10, 1),
    end_time=datetime(2025, 10, 15)
)

# 3. Bulk aggregate and store multiple timeframes
results = repo.bulk_aggregate_and_store(
    asset_id=1,
    source_timeframe='1h',
    target_timeframes=['4h', '1d'],
    start_time=datetime(2025, 10, 1)
)

# 4. Check aggregation status for an asset
status = repo.get_aggregation_status(asset_id=1)

# 5. Optimize storage (keep recent 1h data, aggregate older to higher timeframes)
optimization_result = repo.optimize_storage_with_aggregation(
    asset_id=1,
    source_timeframe='1h',
    keep_days=30
)
"""
