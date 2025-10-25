# backend/app/services/data_quality_service.py
# Service for data quality assessment and monitoring

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from ..repositories.asset.price_data_repository import PriceDataRepository
from ..repositories.asset.asset_repository import AssetRepository

logger = logging.getLogger(__name__)


class DataQualityService:
    """
    Service for managing data quality assessment and monitoring
    
    This service provides methods for:
    - Health reporting and monitoring
    - Data quality assessment
    - Coverage analysis
    - Data integrity checks
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.price_repo = PriceDataRepository(db)
        self.asset_repo = AssetRepository(db)
    
    def get_aggregation_health_report(self, asset_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate health report for timeframe aggregation status
        
        Args:
            asset_id: Specific asset to check (None for all assets)
            
        Returns:
            Health report with recommendations
        """
        if asset_id:
            assets_to_check = [self.asset_repo.get(asset_id)]
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
            
            def safe_count_check(tf_dict, timeframes):
                for tf in timeframes:
                    tf_data = tf_dict.get(tf, {})
                    count = tf_data.get('count', 0)
                    try:
                        count_int = int(count) if count is not None else 0
                        if count_int > 0:
                            return True
                    except (ValueError, TypeError):
                        continue
                return False
            
            has_base_data = safe_count_check(status, base_timeframes)
            has_aggregated_data = safe_count_check(status, higher_timeframes)
            
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

    def assess_mixed_data_quality(self, asset_id: int, days_back: int) -> Dict[str, Any]:
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
                count_raw = tf_status.get('count', 0)
                try:
                    count = int(count_raw) if count_raw is not None else 0
                except (ValueError, TypeError):
                    count = 0
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

    def get_data_completeness_report(self, asset_id: int, timeframe: str = '1d', days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive data completeness report for an asset
        
        Args:
            asset_id: Asset ID to analyze
            timeframe: Primary timeframe to analyze
            days: Number of days to analyze
            
        Returns:
            Detailed completeness report
        """
        try:
            # Get basic aggregation status
            status = self.price_repo.get_aggregation_status(asset_id)
            
            # Get asset info
            asset = self.asset_repo.get(asset_id)
            if not asset:
                return {'error': f'Asset {asset_id} not found'}
            
            # Calculate expected vs actual records
            tf_status = status.get(timeframe, {})
            actual_count_raw = tf_status.get('count', 0)
            try:
                actual_count = int(actual_count_raw) if actual_count_raw is not None else 0
            except (ValueError, TypeError):
                actual_count = 0
            latest_time_str = tf_status.get('latest_time')
            earliest_time_str = tf_status.get('earliest_time')
            
            # Calculate expected record count based on timeframe
            if timeframe == '1h':
                expected_count = days * 24
            elif timeframe == '4h':
                expected_count = days * 6
            elif timeframe == '1d':
                expected_count = days
            elif timeframe == '1w':
                expected_count = max(1, days // 7)
            elif timeframe == '1M':
                expected_count = max(1, days // 30)
            else:
                expected_count = days  # Default to daily
            
            completeness_pct = (actual_count / expected_count * 100) if expected_count > 0 else 0
            
            # Analyze data gaps
            gaps_info = []
            if latest_time_str and earliest_time_str:
                latest_time = datetime.fromisoformat(latest_time_str.replace('Z', '+00:00'))
                earliest_time = datetime.fromisoformat(earliest_time_str.replace('Z', '+00:00'))
                
                # Check for recent data gaps
                now = datetime.utcnow()
                time_since_latest = now - latest_time
                
                if time_since_latest > timedelta(hours=2):  # More than 2 hours old
                    gaps_info.append({
                        'type': 'recent_gap',
                        'description': f'Latest data is {time_since_latest.days} days, {time_since_latest.seconds // 3600} hours old',
                        'severity': 'high' if time_since_latest.days > 1 else 'medium'
                    })
                
                # Check for data range coverage
                data_span_days = (latest_time - earliest_time).days
                if data_span_days < days * 0.8:  # Less than 80% coverage
                    gaps_info.append({
                        'type': 'coverage_gap',
                        'description': f'Data only covers {data_span_days} days out of {days} requested',
                        'severity': 'medium'
                    })
            
            # Calculate quality score
            quality_score = min(100, completeness_pct)
            if gaps_info:
                # Reduce score based on gap severity
                high_severity_gaps = sum(1 for gap in gaps_info if gap['severity'] == 'high')
                medium_severity_gaps = sum(1 for gap in gaps_info if gap['severity'] == 'medium')
                quality_score -= (high_severity_gaps * 20 + medium_severity_gaps * 10)
                quality_score = max(0, quality_score)
            
            return {
                'asset_id': asset_id,
                'symbol': asset.symbol,
                'timeframe': timeframe,
                'analysis_period_days': days,
                'completeness': {
                    'actual_records': actual_count,
                    'expected_records': expected_count,
                    'completeness_percentage': round(completeness_pct, 1),
                    'latest_data': latest_time_str,
                    'earliest_data': earliest_time_str
                },
                'gaps_analysis': gaps_info,
                'quality_score': round(quality_score, 1),
                'quality_grade': 'A' if quality_score >= 90 else 'B' if quality_score >= 80 else 'C' if quality_score >= 70 else 'D' if quality_score >= 60 else 'F',
                'recommendations': self._generate_quality_recommendations(quality_score, gaps_info, completeness_pct)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate completeness report for asset {asset_id}: {str(e)}")
            return {
                'error': f'Completeness analysis failed: {str(e)}',
                'asset_id': asset_id
            }

    def get_system_wide_quality_summary(self, asset_type: str = 'crypto') -> Dict[str, Any]:
        """
        Generate system-wide data quality summary
        
        Args:
            asset_type: Type of assets to analyze
            
        Returns:
            System-wide quality summary
        """
        try:
            # Get all active assets
            assets = self.asset_repo.get_by_filters(
                filters={'asset_type': asset_type, 'is_active': True}
            )
            
            if not assets:
                return {'error': 'No assets found for quality analysis'}
            
            summary_stats = {
                'total_assets': len(assets),
                'assets_analyzed': 0,
                'quality_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0},
                'average_quality_score': 0,
                'assets_needing_attention': [],
                'timeframe_coverage': {},
                'critical_issues': [],
                'recommendations': []
            }
            
            total_quality_score = 0
            quality_scores = []
            
            for asset in assets:
                try:
                    # Get basic health data for this asset
                    health_report = self.get_aggregation_health_report(asset.id)
                    asset_health = health_report.get('detailed_health_data', {}).get(asset.id, {})
                    
                    if asset_health:
                        summary_stats['assets_analyzed'] += 1
                        quality_score = asset_health.get('health_score', 0)
                        quality_scores.append(quality_score)
                        total_quality_score += quality_score
                        
                        # Categorize quality
                        if quality_score >= 90:
                            summary_stats['quality_distribution']['A'] += 1
                        elif quality_score >= 80:
                            summary_stats['quality_distribution']['B'] += 1
                        elif quality_score >= 70:
                            summary_stats['quality_distribution']['C'] += 1
                        elif quality_score >= 60:
                            summary_stats['quality_distribution']['D'] += 1
                        else:
                            summary_stats['quality_distribution']['F'] += 1
                        
                        # Track assets needing attention
                        if quality_score < 80:
                            summary_stats['assets_needing_attention'].append({
                                'asset_id': asset.id,
                                'symbol': asset.symbol,
                                'quality_score': quality_score,
                                'issues': asset_health.get('issues', [])
                            })
                        
                        # Track critical issues
                        issues = asset_health.get('issues', [])
                        for issue in issues:
                            if 'No base timeframe data' in issue:
                                summary_stats['critical_issues'].append({
                                    'type': 'no_base_data',
                                    'asset': asset.symbol,
                                    'description': issue
                                })
                
                except Exception as e:
                    logger.warning(f"Failed to analyze asset {asset.id}: {str(e)}")
                    continue
            
            # Calculate averages and generate recommendations
            if summary_stats['assets_analyzed'] > 0:
                summary_stats['average_quality_score'] = round(total_quality_score / summary_stats['assets_analyzed'], 1)
                
                # Generate system-wide recommendations
                if len(summary_stats['assets_needing_attention']) > len(assets) * 0.2:  # More than 20% need attention
                    summary_stats['recommendations'].append('Consider system-wide data refresh - many assets need attention')
                
                if summary_stats['critical_issues']:
                    summary_stats['recommendations'].append(f'Address {len(summary_stats["critical_issues"])} critical data issues immediately')
                
                if summary_stats['average_quality_score'] < 70:
                    summary_stats['recommendations'].append('System-wide data quality is below acceptable levels - investigate infrastructure')
            
            return summary_stats
            
        except Exception as e:
            logger.error(f"Failed to generate system-wide quality summary: {str(e)}")
            return {
                'error': f'System quality analysis failed: {str(e)}'
            }

    def _generate_quality_recommendations(self, quality_score: float, gaps_info: List[Dict], completeness_pct: float) -> List[str]:
        """
        Generate recommendations based on quality analysis
        
        Args:
            quality_score: Overall quality score
            gaps_info: List of detected gaps
            completeness_pct: Data completeness percentage
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if quality_score < 60:
            recommendations.append('URGENT: Data quality is critically low - immediate attention required')
        elif quality_score < 80:
            recommendations.append('Data quality needs improvement - schedule maintenance')
        
        if completeness_pct < 50:
            recommendations.append('Significant data gaps detected - consider full data resync')
        elif completeness_pct < 80:
            recommendations.append('Some data gaps present - incremental data update recommended')
        
        for gap in gaps_info:
            if gap['type'] == 'recent_gap' and gap['severity'] == 'high':
                recommendations.append('Recent data is outdated - schedule immediate data update')
            elif gap['type'] == 'coverage_gap':
                recommendations.append('Historical data coverage is incomplete - consider backfill operation')
        
        if not recommendations:
            recommendations.append('Data quality is good - continue regular monitoring')
        
        return recommendations


# Global service instance factory
def get_data_quality_service(db: Session) -> DataQualityService:
    """Factory function to create DataQualityService instance"""
    return DataQualityService(db)