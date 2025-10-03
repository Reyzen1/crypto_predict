# File: ./backend/app/repositories/cryptocurrency.py
# Cryptocurrency repository with specialized crypto operations - FIXED

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models import Cryptocurrency, PriceData
from app.repositories.base import BaseRepository


class CryptocurrencyRepository(BaseRepository[Cryptocurrency, dict, dict]):
    """
    Cryptocurrency repository with specialized operations for crypto management
    """

    def __init__(self):
        super().__init__(Cryptocurrency)

    def get_by_symbol(self, db: Session, symbol: str) -> Optional[Cryptocurrency]:
        """
        Get cryptocurrency by symbol (e.g., 'BTC', 'ETH')
        
        Args:
            db: Database session
            symbol: Cryptocurrency symbol
            
        Returns:
            Cryptocurrency instance or None if not found
        """
        return db.query(Cryptocurrency).filter(
            func.upper(Cryptocurrency.symbol) == symbol.upper()
        ).first()

    def get_active_cryptos(self, db: Session, skip: int = 0, limit: int = 100) -> List[Cryptocurrency]:
        """
        Get all active cryptocurrencies
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active cryptocurrency instances
        """
        return (
            db.query(Cryptocurrency)
            .filter(Cryptocurrency.is_active == True)
            .order_by(Cryptocurrency.symbol)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_coingecko_id(self, db: Session, coingecko_id: str) -> Optional[Cryptocurrency]:
        """
        Get cryptocurrency by CoinGecko ID
        
        Args:
            db: Database session
            coingecko_id: CoinGecko API identifier
            
        Returns:
            Cryptocurrency instance or None if not found
        """
        return db.query(Cryptocurrency).filter(
            Cryptocurrency.coingecko_id == coingecko_id
        ).first()

    def get_by_binance_symbol(self, db: Session, binance_symbol: str) -> Optional[Cryptocurrency]:
        """
        Get cryptocurrency by Binance symbol
        
        Args:
            db: Database session
            binance_symbol: Binance trading pair symbol
            
        Returns:
            Cryptocurrency instance or None if not found
        """
        return db.query(Cryptocurrency).filter(
            Cryptocurrency.binance_symbol == binance_symbol
        ).first()

    def create_crypto(
        self, 
        db: Session, 
        *, 
        symbol: str,
        name: str,
        coingecko_id: Optional[str] = None,
        binance_symbol: Optional[str] = None,
        is_active: bool = True
    ) -> Cryptocurrency:
        """
        Create a new cryptocurrency with validation
        
        Args:
            db: Database session
            symbol: Crypto symbol (e.g., 'BTC')
            name: Full name (e.g., 'Bitcoin')
            coingecko_id: CoinGecko identifier
            binance_symbol: Binance trading symbol
            is_active: Whether crypto is active
            
        Returns:
            Created cryptocurrency instance
            
        Raises:
            ValueError: If symbol already exists
        """
        # Check if symbol already exists
        existing_crypto = self.get_by_symbol(db, symbol)
        if existing_crypto:
            raise ValueError(f"Cryptocurrency with symbol {symbol} already exists")
        
        crypto_data = {
            "symbol": symbol.upper(),
            "name": name,
            "coingecko_id": coingecko_id,
            "binance_symbol": binance_symbol,
            "is_active": is_active
        }
        
        return self.create(db, obj_in=crypto_data)

    def deactivate_crypto(self, db: Session, crypto_id: int) -> Optional[Cryptocurrency]:
        """
        Deactivate cryptocurrency
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            
        Returns:
            Updated cryptocurrency instance or None if not found
        """
        crypto = self.get(db, crypto_id)
        if crypto:
            return self.update(db, db_obj=crypto, obj_in={"is_active": False})
        return None

    def activate_crypto(self, db: Session, crypto_id: int) -> Optional[Cryptocurrency]:
        """
        Activate cryptocurrency
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            
        Returns:
            Updated cryptocurrency instance or None if not found
        """
        crypto = self.get(db, crypto_id)
        if crypto:
            return self.update(db, db_obj=crypto, obj_in={"is_active": True})
        return None

    def search_cryptos(
        self, 
        db: Session, 
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Cryptocurrency]:
        """
        Search cryptocurrencies by symbol or name
        
        Args:
            db: Database session
            search_term: Term to search for
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching cryptocurrency instances
        """
        return (
            db.query(Cryptocurrency)
            .filter(
                Cryptocurrency.symbol.ilike(f"%{search_term}%") |
                Cryptocurrency.name.ilike(f"%{search_term}%")
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_crypto_with_latest_price(self, db: Session, crypto_id: int) -> Optional[dict]:
        """
        Get cryptocurrency with its latest price data
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            
        Returns:
            Dict with crypto info and latest price or None if not found
        """
        crypto = self.get(db, crypto_id)
        if not crypto:
            return None
        
        # Get latest price data
        latest_price = (
            db.query(PriceData)
            .filter(PriceData.crypto_id == crypto_id)
            .order_by(desc(PriceData.timestamp))
            .first()
        )
        
        return {
            "cryptocurrency": crypto,
            "latest_price": latest_price
        }

    def get_cryptos_with_price_data(
        self, 
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """
        Get all active cryptocurrencies with their latest price data
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of dicts with crypto info and latest prices
        """
        cryptos = self.get_active_cryptos(db, skip, limit)
        result = []
        
        for crypto in cryptos:
            crypto_with_price = self.get_crypto_with_latest_price(db, crypto.id)
            if crypto_with_price:
                result.append(crypto_with_price)
        
        return result

    def get_supported_symbols(self, db: Session) -> List[str]:
        """
        Get list of all active cryptocurrency symbols
        
        Args:
            db: Database session
            
        Returns:
            List of active crypto symbols
        """
        cryptos = db.query(Cryptocurrency.symbol).filter(
            Cryptocurrency.is_active == True
        ).all()
        return [crypto.symbol for crypto in cryptos]

    def get_coingecko_ids(self, db: Session) -> List[str]:
        """
        Get list of all CoinGecko IDs for active cryptos
        
        Args:
            db: Database session
            
        Returns:
            List of CoinGecko IDs (excluding None values)
        """
        cryptos = (
            db.query(Cryptocurrency.coingecko_id)
            .filter(Cryptocurrency.is_active == True)
            .filter(Cryptocurrency.coingecko_id.isnot(None))
            .all()
        )
        return [crypto.coingecko_id for crypto in cryptos]

    def get_binance_symbols(self, db: Session) -> List[str]:
        """
        Get list of all Binance symbols for active cryptos
        
        Args:
            db: Database session
            
        Returns:
            List of Binance symbols (excluding None values)
        """
        cryptos = (
            db.query(Cryptocurrency.binance_symbol)
            .filter(Cryptocurrency.is_active == True)
            .filter(Cryptocurrency.binance_symbol.isnot(None))
            .all()
        )
        return [crypto.binance_symbol for crypto in cryptos]

    def count_active_cryptos(self, db: Session) -> int:
        """
        Count total number of active cryptocurrencies
        
        Args:
            db: Database session
            
        Returns:
            Number of active cryptocurrencies
        """
        return db.query(Cryptocurrency).filter(Cryptocurrency.is_active == True).count()


# Create global instance
cryptocurrency_repository = CryptocurrencyRepository()
