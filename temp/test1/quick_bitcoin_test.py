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

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

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
            days=7,
            timeframe="1d"
        )
        
        if result.get('success'):
            print("✅ Update successful!")
            print(f"   📊 New records: {result.get('records_inserted', 0)}")
            print(f"   🔄 Updated records: {result.get('records_updated', 0)}")
        else:
            print(f"❌ Update failed: {result.get('message')}")
        
        # Test aggregation
        print("🔧 Testing aggregation...")
        
        agg_result = price_service.auto_aggregate_for_asset(
            asset_id=bitcoin.id,
            source_timeframe='1d'
        )
        
        if 'error' not in agg_result:
            print("✅ Aggregation successful!")
            results = agg_result.get('results', {})
            for tf, res in results.items():
                if res.get('status') == 'success':
                    print(f"   ✅ {tf}: {res.get('records', 0)} records")
        else:
            print(f"❌ Aggregation failed: {agg_result.get('error')}")
        
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