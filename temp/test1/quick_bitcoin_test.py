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
        
        # Find Bitcoin
        bitcoin_assets = asset_repo.get_by_filters(filters={'symbol': 'BTC'})
        
        if not bitcoin_assets:
            print("❌ Bitcoin not found in database")
            
            # Create Bitcoin
            bitcoin_data = {
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'asset_type': 'crypto',
                'is_active': True,
                'is_supported': True,
                'external_ids': {'coingecko': 'bitcoin'}
            }
            
            bitcoin = asset_repo.create(bitcoin_data)
            session.commit()
            print(f"✅ Bitcoin created - ID: {bitcoin.id}")
        else:
            bitcoin = bitcoin_assets[0]
            print(f"✅ Bitcoin found - ID: {bitcoin.id}")
        
        # Test price data update
        print("🔄 Testing data update...")
        
        result = await price_service.populate_price_data(
            asset_id=bitcoin.id,
            days=365,
            timeframe="1d"
        )
        if result is None:
            print("❌ Update failed: No result returned")
        elif result.get('success'):
            print("✅ Update successful!")
            print(f"   📊 New records: {result.get('records_inserted', 0)}")
            print(f"   🔄 Updated records: {result.get('records_updated', 0)}")
        else:
            print(f"❌ Update failed: {result.get('message')}")
        
       
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