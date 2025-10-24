# Example service for timeframe aggregation
# backend/app/services/timeframe_aggregation_service.py

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from ..repositories.asset.price_data_repository import PriceDataRepository
from ..repositories.asset.asset_repository import AssetRepository
from ..external.coingecko import CoinGeckoClient
from .price_data_service import PriceDataService
from .data_quality_service import DataQualityService

logger = logging.getLogger(__name__)


class TimeframeAggregationService:
    """
    Service for managing timeframe aggregation operations
    
    This service provides high-level methods for:
    - Automated timeframe aggregation
    - Storage optimization 
    - Data quality maintenance
    - Performance monitoring
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.price_repo = PriceDataRepository(db)
        self.asset_repo = AssetRepository(db)
        self.coingecko_client = CoinGeckoClient()
        self.price_data_service = PriceDataService(db)
        self.data_quality_service = DataQualityService(db)
    
    def auto_aggregate_for_asset(self, asset_id: int, 
                               source_timeframe: str = '1h',
                               force_refresh: bool = False) -> Dict[str, Any]:
        """
        Automatically aggregate price data for an asset
        
        Args:
            asset_id: Asset to process
            source_timeframe: Base timeframe to aggregate from
            force_refresh: Whether to re-aggregate existing data
            
        Returns:
            Aggregation results and status
        """
        try:
            # Get asset info
            asset = self.asset_repo.get_by_id(asset_id)
            if not asset:
                return {'error': f'Asset {asset_id} not found'}
            
            # Check what timeframes we can aggregate to
            target_timeframes = self.price_repo.get_aggregatable_timeframes(source_timeframe)
            
            if not target_timeframes:
                return {
                    'asset_id': asset_id,
                    'symbol': asset.symbol,
                    'message': f'No aggregatable timeframes for {source_timeframe}',
                    'aggregated_timeframes': []
                }
            
            # Get current status
            status_before = self.price_repo.get_aggregation_status(asset_id)
            
            # Determine time range for aggregation
            source_data_count = status_before.get(source_timeframe, {}).get('count', 0)
            if source_data_count == 0:
                return {
                    'asset_id': asset_id,
                    'symbol': asset.symbol,
                    'error': f'No {source_timeframe} data available for aggregation'
                }
            
            # Calculate individual optimal aggregation windows for each target timeframe
            aggregation_results = {}
            
            if not force_refresh:
                # Process each target timeframe with its own optimal window
                for target_timeframe in target_timeframes:
                    try:
                        # Calculate specific window for this target timeframe
                        aggregation_window = self._calculate_timeframe_specific_window(
                            asset_id=asset_id,
                            source_timeframe=source_timeframe,
                            target_timeframe=target_timeframe
                        )
                        
                        # Perform aggregation for this specific timeframe
                        result = self.price_repo.bulk_aggregate_and_store(
                            asset_id=asset_id,
                            source_timeframe=source_timeframe,
                            target_timeframes=[target_timeframe],
                            start_time=aggregation_window['start_time'],
                            end_time=aggregation_window['end_time']
                        )
                        
                        aggregation_results[target_timeframe] = {
                            'records': result.get(target_timeframe, 0),
                            'window': aggregation_window,
                            'status': 'success'
                        }
                        
                    except Exception as e:
                        aggregation_results[target_timeframe] = {
                            'records': 0,
                            'error': str(e),
                            'status': 'error'
                        }
            else:
                # Force refresh - process all timeframes together
                result = self.price_repo.bulk_aggregate_and_store(
                    asset_id=asset_id,
                    source_timeframe=source_timeframe,
                    target_timeframes=target_timeframes,
                    start_time=None,
                    end_time=None
                )
                
                for tf in target_timeframes:
                    aggregation_results[tf] = {
                        'records': result.get(tf, 0),
                        'window': {'method': 'force_refresh_all_data'},
                        'status': 'success'
                    }
            
            # Update timeframe_data fields in assets table after successful aggregation
            self._update_asset_timeframe_data(asset_id, aggregation_results)
            
            # Get status after aggregation and timeframe updates
            status_after = self.price_repo.get_aggregation_status(asset_id)
            
            return {
                'asset_id': asset_id,
                'symbol': asset.symbol,
                'source_timeframe': source_timeframe,
                'aggregated_timeframes': target_timeframes,
                'results': aggregation_results,
                'status_before': status_before,
                'status_after': status_after,
                'window_optimization': 'individual_timeframe_windows' if not force_refresh else 'force_refresh_all_data'
            }
            
        except Exception as e:
            return {
                'asset_id': asset_id,
                'error': f'Aggregation failed: {str(e)}'
            }

    def _update_asset_timeframe_data(self, asset_id: int, aggregation_results: Dict[str, Any]) -> None:
        """
        Update timeframe_data fields in assets table after successful aggregation
        
        Args:
            asset_id: Asset ID to update
            aggregation_results: Results from aggregation process
        """
        try:
            # Get the asset record
            asset = self.asset_repo.get_by_id(asset_id)
            if not asset:
                logger.warning(f"Asset {asset_id} not found for timeframe data update")
                return
            
            # Get current status to get latest times and counts
            current_status = self.price_repo.get_aggregation_status(asset_id)
            
            updated_timeframes = []
            
            # Update timeframe data for successfully aggregated timeframes
            for timeframe, result in aggregation_results.items():
                if result.get('status') == 'success' and result.get('records', 0) > 0:
                    # Get stats from current status
                    timeframe_stats = current_status.get(timeframe, {})
                    count = timeframe_stats.get('count', 0)
                    earliest_time = timeframe_stats.get('earliest_time')
                    latest_time = timeframe_stats.get('latest_time')
                    
                    if count > 0:
                        # Update the asset's timeframe_data cache using the model method
                        asset.update_timeframe_data(
                            timeframe=timeframe,
                            count=count,
                            earliest_time=earliest_time,
                            latest_time=latest_time
                        )
                        updated_timeframes.append(timeframe)
            
            # If no specific timeframes were processed, refresh all timeframe data
            if not updated_timeframes:
                # Refresh the entire timeframe_data cache from database
                asset.refresh_timeframe_data_from_db(self.db)
                logger.info(f"Refreshed complete timeframe data cache for asset {asset_id}")
            
            # Commit the updates
            if updated_timeframes:
                self.db.commit()
                logger.info(f"Updated asset {asset_id} timeframe data for: {', '.join(updated_timeframes)}")
            else:
                self.db.commit()
                logger.debug(f"Refreshed timeframe data cache for asset {asset_id}")
                
        except Exception as e:
            logger.error(f"Failed to update timeframe data for asset {asset_id}: {str(e)}")
            self.db.rollback()
    

    def _calculate_timeframe_specific_window(self, asset_id: int, source_timeframe: str, 
                                           target_timeframe: str) -> Dict[str, Any]:
        """
        Calculate optimal aggregation window specific to each target timeframe
        
        Different timeframes need different aggregation windows:
        - Monthly (1M): At least 30+ days to ensure complete months
        - Weekly (1w): At least 7+ days to ensure complete weeks
        - Daily (1d): At least 1+ days 
        - 4-hour (4h): At least 8+ hours to ensure multiple periods
        - Hourly (1h): At least 1+ hours
        
        Args:
            asset_id: Asset ID to analyze
            source_timeframe: Source timeframe for aggregation
            target_timeframe: Specific target timeframe to optimize for
            
        Returns:
            Optimal window configuration for this specific timeframe
        """
        from datetime import datetime, timedelta
        
        try:
            # Get current aggregation status
            status = self.price_repo.get_aggregation_status(asset_id)
            source_info = status.get(source_timeframe, {})
            target_info = status.get(target_timeframe, {})
            
            # Get latest times
            source_latest = source_info.get('latest_time')
            target_latest = target_info.get('latest_time')
            
            if not source_latest:
                return {
                    'start_time': None,
                    'end_time': None,
                    'method': 'no_source_data',
                    'target_timeframe': target_timeframe
                }
            
            source_latest_dt = datetime.fromisoformat(source_latest.replace('Z', '+00:00'))
            target_latest_dt = None
            if target_latest:
                target_latest_dt = datetime.fromisoformat(target_latest.replace('Z', '+00:00'))
            
            # Calculate minimum window based on target timeframe requirements
            if target_timeframe == '1M':
                # Monthly: Need at least 30+ days, go back further if no recent aggregation
                min_days = 35  # Extra buffer for month boundaries
                if target_latest_dt:
                    days_since_last = (source_latest_dt - target_latest_dt).days
                    # If last aggregation was more than a week ago, extend window
                    if days_since_last > 7:
                        min_days = max(min_days, days_since_last + 10)
                
            elif target_timeframe == '1w':
                # Weekly: Need at least 10+ days
                min_days = 12  # Extra buffer for week boundaries
                if target_latest_dt:
                    days_since_last = (source_latest_dt - target_latest_dt).days
                    if days_since_last > 3:
                        min_days = max(min_days, days_since_last + 5)
                
            elif target_timeframe == '1d':
                # Daily: Need at least 2+ days
                min_days = 3
                if target_latest_dt:
                    days_since_last = (source_latest_dt - target_latest_dt).days
                    if days_since_last > 1:
                        min_days = max(min_days, days_since_last + 1)
                
            elif target_timeframe == '4h':
                # 4-hour: Need at least 1+ day (6 periods)
                min_days = 2
                if target_latest_dt:
                    days_since_last = (source_latest_dt - target_latest_dt).days
                    if days_since_last > 0:
                        min_days = max(min_days, days_since_last + 1)
                        
            elif target_timeframe == '1h':
                # Hourly: Need at least few hours
                min_days = 1
                if target_latest_dt:
                    hours_since_last = (source_latest_dt - target_latest_dt).total_seconds() / 3600
                    if hours_since_last > 2:
                        min_days = max(min_days, int(hours_since_last / 24) + 1)
            else:
                # Default: 7 days
                min_days = 7
            
            # Calculate optimal window
            end_time = source_latest_dt
            start_time = source_latest_dt - timedelta(days=min_days)
            
            # If we have existing target data, only go back to cover the gap plus buffer
            if target_latest_dt and target_latest_dt > start_time:
                # Add buffer based on timeframe
                if target_timeframe == '1M':
                    buffer_days = 7  # 1 week buffer for monthly
                elif target_timeframe == '1w':
                    buffer_days = 2  # 2 day buffer for weekly
                elif target_timeframe == '1d':
                    buffer_days = 1  # 1 day buffer for daily
                else:
                    buffer_days = 1
                
                start_time = target_latest_dt - timedelta(days=buffer_days)
            
            return {
                'start_time': start_time,
                'end_time': end_time,
                'method': 'timeframe_specific_optimization',
                'target_timeframe': target_timeframe,
                'window_days': (end_time - start_time).days,
                'rationale': f'Optimized for {target_timeframe}: {min_days} day minimum window',
                'source_latest': source_latest,
                'target_latest': target_latest,
                'gap_analysis': {
                    'days_since_last_aggregation': (source_latest_dt - target_latest_dt).days if target_latest_dt else 'first_time',
                    'window_extension': 'extended' if target_latest_dt and (source_latest_dt - target_latest_dt).days > 7 else 'standard'
                }
            }
            
        except Exception as e:
            return {
                'start_time': None,
                'end_time': None,
                'method': 'error',
                'target_timeframe': target_timeframe,
                'error': str(e)
            }

