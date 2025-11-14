#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bitcoin Data Update Test Script
تست اسکریپت برای بروزرسانی داده های بیتکوین در دیتابیس

This script tests and updates Bitcoin price data in the database.
این اسکریپت داده های قیمت بیتکوین را در دیتابیس تست و بروزرسانی می‌کند.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent / ".." / ".." / "backend"
sys.path.insert(0, str(backend_path.resolve()))

# Configure Django settings if needed
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.services.price_data_service import PriceDataService
    from app.services.data_quality_service import DataQualityService
    from app.repositories.asset.asset_repository import AssetRepository
    from app.models.asset.asset import Asset
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure that:")
    print("1. Virtual environment is active")
    print("2. Dependencies are installed: pip install -r backend/requirements.txt") 
    sys.exit(1)

class BitcoinDataUpdater:
    """کلاس برای بروزرسانی داده های بیتکوین"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.engine = None
        self.session = None
        self.price_service = None
        self.quality_service = None
        self.asset_repo = None
        self.bitcoin_asset = None
        
    async def initialize_database(self):
        """Connect to database and initialize services"""
        print("🔗 Connecting to database...")
        
        try:
            # Create database connection directly
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                # Try to load from .env file
                env_path = Path('../../backend/.env')
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        for line in f:
                            if line.strip().startswith('DATABASE_URL='):
                                db_url = line.strip().split('=', 1)[1].strip('"\'')
                                break
            
            if not db_url:
                raise ValueError("DATABASE_URL not found in environment")
                
            print(f"   📊 Database URL: {db_url[:50]}...")
            self.engine = create_engine(db_url)
            SessionLocal = sessionmaker(bind=self.engine)
            self.session = SessionLocal()
            
            # Initialize services
            self.price_service = PriceDataService(self.session)
            self.quality_service = DataQualityService(self.session)
            self.asset_repo = AssetRepository(self.session)
            
            print("✅ Database connection established")
            return True
            
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return False
    
    async def find_or_create_bitcoin(self):
        """پیدا کردن یا ایجاد رکورد بیتکوین"""
        print("🔍 جستجوی بیتکوین در دیتابیس...")
        
        try:
            # Search for Bitcoin by symbol
            bitcoin_assets = self.asset_repo.get_by_filters(
                filters={'symbol': 'BTC'}
            )
            
            if bitcoin_assets:
                self.bitcoin_asset = bitcoin_assets[0]
                print(f"✅ بیتکوین پیدا شد - ID: {self.bitcoin_asset.id}, نام: {self.bitcoin_asset.name}")
                return self.bitcoin_asset
            
            # If not found, create Bitcoin asset
            print("📝 ایجاد رکورد جدید برای بیتکوین...")
            
            bitcoin_data = {
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'asset_type': 'crypto',
                'is_active': True,
                'is_supported': True,
                'external_ids': {
                    'coingecko': 'bitcoin'
                },
                'metadata': {
                    'description': 'Bitcoin - the first cryptocurrency',
                    'category': 'cryptocurrency',
                    'blockchain': 'bitcoin'
                }
            }
            
            self.bitcoin_asset = self.asset_repo.create(bitcoin_data)
            self.session.commit()
            
            print(f"✅ رکورد بیتکوین ایجاد شد - ID: {self.bitcoin_asset.id}")
            return self.bitcoin_asset
            
        except Exception as e:
            print(f"❌ خطا در پیدا کردن/ایجاد بیتکوین: {e}")
            self.session.rollback()
            return None
    
    async def check_current_data_status(self):
        """بررسی وضعیت فعلی داده ها"""
        if not self.bitcoin_asset:
            print("❌ رکورد بیتکوین موجود نیست")
            return None
        
        print(f"📊 بررسی وضعیت داده های بیتکوین (ID: {self.bitcoin_asset.id})...")
        
        try:
            # Get health report
            health_report = self.quality_service.get_aggregation_health_report(self.bitcoin_asset.id)
            asset_health = health_report.get('detailed_health_data', {}).get(self.bitcoin_asset.id, {})
            
            # Get completeness report for different timeframes
            timeframes = ['1h', '1d', '1w']
            status_report = {}
            
            for tf in timeframes:
                completeness = self.quality_service.get_data_completeness_report(
                    asset_id=self.bitcoin_asset.id,
                    timeframe=tf,
                    days=30
                )
                status_report[tf] = completeness
            
            print("\n📈 گزارش وضعیت داده ها:")
            print(f"   🎯 امتیاز سلامت کلی: {asset_health.get('health_score', 0)}")
            print(f"   📊 داده پایه موجود: {'✅' if asset_health.get('has_base_data') else '❌'}")
            print(f"   📈 داده تجمیعی موجود: {'✅' if asset_health.get('has_aggregated_data') else '❌'}")
            
            if asset_health.get('issues'):
                print(f"   ⚠️  مشکلات: {', '.join(asset_health['issues'])}")
            
            print("\n📋 جزئیات تایم فریم ها:")
            for tf, report in status_report.items():
                if 'completeness' in report:
                    comp = report['completeness']
                    print(f"   {tf}: {comp['actual_records']} رکورد ({comp['completeness_percentage']:.1f}% کامل)")
                else:
                    print(f"   {tf}: خطا در گزارش - {report.get('error', 'نامشخص')}")
            
            return {
                'health_report': health_report,
                'status_report': status_report,
                'needs_update': asset_health.get('health_score', 0) < 80
            }
            
        except Exception as e:
            print(f"❌ خطا در بررسی وضعیت داده ها: {e}")
            return None
    
    async def update_price_data(self, timeframe='1d', days=30):
        """بروزرسانی داده های قیمت"""
        if not self.bitcoin_asset:
            print("❌ رکورد بیتکوین موجود نیست")
            return False
        
        print(f"\n🔄 شروع بروزرسانی داده ها...")
        print(f"   📅 تایم فریم: {timeframe}")
        print(f"   📆 تعداد روز: {days}")
        
        try:
            # Update price data
            result = await self.price_service.populate_price_data(
                asset_id=self.bitcoin_asset.id,
                days=days,
                timeframe=timeframe,
                vs_currency="usd"
            )
            
            if result.get('success'):
                print("✅ بروزرسانی موفقیت آمیز!")
                print(f"   📊 رکورد جدید: {result.get('records_inserted', 0)}")
                print(f"   🔄 رکورد بروزرسانی شده: {result.get('records_updated', 0)}")
                print(f"   ⏭️  رکورد رد شده: {result.get('records_skipped', 0)}")
                print(f"   📈 کل پردازش شده: {result.get('total_processed', 0)}")
                
                # Show data range if available
                data_range = result.get('data_range', {})
                if data_range.get('start') and data_range.get('end'):
                    print(f"   📅 بازه داده: {data_range['start']} تا {data_range['end']}")
                
                return True
            else:
                print(f"❌ بروزرسانی ناموفق: {result.get('message', 'خطای نامشخص')}")
                if result.get('error'):
                    print(f"   🔍 جزئیات خطا: {result['error']}")
                return False
                
        except Exception as e:
            print(f"❌ خطا در بروزرسانی داده ها: {e}")
            return False
    
    async def run_aggregation(self):
        """اجرای تجمیع داده ها"""
        if not self.bitcoin_asset:
            print("❌ رکورد بیتکوین موجود نیست")
            return False
        
        print(f"\n🔧 شروع تجمیع داده ها...")
        
        try:
            # Run aggregation
            aggregation_result = self.price_service.auto_aggregate_for_asset(
                asset_id=self.bitcoin_asset.id,
                source_timeframe='1d',
                force_refresh=False
            )
            
            if 'error' not in aggregation_result:
                print("✅ تجمیع موفقیت آمیز!")
                print(f"   🎯 تایم فریم مبدا: {aggregation_result.get('source_timeframe')}")
                
                aggregated_tfs = aggregation_result.get('aggregated_timeframes', [])
                if aggregated_tfs:
                    print(f"   📊 تایم فریم های تجمیع شده: {', '.join(aggregated_tfs)}")
                
                # Show results for each timeframe
                results = aggregation_result.get('results', {})
                for tf, result in results.items():
                    if result.get('status') == 'success':
                        print(f"   ✅ {tf}: {result.get('records', 0)} رکورد")
                    else:
                        print(f"   ❌ {tf}: {result.get('error', 'خطا')}")
                
                return True
            else:
                print(f"❌ تجمیع ناموفق: {aggregation_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ خطا در تجمیع داده ها: {e}")
            return False
    
    async def final_quality_check(self):
        """بررسی نهایی کیفیت داده ها"""
        if not self.bitcoin_asset:
            print("❌ رکورد بیتکوین موجود نیست")
            return
        
        print(f"\n🔍 بررسی نهایی کیفیت داده ها...")
        
        try:
            # Get updated health report
            health_report = self.quality_service.get_aggregation_health_report(self.bitcoin_asset.id)
            asset_health = health_report.get('detailed_health_data', {}).get(self.bitcoin_asset.id, {})
            
            # Get updated completeness
            completeness_1d = self.quality_service.get_data_completeness_report(
                asset_id=self.bitcoin_asset.id,
                timeframe='1d',
                days=30
            )
            
            print(f"✅ گزارش نهایی:")
            print(f"   🎯 امتیاز سلامت: {asset_health.get('health_score', 0)}")
            print(f"   📊 داده پایه: {'✅' if asset_health.get('has_base_data') else '❌'}")
            print(f"   📈 داده تجمیعی: {'✅' if asset_health.get('has_aggregated_data') else '❌'}")
            
            if 'completeness' in completeness_1d:
                comp = completeness_1d['completeness']
                print(f"   📅 کامل بودن داده روزانه: {comp['completeness_percentage']:.1f}%")
                print(f"   📊 تعداد رکورد: {comp['actual_records']}")
            
            # Show any remaining issues
            issues = asset_health.get('issues', [])
            if issues:
                print(f"   ⚠️  مشکلات باقیمانده: {', '.join(issues)}")
            else:
                print("   ✅ هیچ مشکلی وجود ندارد")
                
        except Exception as e:
            print(f"❌ خطا در بررسی نهایی: {e}")
    
    async def cleanup(self):
        """تمیز کردن منابع"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
        print("🧹 منابع پاک شد")
    
    async def run_complete_update(self):
        """اجرای کامل فرآیند بروزرسانی"""
        print("🚀 شروع فرآیند بروزرسانی کامل بیتکوین")
        print("=" * 50)
        
        # Initialize
        if not await self.initialize_database():
            return False
        
        # Find or create Bitcoin
        if not await self.find_or_create_bitcoin():
            return False
        
        # Check current status
        current_status = await self.check_current_data_status()
        if not current_status:
            return False
        
        # Update data if needed
        update_needed = current_status.get('needs_update', True)
        
        if update_needed:
            print(f"\n🔄 نیاز به بروزرسانی تشخیص داده شد")
            
            # Update different timeframes
            timeframes_to_update = [
                ('1d', 30),  # Daily data for 30 days
                ('1h', 7),   # Hourly data for 7 days
            ]
            
            for timeframe, days in timeframes_to_update:
                success = await self.update_price_data(timeframe, days)
                if not success:
                    print(f"⚠️  بروزرسانی {timeframe} ناموفق بود، ادامه می‌دهیم...")
                await asyncio.sleep(2)  # Brief pause between updates
            
            # Run aggregation
            await self.run_aggregation()
            
        else:
            print(f"\n✅ داده ها به‌روز هستند، نیازی به بروزرسانی نیست")
        
        # Final quality check
        await self.final_quality_check()
        
        print("\n" + "=" * 50)
        print("🎉 فرآیند بروزرسانی کامل شد!")
        
        return True


async def main():
    """تابع اصلی"""
    print("Bitcoin Data Update Test Script")
    print("اسکریپت تست بروزرسانی داده‌های بیتکوین")
    print("=" * 50)
    
    updater = BitcoinDataUpdater()
    
    try:
        success = await updater.run_complete_update()
        if success:
            print("\n✅ تست موفقیت آمیز بود!")
        else:
            print("\n❌ تست ناموفق بود!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏸️  فرآیند توسط کاربر متوقف شد")
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")
        sys.exit(1)
    finally:
        await updater.cleanup()


if __name__ == "__main__":
    # Configure logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the test
    asyncio.run(main())