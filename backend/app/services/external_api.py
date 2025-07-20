# File: ./backend/app/services/external_api.py
# Service layer for managing external API integrations

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import logging
from decimal import Decimal

from app.external.coingecko import CoinGeckoClient, symbol_to_coingecko_id, validate_price_data
from app.repositories import cryptocurrency_repository, price_data_repository
from app.schemas.cryptocurrency import CryptocurrencyCreate
from app.schemas.price_data import PriceDataCreate
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ExternalAPIService:
    """
    Service layer for external API operations
    
    This service coordinates between external APIs (CoinGecko) and internal data storage.
    It handles data fetching, validation, transformation, and persistence.
    """
    
    def __init__(self):
        self.coingecko_client = CoinGeckoClient()
    
    async def sync_cryptocurrency_prices(
        self, 
        db: Session,
        crypto_symbols: Optional[List[str]] = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Sync current cryptocurrency prices from CoinGecko
        
        Args:
            db: Database session
            crypto_symbols: List of symbols to sync (default: all active cryptos)
            save_to_db: Whether to save data to database
            
        Returns:
            dict: Sync results with success/failure counts
        """
        logger.info("Starting cryptocurrency price sync")
        
        # Get cryptocurrencies to sync
        if crypto_symbols:
            # Convert symbols to CoinGecko IDs
            coingecko_ids = [symbol_to_coingecko_id(symbol) for symbol in crypto_symbols]
        else:
            # Get all active cryptocurrencies from database
            active_cryptos = cryptocurrency_repository.get_active(db)
            coingecko_ids = [crypto.coingecko_id for crypto in active_cryptos if crypto.coingecko_id]
        
        if not coingecko_ids:
            logger.warning("No cryptocurrencies found to sync")
            return {"success": 0, "failed": 0, "message": "No cryptocurrencies to sync"}
        
        try:
            # Fetch current prices from CoinGecko
            price_data = await self.coingecko_client.get_current_prices(
                crypto_ids=coingecko_ids,
                include_market_cap=True,
                include_24hr_vol=True,
                include_24hr_change=True
            )
            
            # Validate price data
            if not validate_price_data(price_data):
                raise ValueError("Invalid price data received from CoinGecko")
            
            success_count = 0
            failed_count = 0
            
            for coingecko_id, prices in price_data.items():
                try:
                    if save_to_db:
                        success = await self._save_price_data(db, coingecko_id, prices)
                        if success:
                            success_count += 1
                        else:
                            failed_count += 1
                    else:
                        success_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to save price data for {coingecko_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Price sync completed: {success_count} success, {failed_count} failed")
            
            return {
                "success": success_count,
                "failed": failed_count,
                "total": len(price_data),
                "message": f"Synced {success_count} cryptocurrencies successfully"
            }
            
        except Exception as e:
            logger.error(f"Price sync failed: {e}")
            return {
                "success": 0,
                "failed": len(coingecko_ids),
                "error": str(e),
                "message": "Price sync failed"
            }
    
    async def sync_historical_data(
        self,
        db: Session,
        crypto_symbol: str,
        days: int = 30,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Sync historical price data for a cryptocurrency
        
        Args:
            db: Database session
            crypto_symbol: Cryptocurrency symbol (e.g., 'BTC')
            days: Number of days of historical data
            save_to_db: Whether to save data to database
            
        Returns:
            dict: Sync results
        """
        logger.info(f"Starting historical data sync for {crypto_symbol}")
        
        try:
            # Get cryptocurrency from database
            crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
            if not crypto:
                raise ValueError(f"Cryptocurrency {crypto_symbol} not found in database")
            
            if not crypto.coingecko_id:
                raise ValueError(f"No CoinGecko ID for {crypto_symbol}")
            
            # Fetch historical data from CoinGecko
            historical_data = await self.coingecko_client.get_historical_data(
                crypto_id=crypto.coingecko_id,
                days=days
            )
            
            if save_to_db:
                # Save historical data to database
                saved_count = await self._save_historical_data(db, crypto.id, historical_data)
                
                logger.info(f"Historical data sync completed for {crypto_symbol}: {saved_count} records")
                
                return {
                    "success": True,
                    "saved_records": saved_count,
                    "crypto_id": crypto.id,
                    "days": days,
                    "message": f"Saved {saved_count} historical records for {crypto_symbol}"
                }
            else:
                return {
                    "success": True,
                    "data_points": len(historical_data.get("prices", [])),
                    "message": f"Fetched {len(historical_data.get('prices', []))} data points for {crypto_symbol}"
                }
                
        except Exception as e:
            logger.error(f"Historical data sync failed for {crypto_symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Historical data sync failed for {crypto_symbol}"
            }
    
    async def discover_new_cryptocurrencies(
        self,
        db: Session,
        search_queries: Optional[List[str]] = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Discover and add new cryptocurrencies from CoinGecko
        
        Args:
            db: Database session
            search_queries: List of search terms (default: popular cryptos)
            save_to_db: Whether to save new cryptos to database
            
        Returns:
            dict: Discovery results
        """
        logger.info("Starting cryptocurrency discovery")
        
        # Default popular cryptocurrencies to search for
        if not search_queries:
            search_queries = [
                "bitcoin", "ethereum", "binance", "cardano", "solana",
                "polkadot", "dogecoin", "avalanche", "chainlink", "polygon"
            ]
        
        discovered_cryptos = []
        added_count = 0
        
        try:
            for query in search_queries:
                try:
                    # Search for cryptocurrency
                    search_results = await self.coingecko_client.search_cryptocurrencies(query)
                    
                    for result in search_results[:3]:  # Take top 3 results per query
                        crypto_data = {
                            "symbol": result.get("symbol", "").upper(),
                            "name": result.get("name", ""),
                            "coingecko_id": result.get("id", "")
                        }
                        
                        # Skip if missing required data
                        if not all(crypto_data.values()):
                            continue
                        
                        discovered_cryptos.append(crypto_data)
                        
                        if save_to_db:
                            # Check if crypto already exists
                            existing = cryptocurrency_repository.get_by_symbol(db, crypto_data["symbol"])
                            if not existing:
                                # Add new cryptocurrency to database
                                new_crypto = CryptocurrencyCreate(**crypto_data)
                                cryptocurrency_repository.create(db, obj_in=new_crypto)
                                added_count += 1
                                logger.info(f"Added new cryptocurrency: {crypto_data['symbol']}")
                
                except Exception as e:
                    logger.error(f"Failed to process search query '{query}': {e}")
                    continue
            
            logger.info(f"Cryptocurrency discovery completed: {added_count} new cryptos added")
            
            return {
                "success": True,
                "discovered": len(discovered_cryptos),
                "added": added_count,
                "cryptos": discovered_cryptos,
                "message": f"Discovered {len(discovered_cryptos)} cryptos, added {added_count} new ones"
            }
            
        except Exception as e:
            logger.error(f"Cryptocurrency discovery failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Cryptocurrency discovery failed"
            }
    
    async def validate_external_data(
        self,
        crypto_symbol: str,
        price_threshold: float = 0.05  # 5% price difference threshold
    ) -> Dict[str, Any]:
        """
        Validate external data quality and consistency
        
        Args:
            crypto_symbol: Cryptocurrency symbol to validate
            price_threshold: Maximum allowed price difference percentage
            
        Returns:
            dict: Validation results
        """
        logger.info(f"Validating external data for {crypto_symbol}")
        
        try:
            coingecko_id = symbol_to_coingecko_id(crypto_symbol)
            
            # Get current price from CoinGecko
            price_data = await self.coingecko_client.get_current_prices([coingecko_id])
            current_price = price_data.get(coingecko_id, {}).get("usd")
            
            if not current_price:
                return {
                    "valid": False,
                    "error": "No price data available",
                    "message": f"No current price data for {crypto_symbol}"
                }
            
            # Get market data for additional validation
            market_data = await self.coingecko_client.get_market_data(coingecko_id)
            market_price = market_data.get("market_data", {}).get("current_price", {}).get("usd")
            
            # Compare prices for consistency
            price_difference = 0
            if market_price and current_price:
                price_difference = abs(market_price - current_price) / current_price
            
            is_valid = price_difference <= price_threshold
            
            return {
                "valid": is_valid,
                "current_price": current_price,
                "market_price": market_price,
                "price_difference": price_difference,
                "threshold": price_threshold,
                "message": f"Data validation {'passed' if is_valid else 'failed'} for {crypto_symbol}"
            }
            
        except Exception as e:
            logger.error(f"Data validation failed for {crypto_symbol}: {e}")
            return {
                "valid": False,
                "error": str(e),
                "message": f"Data validation failed for {crypto_symbol}"
            }
    
    async def get_api_status(self) -> Dict[str, Any]:
        """
        Get status of external APIs
        
        Returns:
            dict: API status information
        """
        logger.info("Checking external API status")
        
        status = {
            "coingecko": {
                "available": False,
                "response_time": None,
                "last_check": datetime.utcnow().isoformat()
            }
        }
        
        # Test CoinGecko API
        start_time = datetime.utcnow()
        try:
            ping_result = await self.coingecko_client.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            status["coingecko"]["available"] = ping_result
            status["coingecko"]["response_time"] = response_time
            
        except Exception as e:
            logger.error(f"CoinGecko API check failed: {e}")
            status["coingecko"]["error"] = str(e)
        
        return status
    
    async def _save_price_data(self, db: Session, coingecko_id: str, prices: Dict[str, float]) -> bool:
        """
        Save price data to database
        
        Args:
            db: Database session
            coingecko_id: CoinGecko cryptocurrency ID
            prices: Price data from API
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Find cryptocurrency in database
            crypto = cryptocurrency_repository.get_by_coingecko_id(db, coingecko_id)
            if not crypto:
                logger.warning(f"Cryptocurrency not found for CoinGecko ID: {coingecko_id}")
                return False
            
            # Extract price data
            price = prices.get("usd")
            market_cap = prices.get("usd_market_cap")
            volume_24h = prices.get("usd_24h_vol")
            
            if not price:
                logger.warning(f"No USD price for {coingecko_id}")
                return False
            
            # Create price data record
            price_data = PriceDataCreate(
                crypto_id=crypto.id,
                timestamp=datetime.utcnow(),
                open_price=Decimal(str(price)),
                high_price=Decimal(str(price)),
                low_price=Decimal(str(price)),
                close_price=Decimal(str(price)),
                volume=Decimal(str(volume_24h)) if volume_24h else Decimal("0"),
                market_cap=Decimal(str(market_cap)) if market_cap else None
            )
            
            # Save to database
            price_data_repository.create(db, obj_in=price_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save price data for {coingecko_id}: {e}")
            return False
    
    async def _save_historical_data(
        self, 
        db: Session, 
        crypto_id: int, 
        historical_data: Dict[str, List]
    ) -> int:
        """
        Save historical price data to database
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            historical_data: Historical data from CoinGecko
            
        Returns:
            int: Number of records saved
        """
        saved_count = 0
        prices = historical_data.get("prices", [])
        volumes = historical_data.get("total_volumes", [])
        market_caps = historical_data.get("market_caps", [])
        
        for i, price_point in enumerate(prices):
            try:
                timestamp_ms, price = price_point
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                
                # Get corresponding volume and market cap
                volume = volumes[i][1] if i < len(volumes) else 0
                market_cap = market_caps[i][1] if i < len(market_caps) else None
                
                # Check if data already exists (avoid duplicates)
                existing = price_data_repository.get_by_timestamp(db, crypto_id, timestamp)
                if existing:
                    continue
                
                # Create price data record
                price_data = PriceDataCreate(
                    crypto_id=crypto_id,
                    timestamp=timestamp,
                    open_price=Decimal(str(price)),
                    high_price=Decimal(str(price)),
                    low_price=Decimal(str(price)),
                    close_price=Decimal(str(price)),
                    volume=Decimal(str(volume)),
                    market_cap=Decimal(str(market_cap)) if market_cap else None
                )
                
                price_data_repository.create(db, obj_in=price_data)
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Failed to save historical data point: {e}")
                continue
        
        return saved_count
    
    async def close(self):
        """Close external API clients"""
        await self.coingecko_client.close()


# Global service instance
external_api_service = ExternalAPIService()