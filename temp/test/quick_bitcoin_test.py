#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Bitcoin Data Test

Simple script to quickly test Bitcoin data operations.
This script performs basic Bitcoin data fetching, updating, and aggregation tests.
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
import json
from unittest import result

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def format_datetime_in_dict(obj):
    """Convert datetime objects to ISO format strings in nested dictionaries"""
    if isinstance(obj, dict):
        return {k: format_datetime_in_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [format_datetime_in_dict(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


def print_update_results(result, label="Result"):
    """Print a standardized update result block for an asset.

    Args:
        result: dict or None returned from populate_price_data
        label: display label for the header (e.g., 'BTC' or 'BTC.D')
    """
    print(f"\n=========================={label} Results=======================\n")
    if result is None:
        print("❌ Update failed: No result returned")
    elif result.get('success'):
        print("✅ Update successful!")
        print(f"   📊 New records: {result.get('records_inserted', 0)}")
        print(f"   🔄 Updated records: {result.get('records_updated', 0)}")
        print(f"   🔄 aggregation result: {result.get('aggregation_breakdown', {})}")
    else:
        print(f"❌ Update failed: {result.get('message')}")

async def quick_bitcoin_test():
    """Quick Bitcoin data test function"""
    
    try:
        # Check if we're in virtual environment
        import sys
        venv_indicator = sys.prefix != sys.base_prefix
        if not venv_indicator:
            print("⚠️  Virtual environment is not active, please activate it first:")
            print("   Windows: backend\\venv\\Scripts\\activate")
            print("   Linux/Mac: source backend/venv/bin/activate")
        
        # Import after path setup
        from sqlalchemy.orm import sessionmaker
        import app.core.database as db_module
        from app.services.price_data_service import PriceDataService
        from app.repositories.asset.asset_repository import AssetRepository
        
        print("🚀 Starting quick Bitcoin test...")
        
        # Setup database
        print(f"   📊 Database URL: {db_module.DATABASE_URL[:50]}...")
        SessionLocal = sessionmaker(bind=db_module.engine)
        session = SessionLocal()
        
        # Initialize services
        price_service = PriceDataService(session)
        asset_repo = AssetRepository(session)
        
        print("✅ Connection established")
        

        # Test price data update
        print("🔄 Testing data update...")
        """
        print("\n==========================BTC=======================\n")
        result1 = await price_service.populate_price_data(
            asset_repo.get_by_symbol(symbol='BTC'), 
            timeframe="1d", platform="binance")
        print("\n==========================BTC.D=======================\n")
        result2 = await price_service.populate_price_data(
            asset_repo.get_by_symbol(symbol='BTC.D'), 
            timeframe="1d", platform="tradingview")
        print("\n==========================TOTAL=======================\n")
        """
        result3 = await price_service.populate_price_data(
            asset_repo.get_by_symbol(symbol='TOTAL'), 
            timeframe="1d", platform="tradingview")

        #print_update_results(result1, "BTC")
        #print_update_results(result2, "BTC.D")
        print_update_results(result3, "TOTAL")
        session.close()
        db_module.engine.dispose()
        
        print("🎉 Test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nPlease make sure that:")
        print("1. Virtual environment is active")
        print("2. Dependencies are installed: pip install -r backend/requirements.txt")
        print("3. You are in the main project folder")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(quick_bitcoin_test())