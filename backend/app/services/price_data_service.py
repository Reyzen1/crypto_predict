# backend/app/services/price_data_service.py
# Service for price data management with timeframe support

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from sqlalchemy.orm import Session

from app.external.coingecko import CoinGeckoClient
from app.repositories.asset.price_data import PriceDataRepository
from app.repositories.asset.asset import AssetRepository
from app.models.asset.asset import Asset
from app.models.asset.price_data import PriceData

logger = logging.getLogger(__name__)


class PriceDataService:
    """
    Service for managing price data operations with timeframe support
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.coingecko_client = CoinGeckoClient()
        self.price_data_repo = PriceDataRepository(db)
        self.asset_repo = AssetRepository(db)
    
    async def populate_asset_price_data(
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
            success = self.price_data_repo.bulk_insert(processed_data)
            
            if success:
                # Update asset metadata
                await self._update_asset_metadata(asset_id, timeframe, len(processed_data))
                
                logger.info(f"Successfully populated {len(processed_data)} records for asset {asset_id}")
                
                return {
                    'success': True,
                    'records_inserted': len(processed_data),
                    'asset_id': asset_id,
                    'timeframe': timeframe,
                    'period_days': days,
                    'message': f'Successfully populated {len(processed_data)} price records'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to insert data into database',
                    'records_inserted': 0
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
                result = await self.populate_asset_price_data(
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
        timeframe: str = "1d",
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Generate data quality report for an asset
        
        Args:
            asset_id: Asset ID
            timeframe: Data timeframe
            days: Days to analyze
            
        Returns:
            dict: Data quality report
        """
        return self.price_data_repo.get_data_quality_report(asset_id, days)
    
    # Private helper methods
    
    def _get_coingecko_id(self, asset: Asset) -> Optional[str]:
        """Get CoinGecko ID from asset external_ids"""
        if not asset.external_ids:
            return None
        
        return asset.external_ids.get('coingecko')
    
    async def _fetch_price_history(
        self,
        coingecko_id: str,
        days: int,
        timeframe: str,
        vs_currency: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch price history from CoinGecko based on timeframe
        """
        try:
            if timeframe == "1d":
                # Daily data - use market_chart endpoint
                data = await self.coingecko_client.get_historical_data(
                    crypto_id=coingecko_id,
                    days=days,
                    vs_currency=vs_currency
                )
            elif timeframe in ["1h", "4h"]:
                # Hourly data - use market_chart endpoint with hourly resolution
                data = await self.coingecko_client.get_market_chart(
                    crypto_id=coingecko_id,
                    days=days,
                    vs_currency=vs_currency,
                    interval="hourly"
                )
                # Filter to specific hour intervals if needed
                data = self._filter_hourly_data(data, timeframe)
            else:
                logger.warning(f"Timeframe {timeframe} not supported for CoinGecko")
                return []
            
            return data
            
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
                
                # Convert timestamp
                if isinstance(record['timestamp'], (int, float)):
                    candle_time = datetime.fromtimestamp(record['timestamp'] / 1000)
                else:
                    candle_time = record['timestamp']
                
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
        records_count: int
    ) -> None:
        """
        Update asset metadata after successful data population
        """
        try:
            asset = self.asset_repo.get(asset_id)
            if not asset:
                return
            
            # Update timeframe_usage
            if not asset.timeframe_usage:
                asset.timeframe_usage = {}
            
            current_count = asset.timeframe_usage.get(timeframe, 0)
            asset.timeframe_usage[timeframe] = current_count + records_count
            
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
            
            # Update asset
            self.asset_repo.update(asset_id, updates)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating asset metadata: {str(e)}")
            self.db.rollback()
    
    def _calculate_data_quality_score(
        self,
        asset_id: int,
        timeframe: str
    ) -> Optional[int]:
        """
        Calculate data quality score based on completeness and accuracy
        """
        try:
            quality_report = self.get_data_quality_report(asset_id, timeframe)
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
            '1w': 10080
        }
        return timeframe_map.get(timeframe, 1440)  # Default to daily
    
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


# Global service instance factory
def get_price_data_service(db: Session) -> PriceDataService:
    """Factory function to create PriceDataService instance"""
    return PriceDataService(db)