# backend/app/repositories/asset/price_data.py
# Repository for price data management

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

from ..base_repository import BaseRepository
from app.models.asset.price_data import PriceData
from app.models.asset import Asset


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
        ).order_by(PriceData.candle_time.desc()).limit(limit).all()
    
    def get_by_symbol(self, symbol: str, limit: int = 100) -> List[PriceData]:
        """Get recent price data by symbol"""
        return self.db.query(PriceData).join(Asset).filter(
            Asset.symbol == symbol
        ).order_by(PriceData.candle_time.desc()).limit(limit).all()
    
    def get_price_range(self, asset_id: int, start_date: datetime, end_date: datetime) -> List[PriceData]:
        """Get price data within date range"""
        return self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= start_date,
            PriceData.candle_time <= end_date
        ).order_by(PriceData.candle_time.asc()).all()
    
    def get_latest_by_asset(self, asset_id: int) -> Optional[PriceData]:
        """Get latest price for an asset"""
        return self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id
        ).order_by(PriceData.candle_time.desc()).first()
    
    async def get_latest_price_data(self, asset_id: int) -> Optional[PriceData]:
        """
        Get latest price data for an asset (async version)
        
        Args:
            asset_id: Asset ID to get latest price data for
            
        Returns:
            Latest PriceData record or None if not found
        """
        return self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id
        ).order_by(PriceData.candle_time.desc()).first()
    
    def get_ohlc_data(self, asset_id: int, hours: int = 24) -> List[PriceData]:
        """Get OHLC data for specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_time
        ).order_by(PriceData.candle_time.asc()).all()
    
    def get_price_statistics(self, asset_id: int, days: int = 30) -> Dict[str, Any]:
        """Get price statistics for an asset"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stats = self.db.query(
            func.max(PriceData.high_price).label('max_price'),
            func.min(PriceData.low_price).label('min_price'),
            func.avg(PriceData.close_price).label('avg_price'),
            func.sum(PriceData.volume).label('total_volume'),
            func.count(PriceData.id).label('data_points')
        ).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_date
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
        """
        Calculate price volatility using percentage returns
        
        Uses close_price for volatility calculation based on daily returns
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        prices = self.db.query(PriceData.close_price).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_date
        ).order_by(PriceData.candle_time.asc()).all()
        
        if len(prices) < 2:
            return 0.0
        
        price_list = [float(p.close_price) for p in prices]
        returns = [(price_list[i] - price_list[i-1]) / price_list[i-1] for i in range(1, len(price_list))]
        
        if not returns:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return variance ** 0.5
    
    def get_missing_data_gaps(self, asset_id: int, expected_interval_minutes: int = 5) -> List[Dict[str, Any]]:
        """Identify gaps in price data"""
        recent_data = self.db.query(PriceData.candle_time).filter(
            PriceData.asset_id == asset_id
        ).order_by(PriceData.candle_time.desc()).limit(1000).all()
        
        if len(recent_data) < 2:
            return []
        
        gaps = []
        timestamps = [d.candle_time for d in reversed(recent_data)]
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

    def _get_existing_records(self, asset_id: int, timeframe: str, candle_times: List) -> Dict:
        """Get existing records for bulk comparison with timezone normalization"""
        if not candle_times:
            return {}
        
        existing_query = self.db.query(PriceData).filter(
            PriceData.asset_id == asset_id,
            PriceData.timeframe == timeframe,
            PriceData.candle_time.in_(candle_times)
        ).all()
        
        # Create lookup dictionary with timezone normalization
        existing_records = {}
        for record in existing_query:
            normalized_time = record.candle_time
            if normalized_time.tzinfo is not None:
                normalized_time = normalized_time.replace(tzinfo=None)
            existing_records[normalized_time] = record
        
        return existing_records

    def _get_existing_record(self, existing_records: Dict, candle_time) -> Optional[PriceData]:
        """Get existing record with timezone normalization"""
        lookup_time = candle_time
        if hasattr(lookup_time, 'tzinfo') and lookup_time.tzinfo is not None:
            lookup_time = lookup_time.replace(tzinfo=None)
        return existing_records.get(lookup_time)

    def _should_update_existing_record(self, existing: PriceData, new_data: Dict) -> bool:
        """Check if existing record should be updated based on price changes"""
        def safe_compare(existing_val, new_val, tolerance=1e-8):
            if existing_val is None and new_val is None:
                return True
            if existing_val is None or new_val is None:
                return False
            try:
                existing_float = float(existing_val)
                new_float = float(new_val)
                return abs(existing_float - new_float) < tolerance
            except (ValueError, TypeError):
                return existing_val == new_val
        
        # Check if key price fields have changed
        price_unchanged = (
            safe_compare(existing.close_price, new_data.get('close_price')) and
            safe_compare(existing.low_price, new_data.get('low_price')) and
            safe_compare(existing.high_price, new_data.get('high_price'))
        )
        
        return not price_unchanged

    def _update_existing_record(self, existing: PriceData, new_data: Dict) -> None:
        """Update existing record with new data"""
        for key, value in new_data.items():
            if key not in ['asset_id', 'timeframe', 'candle_time'] and hasattr(existing, key):
                setattr(existing, key, value)
    
    def bulk_insert(self, asset: Asset, price_data_list: List[Dict[str, Any]], timeframe: str = '1h') -> Dict[str, Any]:
        """
        Bulk insert price data with conflict handling, cache update, and enhanced reporting
        
        Filtering Rules:
        - Only processes data >= latest existing candle time in database
        - Older data is completely filtered out (not inserted or updated)
        - Only the latest candle (equal time) can be updated if it exists
        - Historical candles are immutable to ensure data integrity
        
        Args:
            asset: Asset object (already loaded with cache data)
            price_data_list: List of price data dictionaries
            timeframe: Target timeframe for optimization (default: '1h')
            
        Returns:
            Dictionary with detailed results including:
            - total_input_records: Original count before filtering
            - filtered_out_old_records: Count of old records filtered out
            - latest_candle_time_filter: The filter timestamp used
        """
        try:
            inserted_count = 0
            updated_count = 0
            skipped_count = 0
            data_range = {'start': None, 'end': None}
            
            # Get latest candle time to only allow updates to the most recent candle
            latest_candle_time = asset.get_latest_candle_time(timeframe) if asset else None
            
            # Filter out data older than the latest candle time (except for equal times which can be updated)
            filtered_price_data_list = []
            if latest_candle_time:
                for data in price_data_list:
                    data_candle_time = data.get('candle_time')
                    if data_candle_time and data_candle_time >= latest_candle_time:
                        filtered_price_data_list.append(data)
                    # Skip older data completely
            else:
                # No existing data, process all
                filtered_price_data_list = price_data_list
            
            # Track min and max times for reporting (from filtered data)
            candle_times = [data['candle_time'] for data in filtered_price_data_list if 'candle_time' in data]
            
            # Extract all candle times for bulk query optimization (from filtered data)
            candle_times_to_check = [data['candle_time'] for data in filtered_price_data_list if 'candle_time' in data]
             
            # Bulk query to check existing records - fetch all at once to avoid N+1 queries
            existing_records = self._get_existing_records(asset.id, timeframe, candle_times_to_check)
            
            # Track processed candle times to avoid duplicates within this batch
            
            for data in filtered_price_data_list:
                # Ensure data consistency - set asset_id and timeframe
                data['asset_id'] = asset.id
                data['timeframe'] = timeframe
                
                # Get existing record using normalized lookup
                existing = self._get_existing_record(existing_records, data['candle_time'])
                
                if not existing:
                    # Insert new record with duplicate check
                    try:
                        price_data = PriceData(**data)
                        self.db.add(price_data)
                        self.db.flush()  # Force DB to check constraints before commit
                        inserted_count += 1
                    except Exception as e:
                        # Handle duplicate key violation - record might have been inserted by another process
                        if "duplicate key value violates unique constraint" in str(e) or "UniqueViolation" in str(e):
                            self.db.rollback()
                            # Re-query to get the existing record
                            existing = self.db.query(PriceData).filter(
                                PriceData.asset_id == asset.id,
                                PriceData.timeframe == timeframe,
                                PriceData.candle_time == data['candle_time']
                            ).first()
                            
                            if existing and latest_candle_time and data['candle_time'] == latest_candle_time:
                                # Try to update the existing record if it's the latest candle
                                try:
                                    for key, value in data.items():
                                        if key not in ['asset_id', 'timeframe', 'candle_time'] and hasattr(existing, key):
                                            setattr(existing, key, value)
                                    updated_count += 1
                                except Exception:
                                    skipped_count += 1
                            else:
                                skipped_count += 1
                        else:
                            # Re-raise if it's not a duplicate key error
                            raise
                else:
                    # Check if this candle is the latest one (only latest candle can be updated)
                    # Only allow updates to the latest candle
                    if latest_candle_time and data['candle_time'] == latest_candle_time:
                        if self._should_update_existing_record(existing, data):
                            # Update existing record with new data
                            self._update_existing_record(existing, data)
                            updated_count += 1
                        else:
                            # Skip update if price data is identical
                            skipped_count += 1
                    else:
                        # Skip update for historical candles (not the latest one)
                        skipped_count += 1

            
            # Calculate data range
            if candle_times:
                data_range = {
                    'start': min(candle_times),
                    'end': max(candle_times)
                }
            
            # Commit with error handling for any remaining constraint violations
            try:
                self.db.commit()
            except Exception as commit_error:
                self.db.rollback()
                if "duplicate key value violates unique constraint" in str(commit_error) or "UniqueViolation" in str(commit_error):
                    # Log the duplicate key error but don't fail completely
                    total_input_records = len(price_data_list)
                    filtered_out_count = total_input_records - len(filtered_price_data_list)
                    return {
                        'status': 'partial_success',
                        'total_input_records': total_input_records,
                        'filtered_out_old_records': filtered_out_count,
                        'total_processed': len(filtered_price_data_list),
                        'inserted_records': inserted_count,
                        'updated_records': updated_count,
                        'skipped_records': skipped_count + (len(filtered_price_data_list) - inserted_count - updated_count - skipped_count),
                        'data_range': data_range,
                        'latest_candle_time_filter': latest_candle_time.isoformat() if latest_candle_time else None,
                        'warning': f"Some records skipped due to constraint violations: {str(commit_error)}",
                        'success': True  # For backward compatibility
                    }
                else:
                    raise
            
            # Update timeframe cache
            if inserted_count > 0 or updated_count > 0:
                self._update_asset_timeframe_cache(asset.id, timeframe, 'refresh')
            
            total_processed = inserted_count + updated_count + skipped_count
            total_input_records = len(price_data_list)
            filtered_out_count = total_input_records - len(filtered_price_data_list)
            
            return {
                'status': 'success',
                'total_input_records': total_input_records,
                'filtered_out_old_records': filtered_out_count,
                'total_processed': total_processed,
                'inserted_records': inserted_count,
                'updated_records': updated_count,
                'skipped_records': skipped_count,
                'data_range': data_range,
                'latest_candle_time_filter': latest_candle_time.isoformat() if latest_candle_time else None,
                'success': True  # For backward compatibility
            }
            
        except Exception as e:
            self.db.rollback()
            total_input_records = len(price_data_list)
            return {
                'status': 'error',
                'error': str(e),
                'total_input_records': total_input_records,
                'filtered_out_old_records': 0,
                'total_processed': 0,
                'inserted_records': 0,
                'updated_records': 0,
                'skipped_records': 0,
                'data_range': {'start': None, 'end': None},
                'latest_candle_time_filter': None,
                'success': False  # For backward compatibility
            }
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """Remove old price data beyond retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted_count = self.db.query(PriceData).filter(
            PriceData.candle_time < cutoff_date
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
                PriceData.candle_time <= past_time
            ).order_by(PriceData.candle_time.desc()).first()
            
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
            PriceData.candle_time >= cutoff_date,
            PriceData.volume.isnot(None)
        ).first()
        
        if not volume_data or not volume_data.avg_volume:
            return {}
        
        # Calculate volume trend (last 24h vs previous period)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_volume = self.db.query(func.avg(PriceData.volume)).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= last_24h
        ).scalar()
        
        prev_24h = last_24h - timedelta(hours=24)
        prev_volume = self.db.query(func.avg(PriceData.volume)).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= prev_24h,
            PriceData.candle_time < last_24h
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
        """
        Identify potential support and resistance levels using high/low prices
        
        Uses percentage-based sensitivity for grouping similar levels together
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get high and low prices for better support/resistance detection
        price_data = self.db.query(PriceData.high_price, PriceData.low_price, PriceData.close_price).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_date
        ).order_by(PriceData.candle_time.asc()).all()
        
        if len(price_data) < 10:
            return {'support_levels': [], 'resistance_levels': []}
        
        # Use close prices for pivot detection but consider high/low for accuracy
        close_prices = [float(p.close_price) for p in price_data]
        high_prices = [float(p.high_price) for p in price_data]
        low_prices = [float(p.low_price) for p in price_data]
        
        # Enhanced pivot point detection using high/low prices
        supports = []
        resistances = []
        
        for i in range(2, len(close_prices) - 2):
            current_low = low_prices[i]
            current_high = high_prices[i]
            
            # Check for local minimum (support) - use low prices
            if (low_prices[i] < low_prices[i-1] and low_prices[i] < low_prices[i+1] and
                low_prices[i] < low_prices[i-2] and low_prices[i] < low_prices[i+2]):
                supports.append(current_low)
            
            # Check for local maximum (resistance) - use high prices  
            if (high_prices[i] > high_prices[i-1] and high_prices[i] > high_prices[i+1] and
                high_prices[i] > high_prices[i-2] and high_prices[i] > high_prices[i+2]):
                resistances.append(current_high)
        
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
        """
        Calculate price correlation between two assets using time-based alignment
        
        Uses tolerance-based timestamp matching for better correlation accuracy
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get aligned price data for both assets
        prices1 = self.db.query(PriceData.candle_time, PriceData.close_price).filter(
            PriceData.asset_id == asset1_id,
            PriceData.candle_time >= cutoff_date
        ).order_by(PriceData.candle_time.asc()).all()
        
        prices2 = self.db.query(PriceData.candle_time, PriceData.close_price).filter(
            PriceData.asset_id == asset2_id,
            PriceData.candle_time >= cutoff_date
        ).order_by(PriceData.candle_time.asc()).all()
        
        if len(prices1) < 10 or len(prices2) < 10:
            return {'correlation': None, 'data_points': 0}
        
        # Create time-based alignment with tolerance for slight time differences
        aligned_prices1 = []
        aligned_prices2 = []
        time_tolerance = timedelta(minutes=5)  # 5-minute tolerance for timestamp matching
        
        for p1 in prices1:
            # Find the closest timestamp in prices2
            closest_p2 = None
            min_time_diff = timedelta.max
            
            for p2 in prices2:
                time_diff = abs(p1.candle_time - p2.candle_time)
                if time_diff <= time_tolerance and time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_p2 = p2
            
            if closest_p2:
                aligned_prices1.append(float(p1.close_price))
                aligned_prices2.append(float(closest_p2.close_price))
        
        aligned_prices1 = []
        if len(aligned_prices1) < 10:
            return {'correlation': None, 'data_points': len(aligned_prices1)}
        
        # Calculate Pearson correlation coefficient
        import statistics
        
        try:
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
                'period_days': days,
                'time_tolerance_minutes': int(time_tolerance.total_seconds() / 60),
                'alignment_method': 'time_based_with_tolerance'
            }
            
        except (ZeroDivisionError, ValueError) as e:
            return {
                'correlation': None,
                'data_points': len(aligned_prices1),
                'period_days': days,
                'error': f'Calculation error: {str(e)}'
            }
    
    def get_data_quality_report(self, asset_id: int, days: int = 7) -> Dict[str, Any]:
        """Generate data quality report for an asset"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        total_records = self.db.query(func.count(PriceData.id)).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_date
        ).scalar()
        
        # Check for missing required fields
        missing_price = self.db.query(func.count(PriceData.id)).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_date,
            PriceData.close_price.is_(None)
        ).scalar()
        
        missing_volume = self.db.query(func.count(PriceData.id)).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_date,
            PriceData.volume.is_(None)
        ).scalar()
        
        # Check for suspicious values (e.g., zero prices)
        zero_prices = self.db.query(func.count(PriceData.id)).filter(
            PriceData.asset_id == asset_id,
            PriceData.candle_time >= cutoff_date,
            PriceData.close_price <= 0
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
        
        # Simplified approach: Use DISTINCT ON for first/last values
        # This is more reliable than complex subqueries
        
        # First, get the main aggregation (everything except open/close)
        period_start = func.date_trunc(interval_expression, PriceData.candle_time).label('period_start')
        
        aggregation_query = self.db.query(
            period_start,
            func.max(PriceData.high_price).label('high_price'),
            func.min(PriceData.low_price).label('low_price'),
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
            period_start
        ).order_by(
            period_start.asc()
        )
        
        # Get main aggregation results
        agg_results = aggregation_query.all()
        
        # Debug: Log the actual number of results
        logger.info(f"DEBUG: Aggregation query returned {len(agg_results)} periods for {target_timeframe}")
        for i, row in enumerate(agg_results):
            logger.info(f"DEBUG: Period {i+1}: {row.period_start} (source_records: {row.source_records})")
        
        # Now get first/last values for each period using simpler queries
        first_last_data = {}
        for row in agg_results:
            period = row.period_start
            
            # Get first record of this period (for open_price)
            first_record = self.db.query(PriceData).filter(
                PriceData.asset_id == asset_id,
                PriceData.timeframe == source_timeframe,
                func.date_trunc(interval_expression, PriceData.candle_time) == period,
                *base_conditions
            ).order_by(PriceData.candle_time.asc()).first()
            
            # Get last record of this period (for close_price)
            last_record = self.db.query(PriceData).filter(
                PriceData.asset_id == asset_id,
                PriceData.timeframe == source_timeframe,
                func.date_trunc(interval_expression, PriceData.candle_time) == period,
                *base_conditions
            ).order_by(PriceData.candle_time.desc()).first()
            
            first_last_data[period] = {
                'first_open': first_record.open_price if first_record else 0,
                'last_close': last_record.close_price if last_record else 0
            }
        
        # Convert to dictionary format using first_last_data
        aggregated_data = []
        for row in agg_results:
            period_time = row.period_start
            first_last = first_last_data.get(period_time, {'first_open': 0, 'last_close': 0})
            
            aggregated_data.append({
                'asset_id': asset_id,
                'timeframe': target_timeframe,
                'candle_time': period_time,
                'open_price': float(first_last['first_open']) if first_last['first_open'] else 0,
                'high_price': float(row.high_price) if row.high_price else 0,
                'low_price': float(row.low_price) if row.low_price else 0,
                'close_price': float(first_last['last_close']) if first_last['last_close'] else 0,
                'volume': float(row.volume) if row.volume else 0,
                'market_cap': float(row.avg_market_cap) if row.avg_market_cap else None,
                'trade_count': int(row.total_trades) if row.total_trades else None,
                'vwap': float(row.vwap) if row.vwap else None,
                'is_validated': False  # Aggregated data needs validation
                # Note: source_records (row.source_records) is available for logging/debugging but not stored in PriceData model
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
                
                # Store aggregated data efficiently using bulk operations
                stored_count = self._bulk_upsert_aggregated_data(
                    aggregated_data=aggregated_data,
                    asset_id=asset_id,
                    target_timeframe=target_tf
                )
                
                self.db.commit()
                results[target_tf] = stored_count
                
                # Update timeframe cache for the target timeframe
                self._update_asset_timeframe_cache(asset_id, target_tf, 'refresh')
                
            except Exception as e:
                self.db.rollback()
                results[target_tf] = f"Error: {str(e)}"
        
        return results

    def get_aggregation_status(self, asset_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Get aggregation status showing available data for each timeframe
        
        Uses cached timeframe_data from asset table for optimal performance
        Falls back to price_data query if cache is empty
        
        Returns:
            Dictionary with timeframe -> {count, latest_time, earliest_time}
        """
        from ...models.asset import Asset
        
        # Get asset with timeframe_data cache
        asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
        
        if not asset:
            return {}
        
        # Use cached data if available
        if asset.timeframe_data:
            return asset.get_all_timeframe_data()
        
        # Fallback: query price_data directly and update cache
        hierarchy = self.get_timeframe_hierarchy()
        status = {}
        
        for timeframe in hierarchy.keys():
            data_stats = self.db.query(
                func.count(PriceData.id).label('count'),
                func.max(PriceData.candle_time).label('latest_time'),
                func.min(PriceData.candle_time).label('earliest_time')
            ).filter(
                PriceData.asset_id == asset_id,
                PriceData.timeframe == timeframe
            ).first()
            
            count = data_stats.count if data_stats else 0
            latest = data_stats.latest.isoformat() if data_stats.latest else None
            earliest = data_stats.earliest.isoformat() if data_stats.earliest else None
            
            status[timeframe] = {
                'count': count,
                'latest_time': latest,
                'earliest_time': earliest,
                'can_aggregate_to': self.get_aggregatable_timeframes(timeframe)
            }
            
            # Update cache
            if count > 0:
                asset.update_timeframe_data(
                    timeframe=timeframe,
                    count=count,
                    earliest_time=earliest,
                    latest_time=latest
                )
        
        # Commit cache updates
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
        
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

    def _update_asset_timeframe_cache(self, asset_id: int, timeframe: str, 
                                    operation: str = 'refresh') -> bool:
        """
        Update asset timeframe_data cache after price data changes
        
        Args:
            asset_id: Asset ID to update
            timeframe: Timeframe that was modified
            operation: 'refresh' (recalculate), 'clear' (reset cache)
            
        Returns:
            Success status
        """
        try:
            from ...models.asset import Asset
            
            asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset:
                return False
            
            if operation == 'clear':
                asset.reset_timeframe_cache()
                self.db.commit()
                return True
            
            # Refresh cache for specific timeframe
            data_stats = self.db.query(
                func.count(PriceData.id).label('count'),
                func.max(PriceData.candle_time).label('latest_time'),
                func.min(PriceData.candle_time).label('earliest_time')
            ).filter(
                PriceData.asset_id == asset_id,
                PriceData.timeframe == timeframe
            ).first()
            
            count = data_stats.count if data_stats else 0
            latest = data_stats.latest.isoformat() if data_stats.latest else None
            earliest = data_stats.earliest.isoformat() if data_stats.earliest else None
            
            asset.update_timeframe_data(
                timeframe=timeframe,
                count=count,
                earliest_time=earliest,
                latest_time=latest
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            # Log error but don't fail the main operation
            return False

    def _bulk_upsert_aggregated_data(self, aggregated_data: List[Dict[str, Any]], 
                                   asset_id: int, target_timeframe: str) -> int:
        """
        Efficiently bulk upsert aggregated data using simple candle_time logic
        
        Simple Logic:
        - If candle_time == latest_candle_time: UPDATE (last candle may have new data)
        - If candle_time > latest_candle_time: INSERT (new candle)
        - If candle_time < latest_candle_time: SKIP (historical complete candle)
        
        This approach is much simpler and more efficient than complex period analysis.
        
        Args:
            aggregated_data: List of aggregated price data dictionaries
            asset_id: Asset ID for filtering
            target_timeframe: Target timeframe for filtering
            
        Returns:
            Number of records processed (inserted + updated)
        """
        if not aggregated_data:
            return 0
        
        try:
            # Step 1: Get the latest candle_time for this asset and timeframe
            latest_candle_record = self.db.query(PriceData.candle_time).filter(
                PriceData.asset_id == asset_id,
                PriceData.timeframe == target_timeframe
            ).order_by(PriceData.candle_time.desc()).first()
            
            latest_candle_time = latest_candle_record.candle_time if latest_candle_record else None
            
            # Step 2: Normalize latest candle time to timeframe boundary
            if latest_candle_time:
                latest_candle_time = self._normalize_candle_time(latest_candle_time, target_timeframe)
            
            # Step 3: Separate data based on normalized candle_time comparison
            records_to_insert = []  # candle_time > latest_candle_time
            records_to_update = []  # candle_time == latest_candle_time
            records_to_skip = []    # candle_time < latest_candle_time (complete historical data)
            
            for data in aggregated_data:
                candle_time = data['candle_time']
                
                # Normalize incoming candle time to timeframe boundary
                normalized_candle_time = self._normalize_candle_time(candle_time, target_timeframe)
                
                if latest_candle_time is None:
                    # No existing data - insert all
                    records_to_insert.append(data)
                elif normalized_candle_time > latest_candle_time:
                    # New candle - insert
                    records_to_insert.append(data)
                elif normalized_candle_time == latest_candle_time:
                    # Latest candle - update (may have new aggregated data)
                    records_to_update.append(data)
                else:
                    # Historical candle - skip (already complete)
                    records_to_skip.append(data)
            
            # Step 3: Bulk insert new records
            inserted_count = 0
            if records_to_insert:
                new_objects = [PriceData(**data) for data in records_to_insert]
                self.db.add_all(new_objects)
                inserted_count = len(new_objects)
            
            # Step 4: Update latest candle if it exists
            updated_count = 0
            if records_to_update and latest_candle_time:
                # Get the existing record to update using normalized time
                existing_record = self.db.query(PriceData).filter(
                    PriceData.asset_id == asset_id,
                    PriceData.timeframe == target_timeframe,
                    PriceData.candle_time == latest_candle_time
                ).first()
                
                if existing_record and records_to_update:
                    # Update with the latest aggregated data
                    update_data = records_to_update[0]  # Should only be one record with latest time
                    for key, value in update_data.items():
                        if key not in ['asset_id', 'timeframe', 'candle_time']:
                            setattr(existing_record, key, value)
                    updated_count = 1
            
            # Commit all changes in one transaction
            self.db.commit()
            
            # Log efficiency metrics
            total_input = len(aggregated_data)
            total_processed = inserted_count + updated_count
            skipped_count = len(records_to_skip)
            
            if skipped_count > 0:
                # This is excellent - we're avoiding unnecessary work on complete historical data
                efficiency_gain = (skipped_count / total_input) * 100
                # Could log: f"Efficiency: {skipped_count}/{total_input} historical candles skipped ({efficiency_gain:.1f}% gain)"
            
            return total_processed
            
        except Exception as e:
            self.db.rollback()
            raise e

    def _bulk_upsert_with_postgresql_on_conflict(self, aggregated_data: List[Dict[str, Any]]) -> int:
        """
        Alternative implementation using PostgreSQL's ON CONFLICT (even more efficient)
        
        This reduces the operation to a single SQL statement with ON CONFLICT DO UPDATE
        Perfect for PostgreSQL databases with high-performance requirements
        
        Args:
            aggregated_data: List of aggregated price data dictionaries
            
        Returns:
            Number of records processed
        """
        if not aggregated_data:
            return 0
        
        try:
            from sqlalchemy import text
            
            # Build bulk INSERT ... ON CONFLICT DO UPDATE statement
            sql = """
                INSERT INTO price_data (
                    asset_id, timeframe, candle_time, open_price, high_price, 
                    low_price, close_price, volume, market_cap, trade_count, vwap, 
                    is_validated
                ) VALUES """
            
            # Add value placeholders
            value_sets = []
            params = {}
            
            for i, data in enumerate(aggregated_data):
                value_set = f"""(
                    :asset_id_{i}, :timeframe_{i}, :candle_time_{i}, :open_price_{i}, 
                    :high_price_{i}, :low_price_{i}, :close_price_{i}, :volume_{i}, 
                    :market_cap_{i}, :trade_count_{i}, :vwap_{i}, 
                    :is_validated_{i}
                )"""
                value_sets.append(value_set)
                
                # Add parameters
                for key, value in data.items():
                    params[f"{key}_{i}"] = value
            
            sql += ", ".join(value_sets)
            
            # Add ON CONFLICT clause
            sql += """
                ON CONFLICT (asset_id, timeframe, candle_time) 
                DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume,
                    market_cap = EXCLUDED.market_cap,
                    trade_count = EXCLUDED.trade_count,
                    vwap = EXCLUDED.vwap,
                    is_validated = EXCLUDED.is_validated,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            # Execute the bulk upsert
            result = self.db.execute(text(sql), params)
            self.db.commit()
            
            # Return the actual number of rows affected by the SQL operation
            # result.rowcount gives us the number of rows inserted/updated
            actual_rows_affected = result.rowcount if result.rowcount is not None else len(aggregated_data)
            
            return actual_rows_affected
            
        except Exception as e:
            self.db.rollback()
            raise e

    def _filter_incomplete_periods(self, records_to_update: List[Tuple], 
                                  target_timeframe: str, asset_id: int) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Filter records to only update incomplete periods (smart optimization)
        
        Logic: A period is incomplete if it could still receive new data based on
        the latest timestamp recorded in the database for this asset.
        
        Args:
            records_to_update: List of (existing_record, new_data) tuples
            target_timeframe: Target timeframe (e.g., '1M', '1w', '1d')
            asset_id: Asset ID to get latest timestamp for
            
        Returns:
            Tuple of (incomplete_updates, complete_skips)
        """
        # Get the latest timestamp from the database for this asset and target timeframe
        latest_db_record = self.db.query(PriceData.candle_time).filter(
            PriceData.asset_id == asset_id,
            PriceData.timeframe == target_timeframe
        ).order_by(PriceData.candle_time.desc()).first()
        
        if not latest_db_record:
            # No existing data - all periods are incomplete
            return records_to_update, []
        
        latest_db_time = latest_db_record.candle_time
        
        # Convert to timezone-aware if needed
        if latest_db_time.tzinfo is None:
            from datetime import timezone
            latest_db_time = latest_db_time.replace(tzinfo=timezone.utc)
        
        incomplete_updates = []
        complete_skips = []
        
        for existing_record, new_data in records_to_update:
            candle_time = new_data['candle_time']
            
            # Convert to timezone-aware if needed
            if candle_time.tzinfo is None:
                from datetime import timezone
                candle_time = candle_time.replace(tzinfo=timezone.utc)
            
            is_incomplete = self._is_incomplete_period(candle_time, target_timeframe, latest_db_time)
            
            if is_incomplete:
                incomplete_updates.append((existing_record, new_data))
            else:
                complete_skips.append((existing_record, new_data))
        
        return incomplete_updates, complete_skips

    def _is_incomplete_period(self, candle_time: datetime, timeframe: str, 
                            latest_db_time: datetime) -> bool:
        """
        Determine if a period is incomplete and needs updating based on latest database timestamp
        
        Logic: A period is incomplete if it could potentially receive more data based on
        the latest timestamp recorded in the database for this asset/timeframe combination.
        
        Args:
            candle_time: Start time of the aggregated period
            timeframe: Target timeframe ('1M', '1w', '1d', '4h')
            latest_db_time: Latest timestamp recorded in database for this asset
            
        Returns:
            True if period is incomplete and needs updating
        """
        from datetime import timedelta
        
        if timeframe == '1M':
            # Monthly: Check if period contains the latest database timestamp
            # A month is incomplete if latest data falls within that month
            next_month_start = (candle_time.replace(day=28) + timedelta(days=4)).replace(day=1)
            
            return candle_time <= latest_db_time < next_month_start
            
        elif timeframe == '1w':
            # Weekly: Check if period contains the latest database timestamp
            # A week is incomplete if latest data falls within that week (7 days)
            week_end = candle_time + timedelta(days=7)
            
            return candle_time <= latest_db_time < week_end
            
        elif timeframe == '1d':
            # Daily: Check if period contains the latest database timestamp
            # A day is incomplete if latest data falls within that day (24 hours)
            day_end = candle_time + timedelta(days=1)
            
            return candle_time <= latest_db_time < day_end
            
        elif timeframe == '4h':
            # 4-hour periods: Check if period contains the latest database timestamp
            period_end = candle_time + timedelta(hours=4)
            
            return candle_time <= latest_db_time < period_end
            
        elif timeframe == '1h':
            # 1-hour periods: Check if period contains the latest database timestamp
            period_end = candle_time + timedelta(hours=1)
            
            return candle_time <= latest_db_time < period_end
            
        else:
            # For other timeframes, calculate period end dynamically
            hierarchy = self.get_timeframe_hierarchy()
            period_minutes = hierarchy.get(timeframe, {}).get('minutes', 60)
            period_end = candle_time + timedelta(minutes=period_minutes)
            
            return candle_time <= latest_db_time < period_end

    def _normalize_candle_time(self, candle_time: datetime, timeframe: str) -> datetime:
        """
        Normalize candle_time to timeframe boundary for accurate comparison
        
        This ensures that candle times are trimmed to their timeframe boundaries:
        - 1M: Trim to start of month (day=1, hour=0, minute=0, second=0)
        - 1w: Trim to start of week (Monday, hour=0, minute=0, second=0)  
        - 1d: Trim to start of day (hour=0, minute=0, second=0)
        - 4h: Trim to 4-hour boundaries (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
        - 1h: Trim to start of hour (minute=0, second=0)
        - 15m: Trim to 15-minute boundaries (00, 15, 30, 45 minutes)
        - 5m: Trim to 5-minute boundaries (00, 05, 10, 15, etc.)
        - 1m: Trim to start of minute (second=0)
        
        Args:
            candle_time: Original candle timestamp
            timeframe: Target timeframe for normalization
            
        Returns:
            Normalized candle timestamp aligned to timeframe boundary
        """
        from datetime import timedelta
        
        # Ensure timezone consistency
        if candle_time.tzinfo is None:
            from datetime import timezone
            candle_time = candle_time.replace(tzinfo=timezone.utc)
        
        if timeframe == '1M':
            # Monthly: Trim to start of month
            return candle_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
        elif timeframe == '1w':
            # Weekly: Trim to start of week (Monday)
            days_since_monday = candle_time.weekday()
            week_start = candle_time - timedelta(days=days_since_monday)
            return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
        elif timeframe == '1d':
            # Daily: Trim to start of day
            return candle_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
        elif timeframe == '4h':
            # 4-hour periods: Trim to 4-hour boundaries (00, 04, 08, 12, 16, 20)
            normalized_hour = (candle_time.hour // 4) * 4
            return candle_time.replace(hour=normalized_hour, minute=0, second=0, microsecond=0)
            
        elif timeframe == '1h':
            # Hourly: Trim to start of hour
            return candle_time.replace(minute=0, second=0, microsecond=0)
            
        elif timeframe == '15m':
            # 15-minute periods: Trim to 15-minute boundaries (00, 15, 30, 45)
            normalized_minute = (candle_time.minute // 15) * 15
            return candle_time.replace(minute=normalized_minute, second=0, microsecond=0)
            
        elif timeframe == '5m':
            # 5-minute periods: Trim to 5-minute boundaries (00, 05, 10, 15, etc.)
            normalized_minute = (candle_time.minute // 5) * 5
            return candle_time.replace(minute=normalized_minute, second=0, microsecond=0)
            
        elif timeframe == '1m':
            # 1-minute periods: Trim to start of minute
            return candle_time.replace(second=0, microsecond=0)
            
        else:
            # For unknown timeframes, get minutes from hierarchy and calculate boundary
            hierarchy = self.get_timeframe_hierarchy()
            timeframe_minutes = hierarchy.get(timeframe, {}).get('minutes', 1)
            
            if timeframe_minutes >= 1440:  # Daily or larger
                return candle_time.replace(hour=0, minute=0, second=0, microsecond=0)
            elif timeframe_minutes >= 60:  # Hourly or larger  
                normalized_hour = (candle_time.hour // (timeframe_minutes // 60)) * (timeframe_minutes // 60)
                return candle_time.replace(hour=normalized_hour, minute=0, second=0, microsecond=0)
            else:  # Minutes
                normalized_minute = (candle_time.minute // timeframe_minutes) * timeframe_minutes
                return candle_time.replace(minute=normalized_minute, second=0, microsecond=0)

    async def get_latest_market_cap(self, asset_id: int) -> Optional[float]:
        """
        Get the latest market cap from database (prioritizing more recent timeframes)
        
        Args:
            asset_id: Asset ID
            
        Returns:
            Latest market cap or None if not found
        """
        try:
            # Try to get market cap from different timeframes, starting with most recent
            timeframes_to_try = ['1h', '4h', '1d', '1w']
            
            for timeframe in timeframes_to_try:
                latest_record = self.db.query(PriceData).filter(
                    and_(
                        PriceData.asset_id == asset_id,
                        PriceData.timeframe == timeframe,
                        PriceData.market_cap.isnot(None),
                        PriceData.market_cap > 0
                    )
                ).order_by(desc(PriceData.candle_time)).first()
                
                if latest_record and latest_record.market_cap:
                    return float(latest_record.market_cap)
            
            return None
            
        except Exception as e:
            # Import logger here to avoid circular imports
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get latest market cap from DB for asset {asset_id}: {e}")
            return None

    async def get_latest_candle_data(self, asset_id: int, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest candle data from database for specified timeframe
        
        Args:
            asset_id: Asset ID
            timeframe: Timeframe ('1d', '1w', '1M' for daily, weekly, monthly)
            
        Returns:
            Dictionary with latest candle data or None if not found
        """
        try:
            # Get the latest candle for the specified timeframe
            latest_candle = self.db.query(PriceData).filter(
                and_(
                    PriceData.asset_id == asset_id,
                    PriceData.timeframe == timeframe
                )
            ).order_by(desc(PriceData.candle_time)).first()
            
            if not latest_candle:
                return None
            
            # Return comprehensive candle data
            candle_data = {
                'candle_time': latest_candle.candle_time,
                'open_price': float(latest_candle.open_price),
                'close_price': float(latest_candle.close_price),
                'high_price': float(latest_candle.high_price),
                'low_price': float(latest_candle.low_price),
                'volume': float(latest_candle.volume) if latest_candle.volume else 0,
                'market_cap': float(latest_candle.market_cap) if latest_candle.market_cap else None,
                'timeframe': timeframe
            }
            
            # Calculate price change within this candle
            if latest_candle.open_price and latest_candle.close_price:
                open_price = float(latest_candle.open_price)
                close_price = float(latest_candle.close_price)
                if open_price > 0:
                    candle_data['price_change_percent'] = ((close_price - open_price) / open_price) * 100
                else:
                    candle_data['price_change_percent'] = 0
            else:
                candle_data['price_change_percent'] = 0
            
            return candle_data
            
        except Exception as e:
            # Import logger here to avoid circular imports
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get latest {timeframe} candle for asset {asset_id}: {e}")
            return None

    async def calculate_multi_period_change(self, asset_id: int, timeframe: str, periods: int) -> Optional[float]:
        """
        Calculate price change over multiple periods (e.g., 4 weeks for 30d)
        
        Args:
            asset_id: Asset ID
            timeframe: Base timeframe ('1w' for weekly)
            periods: Number of periods to look back
            
        Returns:
            Price change percentage or None
        """
        try:
            # Get the last N candles
            candles = self.db.query(PriceData).filter(
                and_(
                    PriceData.asset_id == asset_id,
                    PriceData.timeframe == timeframe
                )
            ).order_by(desc(PriceData.candle_time)).limit(periods).all()
            
            if len(candles) < periods:
                return None
            
            # Get current (latest) and past prices
            latest_candle = candles[0]
            oldest_candle = candles[-1]
            
            current_price = float(latest_candle.close_price)
            past_price = float(oldest_candle.open_price)
            
            if past_price <= 0:
                return None
            
            # Calculate percentage change
            change_percent = ((current_price - past_price) / past_price) * 100
            
            return change_percent
            
        except Exception as e:
            # Import logger here to avoid circular imports
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to calculate multi-period change for asset {asset_id}: {e}")
            return None
