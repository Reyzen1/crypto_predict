# File: ./backend/app/repositories/__init__.py
# Repository package initialization - exports all repositories

from app.repositories.base import BaseRepository
from app.repositories.user import UserRepository, user_repository
from app.repositories.cryptocurrency import CryptocurrencyRepository, cryptocurrency_repository
from app.repositories.price_data import PriceDataRepository, price_data_repository

# Export all repository classes
__all__ = [
    # Base repository
    "BaseRepository",
    
    # Repository classes
    "UserRepository",
    "CryptocurrencyRepository", 
    "PriceDataRepository",
    
    # Repository instances (ready to use)
    "user_repository",
    "cryptocurrency_repository",
    "price_data_repository"
]
