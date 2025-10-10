# Test script for PriceDataService functionality
# File: backend/test_price_service.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from app.db.database import get_db
from app.services.price_data_service import PriceDataService
from app.repositories.asset_repository import AssetRepository
from app.repositories.price_data_repository import PriceDataRepository
from datetime import datetime

def test_price_service():
    """Test PriceDataService functionality"""
    print("=== Testing PriceDataService ===")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Initialize repositories and service
        asset_repo = AssetRepository(db)
        price_data_repo = PriceDataRepository(db)
        price_service = PriceDataService(asset_repo, price_data_repo)
        
        print("✓ Service initialized successfully")
        
        # Test 1: Get active assets
        active_assets = asset_repo.get_active_assets()
        print(f"✓ Found {len(active_assets)} active assets")
        
        if active_assets:
            asset = active_assets[0]
            print(f"Testing with asset: {asset.symbol} (ID: {asset.id})")
            
            # Test 2: Fetch latest price data
            result = price_service.populate_asset_price_data(
                asset_id=asset.id,
                timeframe="1d",
                limit=1
            )
            
            if result["success"]:
                print("✓ Successfully fetched latest price data")
                print(f"  Records processed: {result.get('records_count', 0)}")
            else:
                print(f"✗ Failed to fetch price data: {result.get('error', 'Unknown error')}")
            
            # Test 3: Generate data quality report
            quality_report = price_service.generate_data_quality_report(
                asset_id=asset.id,
                timeframe="1d"
            )
            
            print("✓ Generated data quality report:")
            print(f"  Quality score: {quality_report.get('quality_score', 0)}%")
            print(f"  Total records: {quality_report.get('total_records', 0)}")
            
        else:
            print("✗ No active assets found for testing")
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    test_price_service()