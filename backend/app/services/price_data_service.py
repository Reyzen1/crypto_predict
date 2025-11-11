# backend/app/services/price_data_service.py
# Service for price data management with timeframe support

from fileinput import close
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import logging
from sqlalchemy.orm import Session

from app.external.coingecko import CoinGeckoClient
from app.external.binance import BinanceClient
from app.external.tradingview import TradingViewClient

from app.repositories.asset.price_data_repository import PriceDataRepository
from app.repositories.asset.asset_repository import AssetRepository
from app.models.asset.asset import Asset
from app.models.asset.price_data import PriceData
from app.utils.datetime_utils import normalize_datetime, compare_datetimes, serialize_datetime_objects, normalize_candle_time, timeframe_to_minutes
from app.services import external_api

logger = logging.getLogger(__name__)


class PriceDataService:
    """
    Service for managing price data operations with timeframe support and aggregation
    
    This consolidated service provides:
    - Price data population from external sources
    - Data processing and validation
    - Timeframe normalization
    - Automated timeframe aggregation
    - Storage optimization
    - Asset metadata updates
    """
    
    def __init__(self, db: Session):
        self.db = db

        self.coingecko_client = CoinGeckoClient()
        self.binance_client = BinanceClient()
        self.tradingview_client = TradingViewClient()
        self.client_map = {
            "coingecko": self.coingecko_client,
            "binance": self.binance_client,
            "tradingview": self.tradingview_client,
        }

        self.price_data_repo = PriceDataRepository(db)
        self.asset_repo = AssetRepository(db)
    
    async def populate_price_data(
        self,
        asset: Asset,
        days: Optional[int] = None,
        timeframe: str = "1d",
        vs_currency: str = "usd",
        platform: str = "binance"
    ) -> Dict[str, Any]:
        """
        Complete price data population for an asset with timeframe support
        
        Args:
            asset: Asset object to populate data for
            days: Number of days of historical data (auto-calculated if None)
            timeframe: Data timeframe (1d, 1h, 5m, etc.)
            vs_currency: Base currency (default: usd)
            
        Returns:
            dict: Operation results
        """
        logger.info(f"Starting price data population for asset {asset.id}, timeframe: {timeframe}")
        
        try:
            if not asset:
                raise ValueError(f"Asset {asset.id} not found")
            
            if not asset.is_active or not asset.is_supported:
                raise ValueError(f"Asset {asset.id} is not active or supported")

            # Auto-calculate days if not provided
            if days is None:
                print("**populate_price_data--> _calculate_optimal_days")
                days = await self._calculate_optimal_days(asset, timeframe)
                logger.info(f"Auto-calculated days for asset {asset.id}, timeframe {timeframe}: {days} days")

            api_id = asset.get_external_api_id(platform)
            if not api_id:
                raise ValueError(f"No {platform} ID found for asset {asset.id}")

            print(f"**populate_price_data--> _fetch_price_history {asset.id}")
            price_history = await self._fetch_price_history(
                asset=asset, api_id=api_id, days=days, timeframe=timeframe, vs_currency=vs_currency, platform=platform
                )
            print(f"**populate_price_data--> Fetched price history: {len(price_history)} records")

            # Bulk insert data - NOW includes automatic aggregation with complete statistics
            bulk_result = self.price_data_repo.bulk_insert(asset, price_history, timeframe)
            if bulk_result.get('success', False):
                # Extract aggregation statistics from bulk_insert (NEW - no longer duplicate aggregation)
                auto_aggregation_stats = bulk_result.get('aggregation_results', {})
                total_auto_aggregated = bulk_result.get('total_aggregated_records', 0)
                
                # Legacy manual aggregation (only if auto-aggregation was disabled or failed)
                manual_aggregation_result = {}
                if not auto_aggregation_stats and (bulk_result.get('inserted_records', 0) > 0 or bulk_result.get('updated_records', 0) > 0):
                    try:
                        print("**populate_price_data--> manual auto_aggregate_for_asset start (fallback)")
                        manual_aggregation_result = self.auto_aggregate_for_asset(
                            asset=asset,
                            source_timeframe=timeframe
                        ).get('results', {})
                        print("**populate_price_data--> manual auto_aggregate_for_asset end (fallback)")
                        logger.info(f"Manual aggregation completed for asset {asset.id}: {manual_aggregation_result}")
                    except Exception as e:
                        logger.warning(f"Manual aggregation failed for asset {asset.id} after bulk insert: {e}")

                # Update asset metadata including market data
                print("**populate_price_data--> _update_asset_metadata")
                await self._update_asset_metadata(asset.id, timeframe, platform=platform)

                logger.info(f"Successfully populated {bulk_result.get('inserted_records', 0)} records for asset {asset.id}")
                
                # Calculate total operations including accurate aggregation counts
                total_direct_inserted = bulk_result.get('inserted_records', 0)
                total_direct_updated = bulk_result.get('updated_records', 0)
                
                # ✨ NEW: Extract accurate aggregation statistics
                total_aggregated_inserted = bulk_result.get('total_aggregated_inserted', 0)
                total_aggregated_updated = bulk_result.get('total_aggregated_updated', 0)
                
                # Legacy fallback for manual aggregation
                if total_aggregated_inserted == 0 and manual_aggregation_result:
                    total_aggregated_inserted = sum(manual_aggregation_result.values())
                
                result = {
                    'success': True,
                    # ✨ FIXED: Now accurately separates insert and update operations
                    'records_inserted': total_direct_inserted + total_aggregated_inserted,  # Direct + Aggregated inserts
                    'records_updated': total_direct_updated + total_aggregated_updated,    # Direct + Aggregated updates
                    'records_skipped': bulk_result.get('skipped_records', 0),
                    'total_processed': bulk_result.get('total_processed', 0),
                    
                    # ✨ Detailed breakdown for transparency with accurate aggregation
                    'operation_breakdown': {
                        'direct_inserted': total_direct_inserted,
                        'direct_updated': total_direct_updated,
                        'direct_skipped': bulk_result.get('skipped_records', 0),
                        'aggregated_inserted': total_aggregated_inserted,
                        'aggregated_updated': total_aggregated_updated,  # Now accurately reflects aggregation updates
                        'total_database_operations': total_direct_inserted + total_direct_updated + total_aggregated_inserted + total_aggregated_updated
                    },
                    
                    # ✨ NEW: Complete aggregation statistics from bulk_insert with accurate counts
                    'auto_aggregation_stats': auto_aggregation_stats,
                    'total_auto_aggregated_records': total_aggregated_inserted + total_aggregated_updated,
                    'aggregation_breakdown': {
                        'auto_aggregated_timeframes': self._format_aggregation_timeframes(auto_aggregation_stats),
                        'manual_aggregated_timeframes': list(manual_aggregation_result.keys()) if manual_aggregation_result else [],
                        'total_aggregated_inserted': total_aggregated_inserted,
                        'total_aggregated_updated': total_aggregated_updated,
                        'total_aggregated_records': total_aggregated_inserted + total_aggregated_updated
                    },
                    
                    # Legacy fields for backward compatibility
                    'aggregation_result': manual_aggregation_result,  # Legacy manual aggregation
                    
                    'asset_id': asset.id,
                    'timeframe': timeframe,
                    'period_days': days,
                    'data_range': bulk_result.get('data_range', {}),
                    'message': f'Successfully processed {total_direct_inserted + total_aggregated_inserted + total_direct_updated + total_aggregated_updated} total records: {total_direct_inserted} direct inserts, {total_direct_updated} direct updates, {bulk_result.get("skipped_records", 0)} skipped. Auto-aggregated: {total_aggregated_inserted} inserts + {total_aggregated_updated} updates across {len(auto_aggregation_stats)} timeframes.'
                }
                return serialize_datetime_objects(result)
            else:
                result = {
                    'success': False,
                    'message': f'Failed to insert data into database: {bulk_result.get("error", "Unknown error")}',
                    'records_inserted': 0,
                    'error': bulk_result.get('error', 'Bulk insert failed')
                }
                return serialize_datetime_objects(result)
                
        except Exception as e:
            logger.error(f"Error populating price data for asset {asset.id}: {str(e)}")
            result = {
                'success': False,
                'error': str(e),
                'records_inserted': 0,
                'message': f'Failed to populate price data: {str(e)}'
            }
            return serialize_datetime_objects(result)
    
    async def fetch_and_update_latest_prices(
        self,
        asset_ids: Optional[List[int]] = None,
        timeframe: str = "1d"
    ) -> Dict[str, Any]:
        """
        Fetch and update latest price data for multiple assets
        
        Args:
            asset_ids: List of asset IDs (None for all active assets)
            timeframe: Data timeframe
            
        Returns:
            dict: Batch operation results
        """
        logger.info(f"Starting batch price update, timeframe: {timeframe}")
        
        # Get assets to update - BULK QUERY to avoid N+1 problem
        if asset_ids:
            # Use bulk query instead of individual gets
            assets = self.asset_repo.get_by_ids(asset_ids)  # Single bulk query
        else:
            assets = self.asset_repo.get_active_assets()
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for asset in assets:
            try:
                result = await self.populate_price_data(
                    asset=asset, days=1, timeframe=timeframe
                )
                
                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Asset {asset.id}: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                failed_count += 1
                errors.append(f"Asset {asset.id}: {str(e)}")
        
        result = {
            'success_count': success_count,
            'failed_count': failed_count,
            'total_assets': len(assets),
            'errors': errors,
            'timeframe': timeframe
        }
        return serialize_datetime_objects(result)
    
    def get_price_data_gaps(
        self,
        asset_id: int,
        timeframe: str = "1d",
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Identify gaps in price data for an asset
        
        Args:
            asset_id: Asset ID
            timeframe: Data timeframe
            days_back: Days to check back
            
        Returns:
            list: List of data gaps
        """
        # Convert timeframe to minutes for gap detection
        timeframe_minutes = timeframe_to_minutes(timeframe)
        
        result = self.price_data_repo.get_missing_data_gaps(
            asset_id, timeframe_minutes
        )
        return serialize_datetime_objects(result)
    
    def get_data_quality_report(
        self,
        asset_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Generate data quality report for an asset
        
        Args:
            asset_id: Asset ID
            days: Days to analyze
            
        Returns:
            dict: Data quality report
        """
        result = self.price_data_repo.get_data_quality_report(asset_id, days)
        return serialize_datetime_objects(result)
    
    # Private helper methods
    
    async def _calculate_optimal_days(self, asset: Asset, timeframe: str) -> int:
        """
        Calculate optimal number of days to fetch based on existing data
        
        Args:
            asset: Asset object
            timeframe: Target timeframe
            
        Returns:
            Number of days to fetch from API
        """
        try:
            # Refresh timeframe data from database to get latest information
            # asset.refresh_timeframe_data_from_db(self.db)
            
            # Get timeframe info from cache
            timeframe_info = asset.get_timeframe_data(timeframe)
            
            # Define maximum days available for each timeframe in CoinGecko
            max_days_by_timeframe = {
                '1m': 1,        # 1 minute: limited data
                '5m': 1,        # 5 minutes: limited data  
                '15m': 1,       # 15 minutes: limited data
                '1h': 90,       # 1 hour: ~90 days
                '4h': 90,       # 4 hours: ~90 days
                '1d': 365,      # Daily: up to 1 year
                '1w': 365 * 2,  # Weekly: up to 2 years
                '1M': 365 * 2   # Monthly: up to 2 years
            }
            
            max_days = max_days_by_timeframe.get(timeframe, 365)
            
            if not timeframe_info or not timeframe_info.get('latest_time'):
                # No existing data - fetch maximum available
                logger.info(f"No existing data for asset {asset.id}, timeframe {timeframe}. Fetching {max_days} days")
                return max_days
            
            # Get latest candle time from database
            latest_time = asset.get_latest_candle_time(timeframe) if asset else None
            
            # Check if latest_time is valid
            if not latest_time:
                logger.info(f"No valid latest_time found for asset {asset.id}, timeframe {timeframe}. Fetching {max_days} days")
                return max_days
            
            # Calculate days since latest data using normalized datetime comparison
            # Normalize latest_time to remove timezone info for consistent calculation
            normalized_latest_time = normalize_datetime(latest_time)
            if not normalized_latest_time:
                logger.info(f"Failed to normalize latest_time for asset {asset.id}, timeframe {timeframe}. Fetching {max_days} days")
                return max_days

            # Use current time as naive datetime for consistent comparison
            now = normalize_datetime(datetime.now())
            
            days_since_latest = (now - normalized_latest_time).days
            
            # Add buffer for latest candle update (always fetch last candle + some buffer)
            buffer_days = 2  # Always fetch last 2 days to ensure latest candle is updated
            
            # Total days to fetch = days since latest + buffer, but not more than max
            days_to_fetch = min(days_since_latest + buffer_days, max_days)
            
            # Minimum 1 day to always get some data
            days_to_fetch = max(1, days_to_fetch)
            
            print(
                f"Asset {asset.id}, timeframe {timeframe}: "
                f"Latest data: {normalized_latest_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"Days since: {days_since_latest}, "
                f"Will fetch: {days_to_fetch} days"
            )
            logger.info(
                f"Asset {asset.id}, timeframe {timeframe}: "
                f"Latest data: {normalized_latest_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"Days since: {days_since_latest}, "
                f"Will fetch: {days_to_fetch} days"
            )

            return days_to_fetch
            
        except Exception as e:
            logger.error(f"Error calculating optimal days for asset {asset.id}: {e}")
            # Fallback to reasonable default
            default_days = 30 if timeframe in ['1d', '1h', '4h'] else 7
            logger.info(f"Using fallback: {default_days} days")
            return default_days

    
    async def _fetch_price_history(
        self,
        asset: Asset,
        api_id: str,
        days: int,
        timeframe: str,
        vs_currency: str,
        platform: str
    ) -> List[Dict[str, Any]]:
        if timeframe not in ["1h", "1d"]:
            logger.warning(f"Timeframe {timeframe} not supported")
            return []

        # Map supported platforms to their client instances. This allows a
        # single unified code path and avoids duplicated try/except blocks.
        client = self.client_map.get(platform)
        if not client:
            logger.error(f"Unsupported external API: {platform}")
            return []

        # Debug/logging for the fetch
        logger.debug(f"Fetching price history from {platform} for {api_id}, days: {days}, timeframe: {timeframe}")

        try:
            # All clients implement get_price_data_by_timeframe(asset_id, crypto_id, timeframe, days, vs_currency)
            ohlcv_data = await client.get_price_data_by_timeframe(
                asset_id=asset.id,
                crypto_id=api_id,
                timeframe=timeframe,
                days=days,
                vs_currency=vs_currency,
            )
            return ohlcv_data
        except Exception as e:
            # Provide platform-specific logging but keep behavior consistent
            logger.error(f"Error fetching data from {platform} for asset {asset.id}: {e}")
            return []
    
    async def _update_asset_metadata(
        self,
        asset_id: int,
        timeframe: str,
        platform: str = "binance"
    ) -> None:
        """
        Update asset metadata with optimized API-first approach
        
        Strategy:
        1. Try to get comprehensive data from CoinGecko API first
        2. Fall back to database queries only for missing critical data
        3. Minimize database round-trips by using bulk operations
        """
        try:
            asset = self.asset_repo.get(asset_id)
            if not asset:
                logger.warning(f"Asset {asset_id} not found for metadata update")
                return

            coingecko_id = asset.get_external_id("coingecko")
            updated_fields = []
            
            # Primary strategy: Get comprehensive data from CoinGecko API
            api_data_available = False
            if coingecko_id:
                try:
                    detailed_data = await self.coingecko_client.get_detailed_market_data(coingecko_id)
                    logger.info(f"Fetching comprehensive market data from API for CoinGecko ID: {coingecko_id}")
                    
                    if detailed_data:
                        api_data_available = True
                        
                        # Update current price from API (replaces database query)
                        if 'current_price' in detailed_data:
                            asset.current_price = detailed_data['current_price']
                            updated_fields.append(f"current_price_api: ${detailed_data['current_price']:.8f}")
                        
                        # Update market cap from API (replaces database query)
                        if 'market_cap' in detailed_data:
                            asset.market_cap = detailed_data['market_cap']
                            updated_fields.append(f"market_cap_api: ${detailed_data['market_cap']:,.2f}")
                        
                        # Update volume from API (replaces database query)
                        if 'total_volume' in detailed_data:
                            asset.total_volume = detailed_data['total_volume']
                            updated_fields.append(f"total_volume_api: ${detailed_data['total_volume']:,.2f}")
                        
                        # Update market cap rank
                        if 'market_cap_rank' in detailed_data:
                            asset.market_cap_rank = detailed_data['market_cap_rank']
                            updated_fields.append(f"market_cap_rank: {detailed_data['market_cap_rank']}")
                        
                        # Update supply data
                        if 'circulating_supply' in detailed_data:
                            asset.circulating_supply = detailed_data['circulating_supply']
                            updated_fields.append(f"circulating_supply: {detailed_data['circulating_supply']:,.0f}")
                        
                        if 'total_supply' in detailed_data:
                            asset.total_supply = detailed_data['total_supply']
                            updated_fields.append(f"total_supply: {detailed_data['total_supply']:,.0f}")
                        
                        if 'max_supply' in detailed_data:
                            asset.max_supply = detailed_data['max_supply']
                            updated_fields.append(f"max_supply: {detailed_data['max_supply']:,.0f}")
                        
                        # Update price changes from API (replaces database candle aggregations)
                        if 'price_change_percentage_24h' in detailed_data:
                            asset.price_change_percentage_24h = detailed_data['price_change_percentage_24h']
                            updated_fields.append(f"price_change_24h_api: {detailed_data['price_change_percentage_24h']:.2f}%")
                        
                        if 'price_change_percentage_7d_in_currency' in detailed_data:
                            asset.price_change_percentage_7d = detailed_data['price_change_percentage_7d_in_currency']
                            updated_fields.append(f"price_change_7d_api: {detailed_data['price_change_percentage_7d_in_currency']:.2f}%")
                        
                        if 'price_change_percentage_30d_in_currency' in detailed_data:
                            asset.price_change_percentage_30d = detailed_data['price_change_percentage_30d_in_currency']
                            updated_fields.append(f"price_change_30d_api: {detailed_data['price_change_percentage_30d_in_currency']:.2f}%")
                        
                        # Update ATH/ATL from API (replaces database tracking)
                        if 'ath' in detailed_data and detailed_data['ath']:
                            api_ath = float(detailed_data['ath'])
                            if not asset.ath or api_ath > float(asset.ath):
                                asset.ath = api_ath
                                if 'ath_date' in detailed_data:
                                    asset.ath_date = datetime.fromisoformat(detailed_data['ath_date'].replace('Z', '+00:00'))
                                updated_fields.append(f"ath_api: ${api_ath:.8f}")
                        
                        if 'atl' in detailed_data and detailed_data['atl']:
                            api_atl = float(detailed_data['atl'])
                            if not asset.atl or api_atl < float(asset.atl):
                                asset.atl = api_atl
                                if 'atl_date' in detailed_data:
                                    asset.atl_date = datetime.fromisoformat(detailed_data['atl_date'].replace('Z', '+00:00'))
                                updated_fields.append(f"atl_api: ${api_atl:.8f}")
                        
                        logger.info(f"Successfully updated asset {asset_id} with comprehensive API data")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch detailed market data from API for {coingecko_id}: {e}")
                    api_data_available = False

            # Update basic metadata (always needed regardless of data source)
            updates = {
                'data_source': platform,
                'last_price_update': datetime.utcnow(),
                'last_accessed_at': datetime.utcnow(),
                'access_count': (asset.access_count or 0) + 1,
                'timeframe_usage': asset.timeframe_usage
            }
            
            # Calculate data quality score only when needed (lightweight operation)
            print("****_update_asset_metadata--> _calculate_data_quality_score")
            quality_score = self._calculate_data_quality_score(asset_id, timeframe)
            if quality_score is not None:
                updates['data_quality_score'] = quality_score

            # Save all updates
            print("****_update_asset_metadata--> update_no_obj_return")
            self.asset_repo.update_no_obj_return(db_obj=asset, obj_in=updates)
            
            # Log results
            data_source = "API" if api_data_available else "Database"
            if updated_fields:
                logger.info(f"Updated asset {asset_id} metadata from {data_source}: {', '.join(updated_fields)}")
            else:
                logger.debug(f"Updated asset {asset_id} basic metadata from {data_source}")
            
        except Exception as e:
            logger.error(f"Error updating asset metadata for asset {asset_id}: {str(e)}")
            # BaseRepository.update handles its own transaction management
    
    def _calculate_data_quality_score(
        self,
        asset_id: int,
        timeframe: str
    ) -> Optional[int]:
        """
        Calculate data quality score based on completeness and accuracy
        """
        try:
            print("******_calculate_data_quality_score--> get_data_quality_report")
            quality_report = self.get_data_quality_report(asset_id, days=7)
            return quality_report.get('quality_score')
        except Exception as e:
            logger.error(f"Error calculating quality score: {str(e)}")
            return None

    def _format_aggregation_timeframes(self, auto_aggregation_stats: Dict[str, int]) -> Dict[str, Dict[str, int]]:
        """
        Format aggregation statistics to show insert/update breakdown for each timeframe.
        
        Args:
            auto_aggregation_stats: Raw aggregation stats from bulk_insert
                Example: {'4h_inserted': 2, '4h_updated': 1, '1d_inserted': 0, '1d_updated': 1, '1w_updated': 1}
        
        Returns:
            Dictionary with timeframe breakdown showing inserts and updates separately:
                Example: {
                    '4h': {'inserted': 2, 'updated': 1, 'total': 3},
                    '1d': {'inserted': 0, 'updated': 1, 'total': 1}, 
                    '1w': {'inserted': 0, 'updated': 1, 'total': 1}
                }
        """
        if not auto_aggregation_stats:
            return {}
        
        timeframe_breakdown = {}
        
        # Process each aggregation stat entry
        for key, count in auto_aggregation_stats.items():
            # Extract timeframe and operation type
            if key.endswith('_inserted'):
                timeframe = key.replace('_inserted', '')
                operation = 'inserted'
            elif key.endswith('_updated'):
                timeframe = key.replace('_updated', '')
                operation = 'updated'
            else:
                # Legacy format - treat as mixed operations
                timeframe = key
                # For legacy entries, we can't distinguish insert vs update
                if timeframe not in timeframe_breakdown:
                    timeframe_breakdown[timeframe] = {'inserted': 0, 'updated': 0, 'total': 0}
                timeframe_breakdown[timeframe]['total'] = count
                continue
            
            # Initialize timeframe entry if not exists
            if timeframe not in timeframe_breakdown:
                timeframe_breakdown[timeframe] = {'inserted': 0, 'updated': 0, 'total': 0}
            
            # Set the specific operation count
            timeframe_breakdown[timeframe][operation] = count
        
        # Calculate totals for each timeframe
        for timeframe_data in timeframe_breakdown.values():
            if timeframe_data['total'] == 0:  # Only calculate if not set by legacy format
                timeframe_data['total'] = timeframe_data['inserted'] + timeframe_data['updated']
        
        return timeframe_breakdown
    
    
    def auto_aggregate_for_asset(self, asset: Asset, 
                               source_timeframe: str = '1h',
                               force_refresh: bool = False) -> Dict[str, Any]:
        """
        Automatically aggregate price data for an asset
        
        Args:
            asset: Asset to process
            source_timeframe: Base timeframe to aggregate from
            force_refresh: Whether to re-aggregate existing data
            
        Returns:
            Aggregation results and status
        """
        try:
            # Get asset info
            if not asset:
                return serialize_datetime_objects({'error': f'Asset {asset.id} not found'})
            
            # Check what timeframes we can aggregate to
            target_timeframes = self.price_data_repo.get_aggregatable_timeframes(source_timeframe)
            
            if not target_timeframes:
                result = {
                    'asset_id': asset.id,
                    'symbol': asset.symbol,
                    'message': f'No aggregatable timeframes for {source_timeframe}',
                    'aggregated_timeframes': []
                }
                return serialize_datetime_objects(result)
            
            # Get current status
            print("****auto_aggregate_for_asset-->get_aggregation_status start")
            status_before = self.price_data_repo.get_aggregation_status(asset)
            print("****auto_aggregate_for_asset-->get_aggregation_status complete")

            # Determine time range for aggregation
            source_data_count_raw = status_before.get(source_timeframe, {}).get('count', 0)
            try:
                source_data_count = int(source_data_count_raw) if source_data_count_raw is not None else 0
            except (ValueError, TypeError):
                source_data_count = 0
            if source_data_count == 0:
                result = {
                    'asset_id': asset.id,
                    'symbol': asset.symbol,
                    'error': f'No {source_timeframe} data available for aggregation'
                }
                return serialize_datetime_objects(result)
            
            # Calculate optimal aggregation window for all target timeframes in single query
            aggregation_results = {}
            
            if not force_refresh:
                try:
                    # Calculate optimal window for all target timeframes at once
                    print("****auto_aggregate_for_asset-->_calculate_timeframe_specific_window start")
                    aggregation_window = self._calculate_timeframe_specific_window(
                        asset=asset,
                        source_timeframe=source_timeframe,
                        target_timeframes=target_timeframes
                    )
                    print("****auto_aggregate_for_asset-->_calculate_timeframe_specific_window complete")
                    # Check if window calculation succeeded
                    if aggregation_window.get('start_time') and aggregation_window.get('end_time'):
                        # Perform aggregation for all timeframes using the optimal window
                        print("****auto_aggregate_for_asset-->bulk_aggregate_and_store start")
                        result = self.price_data_repo.bulk_aggregate_and_store(
                            asset=asset,
                            source_timeframe=source_timeframe,
                            target_timeframes=target_timeframes,
                            start_time=aggregation_window['start_time'],
                            end_time=aggregation_window['end_time']
                        )
                        print("****auto_aggregate_for_asset-->bulk_aggregate_and_store complete")
                        
                        # Process results for each timeframe
                        for target_timeframe in target_timeframes:
                            aggregation_results[target_timeframe] = {
                                'records': result.get(target_timeframe, 0),
                                'window': aggregation_window,
                                'status': 'success'
                            }
                    else:
                        # Window calculation failed - mark all timeframes as failed
                        for target_timeframe in target_timeframes:
                            aggregation_results[target_timeframe] = {
                                'records': 0,
                                'error': aggregation_window.get('error', 'Window calculation failed'),
                                'window': aggregation_window,
                                'status': 'error'
                            }
                        
                except Exception as e:
                    # Global error - mark all timeframes as failed
                    for target_timeframe in target_timeframes:
                        aggregation_results[target_timeframe] = {
                            'records': 0,
                            'error': str(e),
                            'status': 'error'
                        }
            else:
                # Force refresh - process all timeframes together
                result = self.price_data_repo.bulk_aggregate_and_store(
                    asset_id=asset.id,
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
            
            # Get status after aggregation and timeframe updates
            status_after = self.price_data_repo.get_aggregation_status(asset)
            
            result = {
                'asset_id': asset.id,
                'symbol': asset.symbol,
                'source_timeframe': source_timeframe,
                'aggregated_timeframes': target_timeframes,
                'results': aggregation_results,
                'status_before': status_before,
                'status_after': status_after,
                'window_optimization': 'individual_timeframe_windows' if not force_refresh else 'force_refresh_all_data'
            }
            return serialize_datetime_objects(result)
            
        except Exception as e:
            result = {
                'asset_id': asset.id,
                'error': f'Aggregation failed: {str(e)}'
            }
            return serialize_datetime_objects(result)


    def _calculate_timeframe_specific_window(self, asset: Asset, source_timeframe: str, 
                                           target_timeframes: List[str]) -> Dict[str, Any]:
        """
        Calculate optimal aggregation window for multiple target timeframes in a single query
        
        Returns the largest window needed to satisfy all target timeframes optimally.
        This avoids multiple database queries and ensures all timeframes are processed efficiently.
        
        Different timeframes need different aggregation windows:
        - Monthly (1M): At least 30+ days to ensure complete months
        - Weekly (1w): At least 7+ days to ensure complete weeks  
        - Daily (1d): At least 1+ days
        - 4-hour (4h): At least 8+ hours to ensure multiple periods
        - Hourly (1h): At least 1+ hours
        
        Args:
            asset_id: Asset ID to analyze
            source_timeframe: Source timeframe for aggregation
            target_timeframes: List of target timeframes to optimize for
            
        Returns:
            Optimal window configuration that satisfies all target timeframes
        """
        try:
            # Single query to get aggregation status for all relevant timeframes
            if not asset:
                result = {
                    'start_time': None,
                    'end_time': None,
                    'method': 'asset_not_found',
                    'target_timeframes': target_timeframes
                }
                return serialize_datetime_objects(result)
            
            # Use the optimized get_aggregation_status that queries database directly
            status = self.price_data_repo.get_aggregation_status(asset)
            source_info = status.get(source_timeframe, {})
            # Get source latest time
            source_latest = source_info.get('latest_time')
            if not source_latest:
                result = {
                    'start_time': None,
                    'end_time': None,
                    'method': 'no_source_data',
                    'target_timeframes': target_timeframes
                }
                return serialize_datetime_objects(result)
            
            source_latest_dt = datetime.fromisoformat(source_latest.replace('Z', '+00:00'))
            
            # Define timeframe requirements and calculate the maximum window needed
            timeframe_requirements = {
                '1M': {'min_days': 35, 'buffer_days': 7, 'extension_threshold': 7},
                '1w': {'min_days': 12, 'buffer_days': 2, 'extension_threshold': 3}, 
                '1d': {'min_days': 3, 'buffer_days': 1, 'extension_threshold': 1},
                '4h': {'min_days': 2, 'buffer_days': 1, 'extension_threshold': 0},
                '1h': {'min_days': 1, 'buffer_days': 1, 'extension_threshold': 0}
            }
            
            max_min_days = 0
            earliest_start_time = source_latest_dt
            timeframe_analysis = {}
            processed_timeframes = []
            
            # Process each target timeframe to find the maximum window requirement
            for target_timeframe in target_timeframes:
                target_info = status.get(target_timeframe, {})
                #print(f"target_info: {target_info}")

                target_latest = target_info.get('latest_time')

                # Get timeframe requirements
                req = timeframe_requirements.get(target_timeframe, {'min_days': 7, 'buffer_days': 1, 'extension_threshold': 1})
                min_days = req['min_days']
                buffer_days = req['buffer_days']
                extension_threshold = req['extension_threshold']
                
                print(f"target_latest: {target_latest}")
                
                if target_latest:
                    # Parse target latest datetime
                    target_latest_dt = datetime.fromisoformat(target_latest.replace('Z', '+00:00'))

                    # Calculate days since last aggregation for this timeframe
                    days_since_last = (source_latest_dt - target_latest_dt).days
                    
                    # Extend window if last aggregation was too long ago
                    if days_since_last > extension_threshold:
                        min_days = max(min_days, days_since_last + buffer_days)
                    
                    # Calculate start time for this timeframe considering existing data
                    timeframe_start_time = target_latest_dt - timedelta(days=buffer_days)
                else:
                    # No existing data for this timeframe - use maximum possible window
                    # Get earliest time from source timeframe to maximize data coverage
                    source_earliest = source_info.get('earliest_time')
                    
                    if source_earliest:
                        # Parse source earliest time and normalize it to target timeframe
                        source_earliest_dt = datetime.fromisoformat(source_earliest.replace('Z', '+00:00'))
                        
                        # Normalize earliest source time to target timeframe boundary
                        normalized_target_start = self._normalize_datetime_to_timeframe(
                            source_earliest_dt, target_timeframe
                        )
                        
                        # Use normalized time as if it's the "latest" target data for calculation
                        target_latest_dt = normalized_target_start
                        days_since_last = (source_latest_dt - normalized_target_start).days
                        
                        # Calculate start time to include ALL available data
                        timeframe_start_time = normalized_target_start - timedelta(days=buffer_days)
                        
                        print(f"Target timeframe {target_timeframe} has no data. Using normalized source earliest time:")
                        print(f"  Source earliest: {source_earliest_dt}")
                        print(f"  Normalized to {target_timeframe}: {normalized_target_start}")
                        print(f"  Calculated window start: {timeframe_start_time}")
                        
                    else:
                        # Fallback: use minimum window if no source earliest data
                        target_latest_dt = None
                        days_since_last = 'first_time_no_source_earliest'
                        timeframe_start_time = source_latest_dt - timedelta(days=min_days)
                
                # Track the earliest start time needed (biggest window)
                if timeframe_start_time < earliest_start_time:
                    earliest_start_time = timeframe_start_time
                
                # Keep track of the largest minimum days requirement
                max_min_days = max(max_min_days, min_days)
                
                # Determine window type based on data availability and calculation method
                if target_latest:
                    window_type = 'extended' if days_since_last != 'first_time' and days_since_last > extension_threshold else 'standard'
                    data_status = 'existing_data_found'
                elif source_info.get('earliest_time'):
                    window_type = 'maximum_coverage'
                    data_status = 'no_target_data_using_normalized_source_earliest'
                else:
                    window_type = 'minimum_fallback'
                    data_status = 'no_data_using_minimum_window'
                
                # Store analysis for this timeframe
                timeframe_analysis[target_timeframe] = {
                    'min_days': min_days,
                    'days_since_last_aggregation': days_since_last,
                    'target_latest': target_latest,
                    'source_earliest': source_info.get('earliest_time'),
                    'calculated_start_time': timeframe_start_time,
                    'window_extension': window_type,
                    'data_status': data_status,
                    'normalized_start': target_latest_dt.isoformat() if target_latest_dt else None
                }
                processed_timeframes.append(target_timeframe)

            # Final window calculation - use the earliest start time to satisfy all timeframes
            end_time = source_latest_dt
            start_time = earliest_start_time
            
            # Ensure minimum window size
            min_window_start = source_latest_dt - timedelta(days=max_min_days)
            if start_time > min_window_start:
                start_time = min_window_start
            
            # Calculate final statistics
            window_days = (end_time - start_time).days
            
            # Determine optimization method
            has_extensions = any(analysis['window_extension'] == 'extended' for analysis in timeframe_analysis.values())
            optimization_method = 'multi_timeframe_optimization_with_extensions' if has_extensions else 'multi_timeframe_optimization_standard'
            
            result = {
                'start_time': start_time,
                'end_time': end_time,
                'method': optimization_method,
                'target_timeframes': processed_timeframes,
                'window_days': window_days,
                'max_min_days_required': max_min_days,
                'rationale': f'Optimized window for {len(processed_timeframes)} timeframes: {", ".join(processed_timeframes)}',
                'source_latest': source_latest,
                'timeframe_analysis': timeframe_analysis,
                'optimization_summary': {
                    'total_timeframes_processed': len(processed_timeframes),
                    'largest_window_timeframe': max(timeframe_analysis.keys(), key=lambda tf: timeframe_analysis[tf]['min_days']),
                    'has_gap_extensions': has_extensions,
                    'single_query_optimization': True
                }
            }
            return serialize_datetime_objects(result)
            
        except Exception as e:
            result = {
                'start_time': None,
                'end_time': None,
                'method': 'error',
                'target_timeframes': target_timeframes,
                'error': str(e)
            }
            return serialize_datetime_objects(result)
    
    def _normalize_datetime_to_timeframe(self, dt: datetime, timeframe: str) -> datetime:
        """
        Normalize datetime to the appropriate timeframe boundary
        
        This ensures that the datetime aligns with the natural boundaries of the target timeframe:
        - 1h: Round down to start of hour
        - 4h: Round down to nearest 4-hour boundary (00:00, 04:00, 08:00, etc.)
        - 1d: Round down to start of day (00:00:00)
        - 1w: Round down to start of week (Monday 00:00:00)
        - 1M: Round down to start of month (1st day 00:00:00)
        
        Args:
            dt: Datetime to normalize
            timeframe: Target timeframe
            
        Returns:
            Normalized datetime aligned to timeframe boundary
        """
        if timeframe == '1h':
            # Round down to start of hour
            return dt.replace(minute=0, second=0, microsecond=0)
            
        elif timeframe == '4h':
            # Round down to nearest 4-hour boundary
            normalized_hour = (dt.hour // 4) * 4
            return dt.replace(hour=normalized_hour, minute=0, second=0, microsecond=0)
            
        elif timeframe == '1d':
            # Round down to start of day
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
            
        elif timeframe == '1w':
            # Round down to start of week (Monday)
            days_since_monday = dt.weekday()
            start_of_week = dt - timedelta(days=days_since_monday)
            return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            
        elif timeframe == '1M':
            # Round down to start of month
            return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
        else:
            # Default: round down to start of day
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)


# Global service instance factory
def get_price_data_service(db: Session) -> PriceDataService:
    """Factory function to create PriceDataService instance"""
    return PriceDataService(db)
