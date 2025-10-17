# Example service for timeframe aggregation
# backend/app/services/timeframe_aggregation_service.py

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from ..repositories.asset.price_data_repository import PriceDataRepository
from ..repositories.asset.asset_repository import AssetRepository
from ..external.coingecko import CoinGeckoClient

logger = logging.getLogger(__name__)


class TimeframeAggregationService:
    """
    Service for managing timeframe aggregation operations
    
    This service provides high-level methods for:
    - Automated timeframe aggregation
    - Storage optimization 
    - Data quality maintenance
    - Performance monitoring
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.price_repo = PriceDataRepository(db)
        self.asset_repo = AssetRepository(db)
        self.coingecko_client = CoinGeckoClient()
    
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
            asset = self.asset_repo.get_by_id(asset_id)
            if not asset:
                return {'error': f'Asset {asset_id} not found'}
            
            # Check what timeframes we can aggregate to
            target_timeframes = self.price_repo.get_aggregatable_timeframes(source_timeframe)
            
            if not target_timeframes:
                return {
                    'asset_id': asset_id,
                    'symbol': asset.symbol,
                    'message': f'No aggregatable timeframes for {source_timeframe}',
                    'aggregated_timeframes': []
                }
            
            # Get current status
            status_before = self.price_repo.get_aggregation_status(asset_id)
            
            # Determine time range for aggregation
            source_data_count = status_before.get(source_timeframe, {}).get('count', 0)
            if source_data_count == 0:
                return {
                    'asset_id': asset_id,
                    'symbol': asset.symbol,
                    'error': f'No {source_timeframe} data available for aggregation'
                }
            
            # Calculate aggregation window (last 7 days for incremental)
            if not force_refresh:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=7)
            else:
                start_time = None
                end_time = None
            
            # Perform aggregation
            aggregation_results = self.price_repo.bulk_aggregate_and_store(
                asset_id=asset_id,
                source_timeframe=source_timeframe,
                target_timeframes=target_timeframes,
                start_time=start_time,
                end_time=end_time
            )
            
            # Get status after aggregation
            status_after = self.price_repo.get_aggregation_status(asset_id)
            
            return {
                'asset_id': asset_id,
                'symbol': asset.symbol,
                'source_timeframe': source_timeframe,
                'aggregated_timeframes': target_timeframes,
                'results': aggregation_results,
                'status_before': status_before,
                'status_after': status_after,
                'aggregation_window': {
                    'start_time': start_time.isoformat() if start_time else 'all_data',
                    'end_time': end_time.isoformat() if end_time else 'all_data'
                }
            }
            
        except Exception as e:
            return {
                'asset_id': asset_id,
                'error': f'Aggregation failed: {str(e)}'
            }
    
    def batch_aggregate_all_assets(self, source_timeframe: str = '1h',
                                 limit: int = None,
                                 asset_type: str = 'crypto') -> Dict[str, Any]:
        """
        Run aggregation for all assets in the system
        
        Args:
            source_timeframe: Base timeframe for aggregation
            limit: Maximum number of assets to process
            asset_type: Filter by asset type
            
        Returns:
            Batch processing results
        """
        # Get all active assets
        assets = self.asset_repo.get_by_filters(
            filters={'asset_type': asset_type, 'is_active': True},
            limit=limit
        )
        
        if not assets:
            return {'error': 'No assets found for aggregation'}
        
        asset_ids = [asset.id for asset in assets]
        
        # Run parallel aggregation
        results = self.price_repo.parallel_aggregate_multiple_assets(
            asset_ids=asset_ids,
            source_timeframe=source_timeframe
        )
        
        # Analyze results
        successful = sum(1 for r in results.values() if r['status'] == 'success')
        failed = len(results) - successful
        
        failed_assets = [
            {'asset_id': aid, 'error': r['error']} 
            for aid, r in results.items() 
            if r['status'] == 'error'
        ]
        
        return {
            'total_assets': len(assets),
            'successful': successful,
            'failed': failed,
            'source_timeframe': source_timeframe,
            'failed_assets': failed_assets,
            'detailed_results': results
        }
    
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
                result = self.price_repo.optimize_storage_with_aggregation(
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
    
    def get_aggregation_health_report(self, asset_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate health report for timeframe aggregation status
        
        Args:
            asset_id: Specific asset to check (None for all assets)
            
        Returns:
            Health report with recommendations
        """
        if asset_id:
            assets_to_check = [self.asset_repo.get_by_id(asset_id)]
            assets_to_check = [a for a in assets_to_check if a]
        else:
            assets_to_check = self.asset_repo.get_by_filters(
                filters={'is_active': True}
            )
        
        if not assets_to_check:
            return {'error': 'No assets found for health check'}
        
        health_data = {}
        recommendations = []
        
        for asset in assets_to_check:
            status = self.price_repo.get_aggregation_status(asset.id)
            
            # Analyze health for this asset
            base_timeframes = ['1m', '5m', '15m', '1h']
            higher_timeframes = ['4h', '1d', '1w', '1M']
            
            has_base_data = any(status.get(tf, {}).get('count', 0) > 0 for tf in base_timeframes)
            has_aggregated_data = any(status.get(tf, {}).get('count', 0) > 0 for tf in higher_timeframes)
            
            health_score = 100
            issues = []
            
            if not has_base_data:
                health_score -= 50
                issues.append('No base timeframe data available')
            
            if has_base_data and not has_aggregated_data:
                health_score -= 30
                issues.append('Missing aggregated timeframes')
                recommendations.append(f'Run aggregation for asset {asset.symbol} (ID: {asset.id})')
            
            # Check data freshness
            latest_times = {}
            for tf, info in status.items():
                if info.get('latest_time'):
                    latest_times[tf] = info['latest_time']
            
            if latest_times:
                most_recent = max(latest_times.values())
                time_since_update = datetime.utcnow() - datetime.fromisoformat(most_recent.replace('Z', '+00:00'))
                
                if time_since_update > timedelta(hours=24):
                    health_score -= 20
                    issues.append(f'Data is {time_since_update.days} days old')
                    recommendations.append(f'Update data for asset {asset.symbol}')
            
            health_data[asset.id] = {
                'symbol': asset.symbol,
                'health_score': max(0, health_score),
                'status': status,
                'issues': issues,
                'has_base_data': has_base_data,
                'has_aggregated_data': has_aggregated_data
            }
        
        # Overall system health
        avg_health = sum(data['health_score'] for data in health_data.values()) / len(health_data)
        
        return {
            'overall_health_score': round(avg_health, 1),
            'overall_grade': 'A' if avg_health >= 90 else 'B' if avg_health >= 80 else 'C' if avg_health >= 70 else 'D' if avg_health >= 60 else 'F',
            'total_assets_checked': len(assets_to_check),
            'assets_needing_attention': sum(1 for data in health_data.values() if data['health_score'] < 80),
            'recommendations': recommendations,
            'detailed_health_data': health_data
        }

    async def handle_mixed_interval_coingecko_data(self, asset_id: int, 
                                                 coingecko_id: str,
                                                 days_back: int = 30,
                                                 update_mode: str = 'smart') -> Dict[str, Any]:
        """
        Handle CoinGecko data with mixed intervals (hourly for recent, daily for older)
        
        CoinGecko behavior:
        - Last 1 day: 5-minute intervals  
        - Last 30 days: hourly intervals
        - Beyond 30 days: daily intervals
        
        This method intelligently fetches and aggregates data across these boundaries.
        Handles overlapping data scenarios (e.g., updating after a week when you already 
        have some hourly data).
        
        Args:
            asset_id: Internal asset ID
            coingecko_id: CoinGecko cryptocurrency ID (e.g., 'bitcoin')
            days_back: Total days of data to fetch
            update_mode: 'smart' (detect existing data), 'force' (overwrite all), 'incremental' (only new)
            
        Returns:
            Aggregation results with mixed interval handling and overlap resolution
        """
        try:
            # Get asset info
            asset = self.asset_repo.get_by_id(asset_id)
            if not asset:
                return {'error': f'Asset {asset_id} not found'}
            
            results = {
                'asset_id': asset_id,
                'symbol': asset.symbol,
                'coingecko_id': coingecko_id,
                'total_days_requested': days_back,
                'intervals_processed': [],
                'aggregation_results': {},
                'data_quality': {}
            }
            
            # Analyze existing data to plan optimal update strategy
            existing_data_analysis = await self._analyze_existing_data(asset_id, days_back)
            
            # Define CoinGecko's interval boundaries with overlap handling
            interval_plan = await self._plan_coingecko_intervals_with_overlap(
                days_back, existing_data_analysis, update_mode
            )
            
            for interval_config in interval_plan:
                try:
                    interval_result = await self._fetch_and_process_interval(
                        asset_id=asset_id,
                        coingecko_id=coingecko_id,
                        config=interval_config
                    )
                    
                    results['intervals_processed'].append(interval_result)
                    
                    # Aggregate processed data to higher timeframes
                    if interval_result['status'] == 'success':
                        source_timeframe = interval_result['source_timeframe']
                        aggregation_result = await self._aggregate_interval_data(
                            asset_id=asset_id,
                            source_timeframe=source_timeframe,
                            data_period=interval_result['period']
                        )
                        results['aggregation_results'][source_timeframe] = aggregation_result
                
                except Exception as e:
                    logger.error(f"Failed to process interval {interval_config}: {str(e)}")
                    results['intervals_processed'].append({
                        'config': interval_config,
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Generate data quality report
            results['data_quality'] = await self._assess_mixed_data_quality(asset_id, days_back)
            
            return results
            
        except Exception as e:
            logger.error(f"Mixed interval processing failed for asset {asset_id}: {str(e)}")
            return {
                'asset_id': asset_id,
                'error': f'Mixed interval processing failed: {str(e)}'
            }

    def _plan_coingecko_intervals(self, days_back: int) -> List[Dict[str, Any]]:
        """
        Plan optimal CoinGecko API calls based on their interval structure
        
        Args:
            days_back: Total days to fetch
            
        Returns:
            List of interval configurations
        """
        plans = []
        
        # CoinGecko interval rules:
        # - 1 day: 5min intervals (very granular, convert to 1h)
        # - 2-30 days: hourly intervals  
        # - 31+ days: daily intervals
        
        if days_back <= 1:
            # Recent data: 5-minute intervals from CoinGecko
            plans.append({
                'days': 1,
                'coingecko_interval': 'minutely',  # CoinGecko auto-selects 5min
                'target_timeframe': '1h',  # We'll aggregate 5min to 1h
                'period_name': 'recent_granular'
            })
            
        elif days_back <= 30:
            # Medium-term: hourly intervals
            plans.append({
                'days': min(days_back, 30),
                'coingecko_interval': 'hourly',
                'target_timeframe': '1h',
                'period_name': 'recent_hourly'
            })
            
        else:
            # Split into hourly (recent 30 days) + daily (older data)
            plans.extend([
                {
                    'days': 30,
                    'coingecko_interval': 'hourly', 
                    'target_timeframe': '1h',
                    'period_name': 'recent_hourly'
                },
                {
                    'days': days_back - 30,
                    'coingecko_interval': 'daily',
                    'target_timeframe': '1d',
                    'period_name': 'historical_daily',
                    'start_days_ago': 30  # Start from 30 days ago
                }
            ])
        
        return plans

    async def _fetch_and_process_interval(self, asset_id: int, coingecko_id: str, 
                                        config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch and process data for a specific interval configuration
        
        Args:
            asset_id: Internal asset ID
            coingecko_id: CoinGecko ID
            config: Interval configuration
            
        Returns:
            Processing results
        """
        try:
            # Fetch data from CoinGecko
            market_data = await self.coingecko_client.get_market_chart(
                crypto_id=coingecko_id,
                vs_currency='usd',
                days=config['days'],
                interval=config['coingecko_interval']
            )
            
            # Convert CoinGecko data to our format
            processed_records = self._convert_coingecko_to_price_data(
                asset_id=asset_id,
                market_data=market_data,
                target_timeframe=config['target_timeframe']
            )
            
            # Store in database
            stored_count = 0
            for record in processed_records:
                # Check for existing data
                existing = self.price_repo.db.query(self.price_repo.model).filter(
                    self.price_repo.model.asset_id == record['asset_id'],
                    self.price_repo.model.timeframe == record['timeframe'],
                    self.price_repo.model.candle_time == record['candle_time']
                ).first()
                
                if not existing:
                    new_record = self.price_repo.model(**record)
                    self.price_repo.db.add(new_record)
                    stored_count += 1
                else:
                    # Update existing record
                    for key, value in record.items():
                        if key not in ['asset_id', 'timeframe', 'candle_time']:
                            setattr(existing, key, value)
                    stored_count += 1
            
            self.price_repo.db.commit()
            
            return {
                'config': config,
                'status': 'success',
                'source_timeframe': config['target_timeframe'],
                'period': config['period_name'],
                'fetched_records': len(processed_records),
                'stored_records': stored_count,
                'data_range': {
                    'start': min(r['candle_time'] for r in processed_records) if processed_records else None,
                    'end': max(r['candle_time'] for r in processed_records) if processed_records else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch interval data: {str(e)}")
            return {
                'config': config,
                'status': 'error',
                'error': str(e)
            }

    def _convert_coingecko_to_price_data(self, asset_id: int, market_data: Dict[str, Any], 
                                       target_timeframe: str) -> List[Dict[str, Any]]:
        """
        Convert CoinGecko market chart data to our price_data format
        
        Args:
            asset_id: Internal asset ID
            market_data: CoinGecko market chart response
            target_timeframe: Target timeframe for storage
            
        Returns:
            List of price_data records
        """
        records = []
        
        # Extract prices, volumes, market_caps
        prices = market_data.get('prices', [])
        volumes = market_data.get('total_volumes', [])
        market_caps = market_data.get('market_caps', [])
        
        # Align data by timestamp
        price_dict = {int(item[0]): float(item[1]) for item in prices}
        volume_dict = {int(item[0]): float(item[1]) for item in volumes}
        market_cap_dict = {int(item[0]): float(item[1]) for item in market_caps}
        
        # Process all timestamps
        all_timestamps = set(price_dict.keys()) | set(volume_dict.keys()) | set(market_cap_dict.keys())
        
        for timestamp_ms in sorted(all_timestamps):
            # Convert to datetime
            candle_time = datetime.fromtimestamp(timestamp_ms / 1000.0)
            
            # For CoinGecko data, we assume OHLC = closing price (they don't provide OHLC)
            price = price_dict.get(timestamp_ms, 0)
            volume = volume_dict.get(timestamp_ms, 0)
            market_cap = market_cap_dict.get(timestamp_ms)
            
            if price > 0:  # Only store records with valid prices
                record = {
                    'asset_id': asset_id,
                    'timeframe': target_timeframe,
                    'candle_time': candle_time,
                    'open_price': price,  # CoinGecko doesn't provide OHLC
                    'high_price': price,
                    'low_price': price,
                    'close_price': price,
                    'volume': volume,
                    'market_cap': market_cap,
                    'trade_count': None,
                    'vwap': price,  # Approximate VWAP as price
                    'is_validated': True  # CoinGecko data is considered validated
                }
                records.append(record)
        
        return records

    async def _aggregate_interval_data(self, asset_id: int, source_timeframe: str, 
                                     data_period: str) -> Dict[str, Any]:
        """
        Aggregate data from processed intervals to higher timeframes
        
        Args:
            asset_id: Asset ID
            source_timeframe: Source timeframe to aggregate from
            data_period: Period identifier for logging
            
        Returns:
            Aggregation results
        """
        try:
            # Get aggregatable timeframes
            target_timeframes = self.price_repo.get_aggregatable_timeframes(source_timeframe)
            
            if not target_timeframes:
                return {
                    'source_timeframe': source_timeframe,
                    'period': data_period,
                    'message': 'No aggregatable timeframes found'
                }
            
            # Perform aggregation
            aggregation_results = self.price_repo.bulk_aggregate_and_store(
                asset_id=asset_id,
                source_timeframe=source_timeframe,
                target_timeframes=target_timeframes
            )
            
            return {
                'source_timeframe': source_timeframe,
                'period': data_period,
                'target_timeframes': target_timeframes,
                'results': aggregation_results,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Aggregation failed for {source_timeframe} in {data_period}: {str(e)}")
            return {
                'source_timeframe': source_timeframe,
                'period': data_period,
                'status': 'error',
                'error': str(e)
            }

    async def _assess_mixed_data_quality(self, asset_id: int, days_back: int) -> Dict[str, Any]:
        """
        Assess data quality for mixed interval data
        
        Args:
            asset_id: Asset ID
            days_back: Days of data to assess
            
        Returns:
            Data quality assessment
        """
        try:
            # Get aggregation status
            status = self.price_repo.get_aggregation_status(asset_id)
            
            # Check data coverage across timeframes
            coverage_analysis = {}
            expected_timeframes = ['1h', '4h', '1d', '1w']
            
            for tf in expected_timeframes:
                tf_status = status.get(tf, {})
                count = tf_status.get('count', 0)
                latest = tf_status.get('latest_time')
                
                # Calculate expected record count for timeframe
                hours_in_period = days_back * 24
                if tf == '1h':
                    expected_count = hours_in_period
                elif tf == '4h':
                    expected_count = hours_in_period // 4
                elif tf == '1d':
                    expected_count = days_back
                elif tf == '1w':
                    expected_count = max(1, days_back // 7)
                else:
                    expected_count = 0
                
                coverage_pct = (count / expected_count * 100) if expected_count > 0 else 0
                
                coverage_analysis[tf] = {
                    'actual_count': count,
                    'expected_count': expected_count,
                    'coverage_percentage': min(100, round(coverage_pct, 1)),
                    'latest_data': latest,
                    'status': 'good' if coverage_pct >= 90 else 'partial' if coverage_pct >= 50 else 'poor'
                }
            
            # Calculate overall quality score
            avg_coverage = sum(c['coverage_percentage'] for c in coverage_analysis.values()) / len(coverage_analysis)
            
            return {
                'overall_coverage_percentage': round(avg_coverage, 1),
                'overall_grade': 'A' if avg_coverage >= 90 else 'B' if avg_coverage >= 80 else 'C' if avg_coverage >= 70 else 'D' if avg_coverage >= 60 else 'F',
                'timeframe_coverage': coverage_analysis,
                'assessment_period_days': days_back,
                'mixed_interval_handling': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Data quality assessment failed: {str(e)}")
            return {
                'error': f'Quality assessment failed: {str(e)}'
            }

    async def batch_process_mixed_interval_data(self, coingecko_mappings: List[Dict[str, Any]], 
                                              days_back: int = 30,
                                              max_concurrent: int = 3) -> Dict[str, Any]:
        """
        Batch process mixed interval data for multiple assets
        
        Args:
            coingecko_mappings: List of {'asset_id': int, 'coingecko_id': str} mappings
            days_back: Days of historical data to fetch
            max_concurrent: Maximum concurrent API calls
            
        Returns:
            Batch processing results
        """
        import asyncio
        from itertools import islice
        
        def chunked(iterable, size):
            """Split iterable into chunks of specified size"""
            iterator = iter(iterable)
            while chunk := list(islice(iterator, size)):
                yield chunk
        
        results = {
            'total_assets': len(coingecko_mappings),
            'days_back': days_back,
            'successful': 0,
            'failed': 0,
            'detailed_results': {},
            'summary': {}
        }
        
        # Process in batches to respect rate limits
        for batch_num, batch in enumerate(chunked(coingecko_mappings, max_concurrent)):
            logger.info(f"Processing batch {batch_num + 1} with {len(batch)} assets")
            
            # Create coroutines for this batch
            batch_tasks = [
                self.handle_mixed_interval_coingecko_data(
                    asset_id=mapping['asset_id'],
                    coingecko_id=mapping['coingecko_id'],
                    days_back=days_back
                )
                for mapping in batch
            ]
            
            try:
                # Execute batch concurrently
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results
                for mapping, result in zip(batch, batch_results):
                    asset_id = mapping['asset_id']
                    
                    if isinstance(result, Exception):
                        results['failed'] += 1
                        results['detailed_results'][asset_id] = {
                            'status': 'error',
                            'error': str(result),
                            'coingecko_id': mapping['coingecko_id']
                        }
                    elif 'error' in result:
                        results['failed'] += 1
                        results['detailed_results'][asset_id] = result
                    else:
                        results['successful'] += 1
                        results['detailed_results'][asset_id] = result
                
                # Add delay between batches to respect rate limits
                if batch_num < len(list(chunked(coingecko_mappings, max_concurrent))) - 1:
                    await asyncio.sleep(2)  # 2 second delay between batches
                
            except Exception as e:
                logger.error(f"Batch {batch_num + 1} failed: {str(e)}")
                for mapping in batch:
                    results['failed'] += 1
                    results['detailed_results'][mapping['asset_id']] = {
                        'status': 'error',
                        'error': f'Batch processing failed: {str(e)}',
                        'coingecko_id': mapping['coingecko_id']
                    }
        
        # Generate summary
        if results['successful'] > 0:
            successful_results = [r for r in results['detailed_results'].values() 
                                if r.get('status') != 'error']
            
            total_intervals = sum(len(r.get('intervals_processed', [])) for r in successful_results)
            total_records = sum(
                sum(interval.get('stored_records', 0) for interval in r.get('intervals_processed', []))
                for r in successful_results
            )
            
            results['summary'] = {
                'success_rate_pct': round(results['successful'] / results['total_assets'] * 100, 1),
                'total_intervals_processed': total_intervals,
                'total_records_stored': total_records,
                'avg_records_per_asset': round(total_records / results['successful'], 1) if results['successful'] > 0 else 0
            }
        
        return results

    def get_coingecko_data_strategy_recommendation(self, days_back: int) -> Dict[str, Any]:
        """
        Get recommendation for optimal CoinGecko data fetching strategy
        
        Args:
            days_back: Number of days to fetch
            
        Returns:
            Strategy recommendation with rationale
        """
        strategy = {
            'days_requested': days_back,
            'recommended_approach': '',
            'api_calls_needed': 0,
            'expected_intervals': [],
            'rate_limit_considerations': '',
            'storage_estimation': {},
            'rationale': []
        }
        
        if days_back <= 1:
            strategy.update({
                'recommended_approach': 'single_granular_fetch',
                'api_calls_needed': 1,
                'expected_intervals': ['5-minute (from CoinGecko) → 1h (aggregated)'],
                'rate_limit_considerations': 'Low impact - 1 API call per asset',
                'rationale': [
                    'Recent data available in 5-minute intervals',
                    'High granularity allows flexible aggregation',
                    'Single API call keeps rate limit usage low'
                ]
            })
        
        elif days_back <= 30:
            strategy.update({
                'recommended_approach': 'single_hourly_fetch',
                'api_calls_needed': 1,
                'expected_intervals': ['1h (native from CoinGecko)'],
                'rate_limit_considerations': 'Low impact - 1 API call per asset',
                'rationale': [
                    'Optimal balance of granularity and API efficiency',
                    'Native hourly data from CoinGecko',
                    'No need for complex aggregation'
                ]
            })
        
        elif days_back <= 90:
            strategy.update({
                'recommended_approach': 'mixed_interval_fetch',
                'api_calls_needed': 2,
                'expected_intervals': [
                    '1h (last 30 days)',
                    '1d (31-90 days ago)'
                ],
                'rate_limit_considerations': 'Medium impact - 2 API calls per asset',
                'rationale': [
                    'Maintains hourly granularity for recent data',
                    'Daily data sufficient for older periods',
                    'Balances detail with API efficiency'
                ]
            })
        
        else:
            strategy.update({
                'recommended_approach': 'segmented_daily_fetch',
                'api_calls_needed': max(2, (days_back // 365) + 1),
                'expected_intervals': [
                    '1h (last 30 days)',
                    f'1d (31-{days_back} days ago)'
                ],
                'rate_limit_considerations': f'Higher impact - {strategy["api_calls_needed"]} API calls per asset',
                'rationale': [
                    'Long historical periods require daily intervals',
                    'Recent data still maintained at hourly granularity',
                    'May need segmentation for very long periods (>365 days)'
                ]
            })
        
        # Storage estimation
        records_per_day = {
            '5m': 288,   # 24h * 12 (5-min intervals)
            '1h': 24,    # 24 hours
            '1d': 1      # 1 day
        }
        
        estimated_records = 0
        if days_back <= 1:
            estimated_records = records_per_day['5m'] * days_back
        elif days_back <= 30:
            estimated_records = records_per_day['1h'] * days_back
        else:
            estimated_records = (records_per_day['1h'] * 30) + (records_per_day['1d'] * (days_back - 30))
        
        strategy['storage_estimation'] = {
            'estimated_base_records': estimated_records,
            'with_aggregation_multiplier': 1.8,  # Accounting for 4h, 1d, etc.
            'total_estimated_records': int(estimated_records * 1.8)
        }
        
        return strategy

    async def _analyze_existing_data(self, asset_id: int, days_back: int) -> Dict[str, Any]:
        """
        Analyze existing data to understand current coverage and overlaps
        
        Args:
            asset_id: Asset to analyze
            days_back: Period to analyze
            
        Returns:
            Analysis of existing data coverage
        """
        try:
            # Get current aggregation status
            status = self.price_repo.get_aggregation_status(asset_id)
            
            # Calculate date ranges
            now = datetime.utcnow()
            cutoff_date = now - timedelta(days=days_back)
            hourly_boundary = now - timedelta(days=30)  # CoinGecko's hourly boundary
            
            analysis = {
                'total_period_days': days_back,
                'cutoff_date': cutoff_date,
                'hourly_boundary_date': hourly_boundary,
                'existing_coverage': {},
                'gaps_detected': [],
                'overlap_zones': [],
                'recommended_strategy': 'full_fetch'  # Default
            }
            
            # Analyze coverage for each timeframe
            for timeframe in ['1h', '1d']:
                tf_status = status.get(timeframe, {})
                count = tf_status.get('count', 0)
                latest_str = tf_status.get('latest_time')
                earliest_str = tf_status.get('earliest_time')
                
                if count > 0 and latest_str and earliest_str:
                    latest = datetime.fromisoformat(latest_str.replace('Z', '+00:00'))
                    earliest = datetime.fromisoformat(earliest_str.replace('Z', '+00:00'))
                    
                    # Check coverage in different zones
                    recent_coverage = latest >= hourly_boundary
                    historical_coverage = earliest <= hourly_boundary
                    
                    analysis['existing_coverage'][timeframe] = {
                        'count': count,
                        'latest': latest,
                        'earliest': earliest,
                        'recent_zone_covered': recent_coverage,
                        'historical_zone_covered': historical_coverage,
                        'data_age_hours': (now - latest).total_seconds() / 3600,
                        'coverage_days': (latest - earliest).days
                    }
                    
                    # Detect gaps
                    if latest < now - timedelta(hours=2):  # More than 2 hours old
                        gap_hours = (now - latest).total_seconds() / 3600
                        analysis['gaps_detected'].append({
                            'timeframe': timeframe,
                            'type': 'recent_gap',
                            'gap_hours': gap_hours,
                            'needs_update': gap_hours > 1
                        })
                    
                    # Detect potential overlaps in the 30-day boundary zone
                    if timeframe == '1h' and latest > hourly_boundary:
                        # We have hourly data beyond the 30-day boundary
                        overlap_days = (latest - hourly_boundary).days
                        if overlap_days > 0:
                            analysis['overlap_zones'].append({
                                'zone': 'hourly_extension',
                                'timeframe': '1h',
                                'overlap_days': overlap_days,
                                'latest_hourly': latest,
                                'boundary': hourly_boundary
                            })
                
                else:
                    analysis['existing_coverage'][timeframe] = {
                        'count': 0,
                        'status': 'no_data'
                    }
            
            # Determine recommended strategy
            hourly_coverage = analysis['existing_coverage'].get('1h', {})
            daily_coverage = analysis['existing_coverage'].get('1d', {})
            
            has_recent_hourly = hourly_coverage.get('recent_zone_covered', False)
            has_historical_daily = daily_coverage.get('historical_zone_covered', False)
            gaps_exist = len(analysis['gaps_detected']) > 0
            overlaps_exist = len(analysis['overlap_zones']) > 0
            
            if not has_recent_hourly and not has_historical_daily:
                analysis['recommended_strategy'] = 'full_fetch'
            elif gaps_exist and overlaps_exist:
                analysis['recommended_strategy'] = 'smart_overlap_resolution'
            elif gaps_exist:
                analysis['recommended_strategy'] = 'incremental_update'
            elif overlaps_exist:
                analysis['recommended_strategy'] = 'overlap_consolidation'
            else:
                analysis['recommended_strategy'] = 'maintenance_update'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze existing data: {str(e)}")
            return {
                'error': str(e),
                'recommended_strategy': 'full_fetch'
            }

    async def _plan_coingecko_intervals_with_overlap(self, days_back: int, 
                                                   existing_analysis: Dict[str, Any],
                                                   update_mode: str) -> List[Dict[str, Any]]:
        """
        Plan CoinGecko intervals considering existing data and overlaps
        
        Args:
            days_back: Total days requested
            existing_analysis: Analysis of existing data
            update_mode: Update strategy mode
            
        Returns:
            Optimized interval plan considering overlaps
        """
        strategy = existing_analysis.get('recommended_strategy', 'full_fetch')
        plans = []
        
        now = datetime.utcnow()
        hourly_boundary = now - timedelta(days=30)
        
        if update_mode == 'force' or strategy == 'full_fetch':
            # Use original planning logic
            return self._plan_coingecko_intervals(days_back)
        
        elif strategy == 'smart_overlap_resolution':
            # Handle the complex scenario: existing hourly data + need for update
            hourly_coverage = existing_analysis['existing_coverage'].get('1h', {})
            
            if hourly_coverage.get('count', 0) > 0:
                latest_hourly = hourly_coverage.get('latest')
                
                # Calculate how much new hourly data we need
                hours_since_latest = (now - latest_hourly).total_seconds() / 3600 if latest_hourly else 24
                days_to_update = min(30, max(1, int(hours_since_latest / 24) + 1))
                
                plans.append({
                    'days': days_to_update,
                    'coingecko_interval': 'hourly',
                    'target_timeframe': '1h',
                    'period_name': 'incremental_hourly_update',
                    'update_type': 'merge_with_existing',
                    'overlap_handling': 'upsert_on_conflict'
                })
                
                # Check if we need historical daily data
                if days_back > 30:
                    daily_coverage = existing_analysis['existing_coverage'].get('1d', {})
                    
                    if daily_coverage.get('count', 0) == 0:
                        # Need to fetch historical daily data
                        plans.append({
                            'days': days_back - 30,
                            'coingecko_interval': 'daily',
                            'target_timeframe': '1d',
                            'period_name': 'historical_daily_backfill',
                            'update_type': 'new_data',
                            'start_days_ago': 30
                        })
        
        elif strategy == 'incremental_update':
            # Simple incremental update
            gaps = existing_analysis.get('gaps_detected', [])
            
            for gap in gaps:
                if gap['timeframe'] == '1h' and gap['needs_update']:
                    update_days = min(7, max(1, int(gap['gap_hours'] / 24) + 1))
                    
                    plans.append({
                        'days': update_days,
                        'coingecko_interval': 'hourly',
                        'target_timeframe': '1h',
                        'period_name': 'gap_fill_update',
                        'update_type': 'fill_gaps',
                        'gap_info': gap
                    })
        
        elif strategy == 'overlap_consolidation':
            # Handle overlaps where we have hourly data beyond 30 days
            overlaps = existing_analysis.get('overlap_zones', [])
            
            for overlap in overlaps:
                if overlap['zone'] == 'hourly_extension':
                    # We have hourly data beyond 30 days - consolidate with daily
                    overlap_days = overlap['overlap_days']
                    
                    plans.append({
                        'action': 'consolidate_overlap',
                        'overlap_days': overlap_days,
                        'source_timeframe': '1h',
                        'target_timeframe': '1d',
                        'period_name': 'hourly_to_daily_consolidation',
                        'consolidation_start': overlap['boundary'],
                        'consolidation_end': overlap['latest_hourly']
                    })
        
        # If no specific plans generated, fall back to maintenance update
        if not plans:
            plans.append({
                'days': min(7, days_back),
                'coingecko_interval': 'hourly',
                'target_timeframe': '1h',
                'period_name': 'maintenance_update',
                'update_type': 'refresh_recent'
            })
        
        return plans

    async def _handle_overlap_consolidation(self, asset_id: int, 
                                          consolidation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle consolidation of overlapping hourly data into daily timeframe
        
        This addresses the scenario where you fetched data a week ago (30+ days of hourly data)
        and now updating again, resulting in 37 days of hourly data when CoinGecko expects
        only 30 days hourly + 7 days daily.
        
        Args:
            asset_id: Asset to consolidate
            consolidation_config: Configuration for consolidation
            
        Returns:
            Consolidation results
        """
        try:
            source_tf = consolidation_config['source_timeframe']  # '1h'
            target_tf = consolidation_config['target_timeframe']  # '1d'
            start_date = consolidation_config['consolidation_start']
            end_date = consolidation_config['consolidation_end']
            
            logger.info(f"Consolidating {source_tf} to {target_tf} for asset {asset_id} "
                       f"from {start_date} to {end_date}")
            
            # Get hourly data in the overlap zone
            overlap_data = self.price_repo.db.query(self.price_repo.model).filter(
                self.price_repo.model.asset_id == asset_id,
                self.price_repo.model.timeframe == source_tf,
                self.price_repo.model.candle_time >= start_date,
                self.price_repo.model.candle_time <= end_date
            ).order_by(self.price_repo.model.candle_time.asc()).all()
            
            if not overlap_data:
                return {
                    'status': 'no_data_to_consolidate',
                    'message': 'No overlapping data found'
                }
            
            # Aggregate hourly data to daily
            daily_aggregates = {}
            
            for record in overlap_data:
                # Group by day
                day_key = record.candle_time.date()
                
                if day_key not in daily_aggregates:
                    daily_aggregates[day_key] = {
                        'records': [],
                        'day_start': datetime.combine(day_key, datetime.min.time())
                    }
                
                daily_aggregates[day_key]['records'].append(record)
            
            # Create daily records from hourly aggregates
            consolidated_records = []
            for day_key, day_data in daily_aggregates.items():
                records = day_data['records']
                
                # Calculate OHLCV for the day
                day_record = {
                    'asset_id': asset_id,
                    'timeframe': target_tf,
                    'candle_time': day_data['day_start'],
                    'open_price': records[0].open_price,  # First record of day
                    'high_price': max(r.high_price for r in records),
                    'low_price': min(r.low_price for r in records),
                    'close_price': records[-1].close_price,  # Last record of day
                    'volume': sum(r.volume for r in records),
                    'market_cap': sum(r.market_cap for r in records if r.market_cap) / len([r for r in records if r.market_cap]) if any(r.market_cap for r in records) else None,
                    'trade_count': sum(r.trade_count for r in records if r.trade_count),
                    'vwap': sum(r.close_price * r.volume for r in records) / sum(r.volume for r in records) if sum(r.volume for r in records) > 0 else records[0].close_price,
                    'is_validated': True
                }
                
                consolidated_records.append(day_record)
            
            # Store daily records
            stored_count = 0
            for record in consolidated_records:
                # Check for existing daily record
                existing = self.price_repo.db.query(self.price_repo.model).filter(
                    self.price_repo.model.asset_id == record['asset_id'],
                    self.price_repo.model.timeframe == record['timeframe'],
                    self.price_repo.model.candle_time == record['candle_time']
                ).first()
                
                if not existing:
                    new_record = self.price_repo.model(**record)
                    self.price_repo.db.add(new_record)
                    stored_count += 1
                else:
                    # Update existing
                    for key, value in record.items():
                        if key not in ['asset_id', 'timeframe', 'candle_time']:
                            setattr(existing, key, value)
            
            # Remove the overlapping hourly records
            deleted_count = self.price_repo.db.query(self.price_repo.model).filter(
                self.price_repo.model.asset_id == asset_id,
                self.price_repo.model.timeframe == source_tf,
                self.price_repo.model.candle_time >= start_date,
                self.price_repo.model.candle_time <= end_date
            ).delete()
            
            self.price_repo.db.commit()
            
            return {
                'status': 'success',
                'consolidation_period': f"{start_date.date()} to {end_date.date()}",
                'hourly_records_processed': len(overlap_data),
                'daily_records_created': stored_count,
                'hourly_records_removed': deleted_count,
                'storage_optimization': f"{deleted_count - stored_count} records saved"
            }
            
        except Exception as e:
            self.price_repo.db.rollback()
            logger.error(f"Overlap consolidation failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
# Usage examples for mixed interval CoinGecko data:
"""
# Initialize service
aggregation_service = TimeframeAggregationService(db_session)

# 1. Handle mixed interval data for a single asset
result = await aggregation_service.handle_mixed_interval_coingecko_data(
    asset_id=1,
    coingecko_id='bitcoin',
    days_back=90  # This will use both hourly and daily intervals
)

# 2. Batch process multiple assets with mixed intervals
coingecko_mappings = [
    {'asset_id': 1, 'coingecko_id': 'bitcoin'},
    {'asset_id': 2, 'coingecko_id': 'ethereum'},
    {'asset_id': 3, 'coingecko_id': 'cardano'}
]

batch_result = await aggregation_service.batch_process_mixed_interval_data(
    coingecko_mappings=coingecko_mappings,
    days_back=60,
    max_concurrent=3
)

# 3. Get strategy recommendation
strategy = aggregation_service.get_coingecko_data_strategy_recommendation(days_back=180)
print(f"Recommended approach: {strategy['recommended_approach']}")
print(f"API calls needed: {strategy['api_calls_needed']}")
print(f"Expected records: {strategy['storage_estimation']['total_estimated_records']}")

# 4. Complete workflow for handling CoinGecko mixed intervals
async def complete_coingecko_aggregation_workflow():
    # Step 1: Get strategy recommendation
    strategy = aggregation_service.get_coingecko_data_strategy_recommendation(days_back=90)
    
    # Step 2: Process mixed interval data
    result = await aggregation_service.handle_mixed_interval_coingecko_data(
        asset_id=1,
        coingecko_id='bitcoin',
        days_back=90
    )
    
    # Step 3: Check data quality
    quality = result.get('data_quality', {})
    print(f"Data quality grade: {quality.get('overall_grade', 'N/A')}")
    
    # Step 4: Run additional aggregation if needed
    if quality.get('overall_coverage_percentage', 0) >= 80:
        aggregation_result = aggregation_service.auto_aggregate_for_asset(
            asset_id=1,
            source_timeframe='1h'
        )
        print(f"Additional aggregation completed: {aggregation_result}")

# Example of handling CoinGecko's specific interval behavior:
# - Days 1: 5-minute data → aggregate to 1h
# - Days 2-30: hourly data → use directly + aggregate to 4h, 1d
# - Days 31+: daily data → use directly + aggregate to 1w, 1M

# The service automatically handles:
# ✅ Mixed interval detection and processing
# ✅ Optimal API call planning
# ✅ Rate limit management
# ✅ Data quality assessment
# ✅ Automatic aggregation to higher timeframes
# ✅ Batch processing for multiple assets
"""