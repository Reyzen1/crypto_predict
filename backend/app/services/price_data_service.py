# backend/app/services/price_data_service.py
# Service for price data management with timeframe support

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from sqlalchemy.orm import Session

from app.external.coingecko import CoinGeckoClient
from app.repositories.asset.price_data_repository import PriceDataRepository
from app.repositories.asset.asset_repository import AssetRepository
from app.models.asset.asset import Asset
from app.models.asset.price_data import PriceData

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
        self.price_data_repo = PriceDataRepository(db)
        self.asset_repo = AssetRepository(db)
    
    async def populate_price_data(
        self,
        asset_id: int,
        days: int = 30,
        timeframe: str = "1d",
        vs_currency: str = "usd"
    ) -> Dict[str, Any]:
        """
        Complete price data population for an asset with timeframe support
        
        Args:
            asset_id: Asset ID to populate data for
            days: Number of days of historical data
            timeframe: Data timeframe (1d, 1h, 5m, etc.)
            vs_currency: Base currency (default: usd)
            
        Returns:
            dict: Operation results
        """
        logger.info(f"Starting price data population for asset {asset_id}, timeframe: {timeframe}")
        
        try:
            # Get asset from database
            asset = self.asset_repo.get(asset_id)
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")
            
            if not asset.is_active or not asset.is_supported:
                raise ValueError(f"Asset {asset_id} is not active or supported")
            
            # Get CoinGecko coin_id
            coingecko_id = self._get_coingecko_id(asset)
            if not coingecko_id:
                raise ValueError(f"No CoinGecko ID found for asset {asset_id}")
            
            # Fetch data from CoinGecko based on timeframe
            price_history = await self._fetch_price_history(
                coingecko_id, days, timeframe, vs_currency
            )
            if not price_history:
                return {
                    'success': False,
                    'message': 'No data received from CoinGecko',
                    'records_inserted': 0
                }
            
            # Process and validate data
            processed_data = self._process_price_data(
                asset_id, price_history, timeframe
            )
            
            # Bulk insert data
            bulk_result = self.price_data_repo.bulk_insert(processed_data)
            
            if bulk_result.get('success', False):
                # Trigger aggregation for the asset after successful data insertion
                try:
                    aggregation_result = self.auto_aggregate_for_asset(
                        asset_id=asset_id, 
                        source_timeframe=timeframe
                    )
                    logger.info(f"Aggregation completed for asset {asset_id}: {aggregation_result}")
                except Exception as e:
                    logger.warning(f"Aggregation failed for asset {asset_id} after bulk insert: {e}")
                
                # Update asset metadata including market data
                await self._update_asset_metadata(asset_id, timeframe, bulk_result.get('inserted_records', 0), coingecko_id)

                logger.info(f"Successfully populated {bulk_result.get('inserted_records', 0)} records for asset {asset_id}")
                
                return {
                    'success': True,
                    'records_inserted': bulk_result.get('inserted_records', 0),
                    'records_updated': bulk_result.get('updated_records', 0),
                    'records_skipped': bulk_result.get('skipped_records', 0),
                    'total_processed': bulk_result.get('total_processed', 0),
                    'asset_id': asset_id,
                    'timeframe': timeframe,
                    'period_days': days,
                    'data_range': bulk_result.get('data_range', {}),
                    'message': f'Successfully populated {bulk_result.get("inserted_records", 0)} new records, updated {bulk_result.get("updated_records", 0)}, skipped {bulk_result.get("skipped_records", 0)}'
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to insert data into database: {bulk_result.get("error", "Unknown error")}',
                    'records_inserted': 0,
                    'error': bulk_result.get('error', 'Bulk insert failed')
                }
                
        except Exception as e:
            logger.error(f"Error populating price data for asset {asset_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'records_inserted': 0,
                'message': f'Failed to populate price data: {str(e)}'
            }
    
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
        
        # Get assets to update
        if asset_ids:
            assets = [self.asset_repo.get(asset_id) for asset_id in asset_ids]
            assets = [a for a in assets if a]  # Filter out None values
        else:
            assets = self.asset_repo.get_active_assets()
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for asset in assets:
            try:
                result = await self.populate_price_data(
                    asset.id, days=1, timeframe=timeframe
                )
                
                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Asset {asset.id}: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                failed_count += 1
                errors.append(f"Asset {asset.id}: {str(e)}")
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'total_assets': len(assets),
            'errors': errors,
            'timeframe': timeframe
        }
    
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
        timeframe_minutes = self._timeframe_to_minutes(timeframe)
        
        return self.price_data_repo.get_missing_data_gaps(
            asset_id, timeframe_minutes
        )
    
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
        return self.price_data_repo.get_data_quality_report(asset_id, days)
    
    # Private helper methods
    
    def _get_coingecko_id(self, asset: Asset) -> Optional[str]:
        """
        Get CoinGecko ID from asset external_ids
        
        Supports multiple storage formats:
        - JSON string: '{"coingecko_id": "bitcoin", "coinmarketcap_id": "1"}'
        - Dict: {"coingecko": "bitcoin"}
        - Key variations: coingecko, coingecko_id, coin_gecko_id
        
        Note: Recommended canonical format is JSON string with 'coingecko_id' key
        for consistency with external API naming conventions.
        
        Returns:
            CoinGecko ID string or None if not found
        """
        if not asset.external_ids:
            return None
        
        try:
            # Handle JSON string format
            if isinstance(asset.external_ids, str):
                external_ids_dict = json.loads(asset.external_ids)
            elif isinstance(asset.external_ids, dict):
                external_ids_dict = asset.external_ids
            else:
                logger.warning(f"Unsupported external_ids format for asset {asset.id}: {type(asset.external_ids)}")
                return None
            
            # Try multiple key variations (order by preference)
            key_variations = ['coingecko', 'coingecko_id', 'coin_gecko_id', 'coinGeckoId']
            
            for key in key_variations:
                if key in external_ids_dict and external_ids_dict[key]:
                    return str(external_ids_dict[key]).strip()
            
            return None
            
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            logger.error(f"Error parsing external_ids for asset {asset.id}: {e}")
            return None
    
    async def _fetch_price_history(
        self,
        coingecko_id: str,
        days: int,
        timeframe: str,
        vs_currency: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch price history from CoinGecko and convert to OHLCV format
        """
        try:
            # Get raw time-series data from CoinGecko
            if timeframe == "1d":
                # Daily data - use get_price_data_by_timeframe for better filtering
                raw_data = await self.coingecko_client.get_price_data_by_timeframe(
                    crypto_id=coingecko_id,
                    timeframe=timeframe,
                    limit=days,
                    vs_currency=vs_currency
                )
            elif timeframe in ["1h", "4h"]:
                # Calculate appropriate limit for timeframe
                limit = self._calculate_data_points_needed(days, timeframe)
                raw_data = await self.coingecko_client.get_price_data_by_timeframe(
                    crypto_id=coingecko_id,
                    timeframe=timeframe,
                    limit=limit,
                    vs_currency=vs_currency
                )
            else:
                logger.warning(f"Timeframe {timeframe} not supported for CoinGecko")
                return []
            
            # Convert time-series data to OHLCV format
            ohlcv_data = self._convert_time_series_to_ohlcv(raw_data, timeframe)
            
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Error fetching data from CoinGecko: {str(e)}")
            return []
    
    def _process_price_data(
        self,
        asset_id: int,
        price_history: List[Dict[str, Any]],
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """
        Process raw price data into database-ready format
        """
        processed_data = []
        
        for record in price_history:
            try:
                # Validate required fields
                if not all(key in record for key in ['timestamp', 'open', 'high', 'low', 'close']):
                    logger.warning(f"Skipping invalid record: {record}")
                    continue
                
                # Convert timestamp and normalize based on timeframe
                if isinstance(record['timestamp'], (int, float)):
                    candle_time = datetime.fromtimestamp(record['timestamp'] / 1000)
                else:
                    candle_time = record['timestamp']
                
                # Normalize candle time based on timeframe
                candle_time = self._normalize_candle_time(candle_time, timeframe)
                
                processed_record = {
                    'asset_id': asset_id,
                    'timeframe': timeframe,
                    'open_price': Decimal(str(record['open'])),
                    'high_price': Decimal(str(record['high'])),
                    'low_price': Decimal(str(record['low'])),
                    'close_price': Decimal(str(record['close'])),
                    'volume': Decimal(str(record.get('volume', 0))),
                    'market_cap': Decimal(str(record['market_cap'])) if record.get('market_cap') else None,
                    'trade_count': record.get('trade_count'),
                    'vwap': Decimal(str(record['vwap'])) if record.get('vwap') else None,
                    'candle_time': candle_time,
                    'is_validated': False  # Will be validated later
                }
                
                processed_data.append(processed_record)
                
            except Exception as e:
                logger.warning(f"Error processing record {record}: {str(e)}")
                continue
        
        return processed_data
    
    async def _update_asset_metadata(
        self,
        asset_id: int,
        timeframe: str,
        records_count: int,
        coingecko_id: str = None
    ) -> None:
        """
        Update asset metadata after successful data population and market data from database
        """
        try:
            asset = self.asset_repo.get(asset_id)
            if not asset:
                logger.warning(f"Asset {asset_id} not found for metadata update")
                return
            
            updated_fields = []
            
            # Update timeframe_usage
            if not asset.timeframe_usage:
                asset.timeframe_usage = {}
            
            current_count = asset.timeframe_usage.get(timeframe, 0)
            asset.timeframe_usage[timeframe] = current_count + records_count
            
            # Get current price from the latest price data in database
            latest_price_data = await self.price_data_repo.get_latest_price_data(asset_id)
            if latest_price_data:
                latest_price = float(latest_price_data.close_price)
                if latest_price > 0:
                    asset.update_price_data(price=latest_price)
                    updated_fields.append(f"current_price: ${latest_price:.8f}")
            
            # Get volume data from latest daily candle
            latest_daily_candle = await self.price_data_repo.get_latest_candle_data(asset_id, '1d')
            if latest_daily_candle and latest_daily_candle.get('volume'):
                latest_volume = float(latest_daily_candle['volume'])
                if latest_volume > 0:
                    asset.total_volume = latest_volume
                    updated_fields.append(f"total_volume: ${latest_volume:,.2f}")
            
            # Get market cap from latest candle data
            latest_market_cap = await self.price_data_repo.get_latest_market_cap(asset_id)
            if latest_market_cap:
                asset.market_cap = latest_market_cap
                updated_fields.append(f"market_cap_from_db: ${latest_market_cap:,.2f}")
            
            # For price changes, use latest aggregated candles instead of time-based calculations
            # This method is more accurate as it uses actual daily/weekly/monthly candle data
            price_changes = await self.calculate_price_change_from_candles(asset_id)
            
            # Update 24h change from daily candle
            if price_changes['24h'] is not None:
                asset.price_change_percentage_24h = price_changes['24h']
                updated_fields.append(f"price_change_24h_candle: {price_changes['24h']:.2f}%")
            
            # Update 7d change from weekly candle
            if price_changes['7d'] is not None:
                asset.price_change_percentage_7d = price_changes['7d']
                updated_fields.append(f"price_change_7d_candle: {price_changes['7d']:.2f}%")
            
            # Update 30d change from monthly candle or calculated from weekly candles
            if price_changes['30d'] is not None:
                asset.price_change_percentage_30d = price_changes['30d']
                updated_fields.append(f"price_change_30d_candle: {price_changes['30d']:.2f}%")
            
            # Update other metadata
            updates = {
                'last_price_update': datetime.utcnow(),
                'last_accessed_at': datetime.utcnow(),
                'access_count': (asset.access_count or 0) + 1,
                'timeframe_usage': asset.timeframe_usage
            }
            
            # Calculate and update data quality score
            quality_score = self._calculate_data_quality_score(asset_id, timeframe)
            if quality_score is not None:
                updates['data_quality_score'] = quality_score
            
            # If we have CoinGecko ID, fetch additional detailed market data
            if coingecko_id:
                try:
                    detailed_data = await self.coingecko_client.get_detailed_market_data(coingecko_id)
                    if detailed_data:
                        # Update additional fields from detailed API response
                        if 'market_cap_rank' in detailed_data:
                            asset.market_cap_rank = detailed_data['market_cap_rank']
                            updated_fields.append(f"market_cap_rank: {detailed_data['market_cap_rank']}")
                        
                        if 'circulating_supply' in detailed_data:
                            asset.circulating_supply = detailed_data['circulating_supply']
                            updated_fields.append(f"circulating_supply: {detailed_data['circulating_supply']:,.0f}")
                        
                        if 'total_supply' in detailed_data:
                            asset.total_supply = detailed_data['total_supply']
                            updated_fields.append(f"total_supply: {detailed_data['total_supply']:,.0f}")
                        
                        if 'max_supply' in detailed_data:
                            asset.max_supply = detailed_data['max_supply']
                            updated_fields.append(f"max_supply: {detailed_data['max_supply']:,.0f}")
                        
                        # Use more accurate price changes from API if available
                        if 'price_change_percentage_24h' in detailed_data:
                            asset.price_change_percentage_24h = detailed_data['price_change_percentage_24h']
                            updated_fields.append(f"price_change_24h_api: {detailed_data['price_change_percentage_24h']:.2f}%")
                        
                        if 'price_change_percentage_7d_in_currency' in detailed_data:
                            asset.price_change_percentage_7d = detailed_data['price_change_percentage_7d_in_currency']
                            updated_fields.append(f"price_change_7d_api: {detailed_data['price_change_percentage_7d_in_currency']:.2f}%")
                        
                        if 'price_change_percentage_30d_in_currency' in detailed_data:
                            asset.price_change_percentage_30d = detailed_data['price_change_percentage_30d_in_currency']
                            updated_fields.append(f"price_change_30d_api: {detailed_data['price_change_percentage_30d_in_currency']:.2f}%")
                        
                        # Update ATH/ATL from API if more accurate
                        if 'ath' in detailed_data and 'ath_date' in detailed_data:
                            api_ath = float(detailed_data['ath']['usd'])
                            if not asset.ath or api_ath > float(asset.ath):
                                asset.ath = api_ath
                                asset.ath_date = datetime.fromisoformat(detailed_data['ath_date']['usd'].replace('Z', '+00:00'))
                                updated_fields.append(f"ath_api: ${api_ath:.8f}")
                        
                        if 'atl' in detailed_data and 'atl_date' in detailed_data:
                            api_atl = float(detailed_data['atl']['usd'])
                            if not asset.atl or api_atl < float(asset.atl):
                                asset.atl = api_atl
                                asset.atl_date = datetime.fromisoformat(detailed_data['atl_date']['usd'].replace('Z', '+00:00'))
                                updated_fields.append(f"atl_api: ${api_atl:.8f}")
                                
                except Exception as e:
                    logger.warning(f"Failed to fetch detailed market data for {coingecko_id}: {e}")
            
            # Update asset with basic metadata
            updated_asset = self.asset_repo.update(db_obj=asset, obj_in=updates)
            
            # Log the updates (commit is already handled in update method)
            if updated_fields:
                logger.info(f"Updated asset {asset_id} metadata and market data: {', '.join(updated_fields)}")
            else:
                logger.debug(f"Updated asset {asset_id} metadata (no market data updates)")
            
        except Exception as e:
            logger.error(f"Error updating asset metadata and market data for asset {asset_id}: {str(e)}")
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
            quality_report = self.get_data_quality_report(asset_id, days=7)
            return quality_report.get('quality_score')
        except Exception as e:
            logger.error(f"Error calculating quality score: {str(e)}")
            return None
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes"""
        timeframe_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080,
            '1M': 43200  # Approximate 30 days
        }
        return timeframe_map.get(timeframe, 1440)  # Default to daily
    
    def _normalize_candle_time(self, candle_time: datetime, timeframe: str) -> datetime:
        """
        Normalize candle time based on timeframe to ensure consistent alignment
        
        This function aligns timestamps to timeframe boundaries to ensure:
        - Consistent data grouping across different sources
        - Proper aggregation alignment for higher timeframes
        - Elimination of sub-timeframe timestamp variations
        
        Args:
            candle_time: Original candle time
            timeframe: Target timeframe (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)
            
        Returns:
            Normalized datetime aligned to timeframe boundaries
            
        Examples:
            - 1m: 14:37:25 -> 14:37:00 (zero seconds)
            - 5m: 14:37:25 -> 14:35:00 (5-minute boundaries: 00, 05, 10, ...)
            - 1h: 14:37:25 -> 14:00:00 (hour boundaries)
            - 4h: 14:37:25 -> 12:00:00 (4-hour boundaries: 00, 04, 08, 12, 16, 20)
            - 1d: 14:37:25 -> 00:00:00 (start of day UTC)
            - 1w: Mon 14:37:25 -> Mon 00:00:00 (start of week, Monday UTC)
            - 1M: 2024-01-15 14:37:25 -> 2024-01-01 00:00:00 (start of month UTC)
        """
        if timeframe == '1m':
            # Align to minute boundaries (zero seconds)
            return candle_time.replace(second=0, microsecond=0)
        
        elif timeframe == '5m':
            # Align to 5-minute boundaries
            minutes = (candle_time.minute // 5) * 5
            return candle_time.replace(minute=minutes, second=0, microsecond=0)
        
        elif timeframe == '15m':
            # Align to 15-minute boundaries
            minutes = (candle_time.minute // 15) * 15
            return candle_time.replace(minute=minutes, second=0, microsecond=0)
        
        elif timeframe == '1h':
            # Align to hour boundaries
            return candle_time.replace(minute=0, second=0, microsecond=0)
        
        elif timeframe == '4h':
            # Align to 4-hour boundaries (0, 4, 8, 12, 16, 20)
            hour = (candle_time.hour // 4) * 4
            return candle_time.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        elif timeframe == '1d':
            # Align to day boundaries (start of day UTC)
            return candle_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        elif timeframe == '1w':
            # Align to week boundaries (Monday 00:00 UTC)
            days_since_monday = candle_time.weekday()
            week_start = candle_time - timedelta(days=days_since_monday)
            return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        elif timeframe == '1M':
            # Align to month boundaries (first day of month 00:00 UTC)
            return candle_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        else:
            # Default: align to minute boundaries for unknown timeframes
            logger.warning(f"Unknown timeframe '{timeframe}', defaulting to minute alignment")
            return candle_time.replace(second=0, microsecond=0)
    
    def _filter_hourly_data(
        self,
        data: List[Dict[str, Any]],
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """
        Filter hourly data to specific intervals (e.g., 4h)
        """
        if timeframe == "1h":
            return data
        
        if timeframe == "4h":
            # Keep every 4th hour
            filtered_data = []
            for i, record in enumerate(data):
                timestamp = record.get('timestamp', 0)
                hour = datetime.fromtimestamp(timestamp / 1000).hour
                if hour % 4 == 0:
                    filtered_data.append(record)
            return filtered_data
        
        return data

    async def calculate_price_change_from_candles(self, asset_id: int) -> Dict[str, Optional[float]]:
        """
        Calculate price change percentages using latest candles from aggregated timeframes
        
        Args:
            asset_id: Asset ID
            
        Returns:
            Dictionary with price change percentages for different periods
        """
        try:
            price_changes = {
                '24h': None,
                '7d': None, 
                '30d': None
            }
            
            # Get latest daily candle for 24h change
            daily_candle = await self.price_data_repo.get_latest_candle_data(asset_id, '1d')
            if daily_candle:
                price_changes['24h'] = daily_candle.get('price_change_percent')
                logger.debug(f"24h change from daily candle for asset {asset_id}: {price_changes['24h']:.2f}%")
            
            # Get latest weekly candle for 7d change
            weekly_candle = await self.price_data_repo.get_latest_candle_data(asset_id, '1w')
            if weekly_candle:
                price_changes['7d'] = weekly_candle.get('price_change_percent')
                logger.debug(f"7d change from weekly candle for asset {asset_id}: {price_changes['7d']:.2f}%")
            
            # Get latest monthly candle for 30d change
            monthly_candle = await self.price_data_repo.get_latest_candle_data(asset_id, '1M')
            if monthly_candle:
                price_changes['30d'] = monthly_candle.get('price_change_percent')
                logger.debug(f"30d change from monthly candle for asset {asset_id}: {price_changes['30d']:.2f}%")
            
            # If no monthly data, try to calculate 30d from multiple weekly candles
            if price_changes['30d'] is None:
                price_changes['30d'] = await self.price_data_repo.calculate_multi_period_change(asset_id, '1w', 4)
            
            return price_changes
            
        except Exception as e:
            logger.error(f"Failed to calculate price changes from candles for asset {asset_id}: {e}")
            return {'24h': None, '7d': None, '30d': None}

    def optimize_storage_for_all_assets(self, source_timeframe: str = '1h',
                                      keep_recent_days: int = 30,
                                      asset_type: str = 'crypto') -> Dict[str, Any]:
        """
        Optimize storage for all assets by aggregating old data
        
        Args:
            source_timeframe: Base timeframe to optimize
            keep_recent_days: Days of recent data to keep in original timeframe
            asset_type: Filter by asset type
            
        Returns:
            Storage optimization results
        """
        # Get all active assets
        assets = self.asset_repo.get_by_filters(
            filters={'asset_type': asset_type, 'is_active': True}
        )
        
        optimization_results = {}
        total_space_saved = 0
        
        for asset in assets:
            try:
                result = self.price_data_repo.optimize_storage_with_aggregation(
                    asset_id=asset.id,
                    source_timeframe=source_timeframe,
                    keep_days=keep_recent_days
                )
                
                optimization_results[asset.id] = {
                    'symbol': asset.symbol,
                    'status': 'success',
                    'deleted_records': result.get('deleted_source_records', 0),
                    'aggregated_records': result.get('aggregated_records', {}),
                    'result': result
                }
                
                total_space_saved += result.get('deleted_source_records', 0)
                
            except Exception as e:
                optimization_results[asset.id] = {
                    'symbol': asset.symbol,
                    'status': 'error',
                    'error': str(e)
                }
        
        successful_optimizations = sum(
            1 for r in optimization_results.values() 
            if r['status'] == 'success'
        )
        
        return {
            'total_assets_processed': len(assets),
            'successful_optimizations': successful_optimizations,
            'total_records_removed': total_space_saved,
            'source_timeframe': source_timeframe,
            'keep_recent_days': keep_recent_days,
            'detailed_results': optimization_results,
            'storage_optimization_summary': {
                'estimated_space_saved_pct': min(85, total_space_saved * 0.001),  # Rough estimate
                'aggregation_strategy': 'old_data_to_higher_timeframes'
            }
        }


    # Timeframe Aggregation Methods (moved from TimeframeAggregationService)
    
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
            asset = self.asset_repo.get(asset_id)
            if not asset:
                return {'error': f'Asset {asset_id} not found'}
            
            # Check what timeframes we can aggregate to
            target_timeframes = self.price_data_repo.get_aggregatable_timeframes(source_timeframe)
            
            if not target_timeframes:
                return {
                    'asset_id': asset_id,
                    'symbol': asset.symbol,
                    'message': f'No aggregatable timeframes for {source_timeframe}',
                    'aggregated_timeframes': []
                }
            
            # Get current status
            status_before = self.price_data_repo.get_aggregation_status(asset_id)
            
            # Determine time range for aggregation
            source_data_count_raw = status_before.get(source_timeframe, {}).get('count', 0)
            try:
                source_data_count = int(source_data_count_raw) if source_data_count_raw is not None else 0
            except (ValueError, TypeError):
                source_data_count = 0
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
                        result = self.price_data_repo.bulk_aggregate_and_store(
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
                result = self.price_data_repo.bulk_aggregate_and_store(
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
            status_after = self.price_data_repo.get_aggregation_status(asset_id)
            
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
            asset = self.asset_repo.get(asset_id)
            if not asset:
                logger.warning(f"Asset {asset_id} not found for timeframe data update")
                return
            
            # Get current status to get latest times and counts
            current_status = self.price_data_repo.get_aggregation_status(asset_id)
            
            updated_timeframes = []
            
            # Update timeframe data for successfully aggregated timeframes
            for timeframe, result in aggregation_results.items():
                # Ensure records is an integer for comparison
                records = result.get('records', 0)
                try:
                    records_int = int(records) if records is not None else 0
                except (ValueError, TypeError):
                    records_int = 0
                
                if result.get('status') == 'success' and records_int > 0:
                    # Get stats from current status
                    timeframe_stats = current_status.get(timeframe, {})
                    count = int(timeframe_stats.get('count', 0)) if timeframe_stats.get('count') is not None else 0
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
        try:
            # Get current aggregation status
            status = self.price_data_repo.get_aggregation_status(asset_id)
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
    
    def _calculate_data_points_needed(self, days: int, timeframe: str) -> int:
        """
        Calculate how many data points we need for given days and timeframe
        
        Args:
            days: Number of days to cover
            timeframe: Timeframe ('1h', '4h', '1d')
            
        Returns:
            int: Number of data points needed
        """
        if timeframe == '1h':
            # 24 hours per day
            return days * 24
        elif timeframe == '4h':
            # 6 four-hour periods per day (24/4)
            return days * 6
        elif timeframe == '1d':
            # 1 day per day
            return days
        else:
            # Default to daily
            return days
    
    def _convert_time_series_to_ohlcv(
        self, 
        time_series_data: Dict[str, List[List[float]]], 
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """
        Convert CoinGecko time-series data to OHLCV format
        
        Args:
            time_series_data: Raw data from CoinGecko API
                Format: {'prices': [[timestamp, price]], 'market_caps': [[timestamp, cap]], 'total_volumes': [[timestamp, vol]]}
            timeframe: Target timeframe ('1h', '4h', '1d')
            
        Returns:
            List of OHLCV records suitable for _process_price_data
        """
        try:
            prices = time_series_data.get('prices', [])
            market_caps = time_series_data.get('market_caps', [])
            volumes = time_series_data.get('total_volumes', [])
            
            if not prices:
                logger.warning("No price data in time-series response")
                return []
            
            # Group data by timeframe periods to create OHLCV candles
            ohlcv_records = []
            
            # For each price point, create a minimal OHLCV record
            # Since CoinGecko doesn't provide true OHLCV data, we'll simulate it
            for i, (timestamp_ms, price) in enumerate(prices):
                try:
                    # Get corresponding market cap and volume
                    market_cap = None
                    volume = 0
                    
                    # Find matching timestamp in market_caps
                    if market_caps:
                        for mc_timestamp, mc_value in market_caps:
                            if abs(mc_timestamp - timestamp_ms) <= 3600000:  # Within 1 hour
                                market_cap = mc_value
                                break
                    
                    # Find matching timestamp in volumes
                    if volumes:
                        for vol_timestamp, vol_value in volumes:
                            if abs(vol_timestamp - timestamp_ms) <= 3600000:  # Within 1 hour
                                volume = vol_value
                                break
                    
                    # Since we only have single price points, we'll create pseudo-OHLCV
                    # For better accuracy, we could use moving averages or interpolation
                    # but for now, we'll use the same price for OHLC with small variations
                    
                    # Create small variations to simulate OHLC (typically within 0.1% of price)
                    variation = price * 0.001  # 0.1% variation
                    
                    record = {
                        'timestamp': timestamp_ms,
                        'open': price - (variation * 0.5),  # Slightly lower open
                        'high': price + variation,          # Slightly higher high
                        'low': price - variation,           # Slightly lower low  
                        'close': price,                     # Actual price as close
                        'volume': volume,
                        'market_cap': market_cap
                    }
                    
                    ohlcv_records.append(record)
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid price data point at index {i}: {e}")
                    continue
            
            logger.info(f"Converted {len(prices)} time-series points to {len(ohlcv_records)} OHLCV records")
            return ohlcv_records
            
        except Exception as e:
            logger.error(f"Error converting time-series to OHLCV: {e}")
            return []


# Global service instance factory
def get_price_data_service(db: Session) -> PriceDataService:
    """Factory function to create PriceDataService instance"""
    return PriceDataService(db)