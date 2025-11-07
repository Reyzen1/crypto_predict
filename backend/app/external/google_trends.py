# File: ./backend/app/external/google_trends.py
# Safe Google Trends API client using pytrends

import asyncio
import random
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import pandas as pd

from app.core.rate_limiter import rate_limiter
from app.core.config import settings

logger = logging.getLogger(__name__)

# Import pytrends with fallback
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    logger.warning("pytrends not installed. Install with: pip install pytrends")


class GoogleTrendsAPIError(Exception):
    """Custom exception for Google Trends API errors"""
    pass


class GoogleTrendsRateLimitError(GoogleTrendsAPIError):
    """Exception for rate limit errors"""
    pass


class GoogleTrendsBlockedError(GoogleTrendsAPIError):
    """Exception for IP blocking"""
    pass


class SafeGoogleTrendsClient:
    """
    Safe Google Trends client with advanced protection against IP blocking
    
    Features:
    - Smart rate limiting with randomization
    - User Agent rotation
    - Circuit breaker pattern
    - Session management
    - Exponential backoff
    - Request monitoring and logging
    
    Protection Strategies:
    - Conservative request limits (50 per day)
    - Random delays between requests (15-45 seconds)
    - Session rotation every 10 requests
    - User Agent rotation
    - Circuit breaker on failures
    - Graceful degradation
    """
    
    def __init__(self):
        if not PYTRENDS_AVAILABLE:
            raise GoogleTrendsAPIError("pytrends library is not installed")
        
        # Session management
        self.current_session = None
        self.session_request_count = 0
        self.session_limit = 10  # Max requests per session
        
        # Rate limiting
        self.last_request_time = 0
        self.daily_request_count = 0
        self.daily_limit = 50  # Conservative daily limit
        self.min_delay = 15     # Minimum 15 seconds between requests
        self.max_delay = 45     # Maximum 45 seconds
        
        # Circuit breaker
        self.failure_count = 0
        self.max_failures = 3
        self.cooldown_period = 1800  # 30 minutes cooldown
        self.last_failure_time = 0
        self.circuit_state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        
        # User Agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        self.current_user_agent_index = 0
        
        # Request monitoring
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_success_time = 0
    
    def _check_circuit_breaker(self):
        """Check circuit breaker state"""
        current_time = time.time()
        
        if self.circuit_state == 'OPEN':
            # Check if cooldown period has passed
            if current_time - self.last_failure_time > self.cooldown_period:
                self.circuit_state = 'HALF_OPEN'
                logger.info("Circuit breaker moving to HALF_OPEN state")
            else:
                remaining_cooldown = self.cooldown_period - (current_time - self.last_failure_time)
                raise GoogleTrendsBlockedError(
                    f"Circuit breaker OPEN. Cooldown for {remaining_cooldown:.0f} more seconds"
                )
        
        # Check if we've hit failure threshold
        if self.failure_count >= self.max_failures:
            self.circuit_state = 'OPEN'
            self.last_failure_time = current_time
            raise GoogleTrendsBlockedError("Too many failures. Circuit breaker activated")
    
    def _check_rate_limits(self):
        """Check various rate limits"""
        # Daily limit check
        if self.daily_request_count >= self.daily_limit:
            raise GoogleTrendsRateLimitError("Daily request limit exceeded")
        
        # Session limit check
        if self.session_request_count >= self.session_limit:
            logger.info("Session limit reached, will create new session")
            self._invalidate_session()
        
        # Time since last request check
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            wait_needed = self.min_delay - time_since_last
            raise GoogleTrendsRateLimitError(f"Too soon. Wait {wait_needed:.1f} more seconds")
    
    def _create_new_session(self):
        """Create new session with rotated User Agent"""
        try:
            # Rotate User Agent
            user_agent = self.user_agents[self.current_user_agent_index]
            self.current_user_agent_index = (self.current_user_agent_index + 1) % len(self.user_agents)
            
            # Create new pytrends session
            self.current_session = TrendReq(
                hl='en-US',
                tz=360,
                timeout=(10, 25),
                retries=1,
                backoff_factor=0.5,
                requests_args={'verify': True}
            )
            
            # Set custom User Agent
            if hasattr(self.current_session, 'session'):
                self.current_session.session.headers.update({
                    'User-Agent': user_agent
                })
            
            self.session_request_count = 0
            logger.info(f"New Google Trends session created with UA: {user_agent[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to create new session: {e}")
            self.current_session = None
            raise GoogleTrendsAPIError(f"Session creation failed: {e}")
    
    def _invalidate_session(self):
        """Invalidate current session"""
        self.current_session = None
        self.session_request_count = 0
    
    async def _smart_delay(self):
        """Apply smart delay with randomization"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # Calculate base delay needed
        if elapsed < self.min_delay:
            base_wait = self.min_delay - elapsed
        else:
            base_wait = 0
        
        # Add random component for human-like behavior
        random_delay = random.uniform(5, 20)
        
        # Add extra delay based on recent failures
        failure_penalty = self.failure_count * 10
        
        total_wait = base_wait + random_delay + failure_penalty
        
        if total_wait > 0:
            logger.debug(f"Smart delay: {total_wait:.1f}s (base: {base_wait:.1f}, random: {random_delay:.1f}, penalty: {failure_penalty:.1f})")
            await asyncio.sleep(total_wait)
        
        self.last_request_time = time.time()
    
    async def get_crypto_trends_365_days(self, 
                                        keywords: List[str] = ['bitcoin', 'cryptocurrency'],
                                        max_retries: int = 3) -> Dict[str, Any]:
        """
        Get Google Trends data for crypto keywords over 365 days with maximum safety
        
        Args:
            keywords: List of search terms (max 5 keywords)
            max_retries: Maximum retry attempts
            
        Returns:
            Dict with trends data or error information
            
        Example:
            client = SafeGoogleTrendsClient()
            data = await client.get_crypto_trends_365_days(['bitcoin', 'ethereum'])
        """
        # Input validation
        if not keywords or len(keywords) > 5:
            raise ValueError("Keywords must be provided and max 5 items")
        
        # Pre-flight checks
        self._check_circuit_breaker()
        self._check_rate_limits()
        
        # Ensure we have a session
        if self.current_session is None:
            self._create_new_session()
        
        for attempt in range(max_retries):
            try:
                # Apply smart delay
                await self._smart_delay()
                
                logger.info(f"Requesting Google Trends data (attempt {attempt + 1}/{max_retries})")
                logger.debug(f"Keywords: {keywords}, Session requests: {self.session_request_count}")
                
                # Make the actual request in executor to avoid blocking
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._build_payload_sync,
                    keywords
                )
                
                # Get interest over time data
                interest_data = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._get_interest_over_time_sync
                )
                
                # Get related queries
                related_queries = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._get_related_queries_sync
                )
                
                # Update counters on success
                self.total_requests += 1
                self.successful_requests += 1
                self.daily_request_count += 1
                self.session_request_count += 1
                self.last_success_time = time.time()
                
                # Reset failure count on success
                if self.circuit_state == 'HALF_OPEN':
                    self.circuit_state = 'CLOSED'
                    self.failure_count = 0
                    logger.info("Circuit breaker reset to CLOSED")
                elif self.failure_count > 0:
                    self.failure_count = max(0, self.failure_count - 1)
                
                # Process and return data
                result = self._process_trends_data(interest_data, related_queries, keywords)
                
                logger.info(f"Successfully retrieved Google Trends data: {result.get('data_points', 0)} records")
                return result
                
            except Exception as e:
                self.total_requests += 1
                self.failed_requests += 1
                self.failure_count += 1
                
                error_msg = str(e).lower()
                
                # Detect different types of errors
                if 'too many requests' in error_msg or '429' in error_msg:
                    error_type = "Rate Limit"
                    self.failure_count += 2  # Penalize rate limit errors more
                elif 'blocked' in error_msg or 'forbidden' in error_msg or '403' in error_msg:
                    error_type = "IP Blocked"
                    self.failure_count += 3  # Penalize blocks heavily
                elif 'timeout' in error_msg or 'connection' in error_msg:
                    error_type = "Network Error"
                else:
                    error_type = "Unknown Error"
                
                logger.warning(f"Attempt {attempt + 1} failed ({error_type}): {e}")
                
                # Handle different error types
                if error_type == "IP Blocked":
                    self.circuit_state = 'OPEN'
                    self.last_failure_time = time.time()
                    return {
                        'error': 'IP appears to be blocked by Google',
                        'error_type': 'ip_blocked',
                        'success': False,
                        'keywords': keywords,
                        'retry_after': self.cooldown_period,
                        'last_updated': datetime.now().isoformat()
                    }
                
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    backoff_delay = (2 ** attempt) * 60 + random.uniform(30, 120)
                    logger.info(f"Backing off for {backoff_delay:.1f} seconds")
                    await asyncio.sleep(backoff_delay)
                    
                    # Create new session after failure
                    self._invalidate_session()
                    self._create_new_session()
                else:
                    # Final failure
                    return {
                        'error': f'All attempts failed. Last error: {e}',
                        'error_type': error_type.lower().replace(' ', '_'),
                        'success': False,
                        'keywords': keywords,
                        'attempts': max_retries,
                        'last_updated': datetime.now().isoformat()
                    }
        
        return {'error': 'Unexpected end of retry loop', 'success': False}
    
    def _build_payload_sync(self, keywords: List[str]):
        """Synchronous wrapper for build_payload"""
        self.current_session.build_payload(
            kw_list=keywords,
            cat=0,
            timeframe='today 12-m',  # 12 months = ~365 days
            geo='',
            gprop=''
        )
    
    def _get_interest_over_time_sync(self) -> pd.DataFrame:
        """Synchronous wrapper for interest_over_time"""
        return self.current_session.interest_over_time()
    
    def _get_related_queries_sync(self) -> Dict:
        """Synchronous wrapper for related_queries"""
        try:
            return self.current_session.related_queries()
        except Exception as e:
            logger.warning(f"Failed to get related queries: {e}")
            return {}
    
    def _process_trends_data(self, 
                           interest_data: pd.DataFrame, 
                           related_queries: Dict, 
                           keywords: List[str]) -> Dict[str, Any]:
        """Process raw trends data into standardized format"""
        try:
            # Convert interest data to dict
            if not interest_data.empty:
                # Remove 'isPartial' column if it exists
                if 'isPartial' in interest_data.columns:
                    interest_data = interest_data.drop('isPartial', axis=1)
                
                interest_dict = interest_data.to_dict()
                data_points = len(interest_data)
                
                # Get date range
                start_date = interest_data.index[0].isoformat() if len(interest_data) > 0 else None
                end_date = interest_data.index[-1].isoformat() if len(interest_data) > 0 else None
            else:
                interest_dict = {}
                data_points = 0
                start_date = None
                end_date = None
            
            # Process related queries
            processed_related = {}
            for keyword, queries in related_queries.items():
                if isinstance(queries, dict):
                    processed_related[keyword] = {
                        'top': queries.get('top', []).head(10).to_dict() if hasattr(queries.get('top', []), 'head') else [],
                        'rising': queries.get('rising', []).head(10).to_dict() if hasattr(queries.get('rising', []), 'head') else []
                    }
            
            return {
                'interest_over_time': interest_dict,
                'related_queries': processed_related,
                'keywords': keywords,
                'timeframe': 'today 12-m',
                'data_points': data_points,
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'success': True,
                'last_updated': datetime.now().isoformat(),
                'session_stats': {
                    'total_requests': self.total_requests,
                    'successful_requests': self.successful_requests,
                    'failed_requests': self.failed_requests,
                    'success_rate': round((self.successful_requests / max(self.total_requests, 1)) * 100, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing trends data: {e}")
            return {
                'error': f'Data processing failed: {e}',
                'success': False,
                'keywords': keywords,
                'last_updated': datetime.now().isoformat()
            }
    
    async def get_crypto_sentiment_from_trends(self, 
                                             keywords: List[str] = ['bitcoin', 'cryptocurrency']) -> Dict[str, Any]:
        """
        Calculate crypto market sentiment from Google Trends data
        
        Args:
            keywords: List of crypto-related search terms
            
        Returns:
            Dict with sentiment analysis
        """
        trends_data = await self.get_crypto_trends_365_days(keywords)
        
        if not trends_data.get('success'):
            return {
                'error': trends_data.get('error', 'Unknown error'),
                'success': False,
                'keywords': keywords
            }
        
        try:
            interest_data = trends_data.get('interest_over_time', {})
            
            if not interest_data:
                return {
                    'error': 'No trends data available for sentiment analysis',
                    'success': False,
                    'keywords': keywords
                }
            
            # Calculate sentiment for primary keyword
            primary_keyword = keywords[0]
            if primary_keyword not in interest_data:
                return {
                    'error': f'No data available for primary keyword: {primary_keyword}',
                    'success': False,
                    'keywords': keywords
                }
            
            # Get values and clean them
            values = list(interest_data[primary_keyword].values())
            values = [v for v in values if v is not None and isinstance(v, (int, float)) and v > 0]
            
            if not values or len(values) < 10:
                return {
                    'error': 'Insufficient valid data points for sentiment analysis',
                    'success': False,
                    'keywords': keywords
                }
            
            # Calculate sentiment metrics
            current_value = values[-1]
            recent_avg = sum(values[-7:]) / len(values[-7:])  # Last 7 data points
            overall_avg = sum(values) / len(values)
            max_value = max(values)
            min_value = min(values)
            
            # Normalize current value (0-100 scale)
            if max_value > min_value:
                normalized_current = ((current_value - min_value) / (max_value - min_value)) * 100
            else:
                normalized_current = 50  # Neutral if no variation
            
            # Calculate trend direction
            if len(values) >= 14:
                recent_trend = sum(values[-7:]) / 7 - sum(values[-14:-7]) / 7
                trend_direction = 'increasing' if recent_trend > 0 else 'decreasing' if recent_trend < 0 else 'stable'
            else:
                trend_direction = 'stable'
            
            # Calculate sentiment score (0-100)
            sentiment_score = (
                normalized_current * 0.4 +  # Current position weight
                (recent_avg / overall_avg * 50) * 0.4 +  # Recent vs overall weight
                (50 + (recent_trend if 'recent_trend' in locals() else 0)) * 0.2  # Trend weight
            )
            sentiment_score = max(0, min(100, sentiment_score))
            
            return {
                'keyword': primary_keyword,
                'sentiment_score': round(sentiment_score, 1),
                'current_interest': current_value,
                'recent_average': round(recent_avg, 1),
                'overall_average': round(overall_avg, 1),
                'trend_direction': trend_direction,
                'interest_range': {
                    'min': min_value,
                    'max': max_value,
                    'current_percentile': round(normalized_current, 1)
                },
                'data_quality': {
                    'total_points': len(values),
                    'date_range': trends_data.get('date_range', {}),
                    'completeness': round((len(values) / 52) * 100, 1)  # Assuming weekly data for 12 months
                },
                'success': True,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating sentiment from trends: {e}")
            return {
                'error': f'Sentiment calculation failed: {e}',
                'success': False,
                'keywords': keywords
            }
    
    async def get_historical_google_trends_scores(self, 
                                                 keywords: List[str] = ['bitcoin'],
                                                 days: int = 365) -> Dict[str, Any]:
        """
        Get historical Google Trends sentiment scores for 365 days
        
        Args:
            keywords: List of crypto-related search terms
            days: Number of days to calculate scores for (max 365)
            
        Returns:
            Dict with historical sentiment scores for each day/week
            
        Example:
            scores = await client.get_historical_google_trends_scores(['bitcoin'])
            for record in scores['historical_scores']:
                print(f"{record['date']}: {record['google_trends_score']}")
        """
        if days > 365:
            days = 365
            logger.warning("Days limited to 365 for Google Trends historical data")
        
        # Get raw trends data
        trends_data = await self.get_crypto_trends_365_days(keywords)
        
        if not trends_data.get('success'):
            return {
                'error': trends_data.get('error', 'Failed to get trends data'),
                'success': False,
                'keywords': keywords
            }
        
        try:
            interest_data = trends_data.get('interest_over_time', {})
            primary_keyword = keywords[0]
            
            if primary_keyword not in interest_data:
                return {
                    'error': f'No data available for keyword: {primary_keyword}',
                    'success': False,
                    'keywords': keywords
                }
            
            # Get raw interest data with timestamps
            raw_data = interest_data[primary_keyword]
            
            if not raw_data:
                return {
                    'error': 'No interest data available',
                    'success': False,
                    'keywords': keywords
                }
            
            # Convert to list of (date, value) pairs and sort by date
            data_points = []
            for date_str, value in raw_data.items():
                if value is not None and isinstance(value, (int, float)) and value >= 0:
                    try:
                        # Parse date string to datetime
                        if isinstance(date_str, str):
                            if 'T' in date_str:
                                # ISO format
                                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            else:
                                # Try different date formats
                                try:
                                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                except ValueError:
                                    try:
                                        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                                    except ValueError:
                                        continue
                        else:
                            continue
                        
                        data_points.append((date_obj, value))
                    except Exception as e:
                        logger.warning(f"Failed to parse date {date_str}: {e}")
                        continue
            
            if not data_points:
                return {
                    'error': 'No valid data points found',
                    'success': False,
                    'keywords': keywords
                }
            
            # Sort by date
            data_points.sort(key=lambda x: x[0])
            
            # Calculate global statistics for normalization
            values = [point[1] for point in data_points]
            max_value = max(values)
            min_value = min(values)
            overall_avg = sum(values) / len(values)
            
            # Calculate historical sentiment scores
            historical_scores = []
            
            for i, (date_obj, current_value) in enumerate(data_points):
                try:
                    # Calculate rolling averages and trends
                    if i >= 6:  # Need at least 7 points for weekly average
                        recent_values = values[max(0, i-6):i+1]  # Last 7 points including current
                        recent_avg = sum(recent_values) / len(recent_values)
                    else:
                        recent_avg = current_value
                    
                    # Calculate trend (if enough data)
                    if i >= 13:  # Need at least 14 points for trend calculation
                        current_period = values[max(0, i-6):i+1]
                        previous_period = values[max(0, i-13):max(1, i-6)]
                        
                        current_period_avg = sum(current_period) / len(current_period)
                        previous_period_avg = sum(previous_period) / len(previous_period)
                        
                        trend_change = current_period_avg - previous_period_avg
                        trend_direction = 'increasing' if trend_change > 0 else 'decreasing' if trend_change < 0 else 'stable'
                    else:
                        trend_change = 0
                        trend_direction = 'stable'
                    
                    # Normalize current value (0-100 scale)
                    if max_value > min_value:
                        normalized_current = ((current_value - min_value) / (max_value - min_value)) * 100
                    else:
                        normalized_current = 50
                    
                    # Calculate sentiment score for this point
                    sentiment_score = (
                        normalized_current * 0.4 +  # Current position weight
                        (recent_avg / overall_avg * 50) * 0.4 +  # Recent vs overall weight
                        (50 + min(max(trend_change, -10), 10)) * 0.2  # Trend weight (clamped)
                    )
                    sentiment_score = max(0, min(100, sentiment_score))
                    
                    # Create historical record
                    historical_record = {
                        'date': date_obj.strftime('%Y-%m-%d'),
                        'timestamp': date_obj.isoformat(),
                        'google_trends_score': round(sentiment_score, 1),
                        'raw_interest_value': current_value,
                        'normalized_value': round(normalized_current, 1),
                        'recent_average': round(recent_avg, 1),
                        'trend_direction': trend_direction,
                        'trend_change': round(trend_change, 2) if abs(trend_change) > 0.01 else 0
                    }
                    
                    historical_scores.append(historical_record)
                    
                except Exception as e:
                    logger.warning(f"Error calculating score for date {date_obj}: {e}")
                    continue
            
            # Limit to requested days (from most recent)
            if len(historical_scores) > days:
                historical_scores = historical_scores[-days:]
            
            # Calculate summary statistics
            if historical_scores:
                scores = [record['google_trends_score'] for record in historical_scores]
                summary_stats = {
                    'total_records': len(historical_scores),
                    'date_range': {
                        'start': historical_scores[0]['date'],
                        'end': historical_scores[-1]['date']
                    },
                    'score_statistics': {
                        'current': scores[-1],
                        'average': round(sum(scores) / len(scores), 1),
                        'min': min(scores),
                        'max': max(scores),
                        'volatility': round(
                            (sum((score - sum(scores)/len(scores))**2 for score in scores) / len(scores))**0.5, 1
                        )
                    },
                    'data_quality': {
                        'completeness': round((len(historical_scores) / min(days, 52)) * 100, 1),
                        'coverage_days': len(historical_scores)
                    }
                }
            else:
                summary_stats = {
                    'total_records': 0,
                    'error': 'No valid historical scores calculated'
                }
            
            return {
                'historical_scores': historical_scores,
                'summary_statistics': summary_stats,
                'keywords': keywords,
                'primary_keyword': primary_keyword,
                'success': True,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating historical Google Trends scores: {e}")
            return {
                'error': f'Historical calculation failed: {e}',
                'success': False,
                'keywords': keywords
            }
    
    async def get_trending_crypto_keywords(self) -> Dict[str, Any]:
        """
        Get currently trending crypto-related keywords (if available)
        
        Returns:
            Dict with trending keywords or error
        """
        try:
            if self.current_session is None:
                self._create_new_session()
            
            await self._smart_delay()
            
            # Get trending searches for US
            trending = await asyncio.get_event_loop().run_in_executor(
                None,
                self.current_session.trending_searches,
                'united_states'
            )
            
            # Filter for crypto-related terms
            crypto_keywords = ['bitcoin', 'crypto', 'ethereum', 'blockchain', 'nft', 'defi', 'trading']
            trending_crypto = []
            
            if not trending.empty:
                trending_list = trending[0].tolist()
                for term in trending_list[:20]:  # Check top 20
                    term_lower = term.lower()
                    if any(keyword in term_lower for keyword in crypto_keywords):
                        trending_crypto.append(term)
            
            return {
                'trending_crypto_keywords': trending_crypto[:10],  # Return top 10
                'total_trending': len(trending) if not trending.empty else 0,
                'crypto_percentage': round((len(trending_crypto) / max(len(trending), 1)) * 100, 1) if not trending.empty else 0,
                'success': True,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Failed to get trending keywords: {e}")
            return {
                'error': f'Failed to get trending keywords: {e}',
                'success': False,
                'last_updated': datetime.now().isoformat()
            }
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get client statistics and health"""
        current_time = time.time()
        
        return {
            'session_stats': {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': round((self.successful_requests / max(self.total_requests, 1)) * 100, 1),
                'daily_requests': self.daily_request_count,
                'daily_limit': self.daily_limit,
                'session_requests': self.session_request_count,
                'session_limit': self.session_limit
            },
            'rate_limiting': {
                'last_request_ago': round(current_time - self.last_request_time, 1) if self.last_request_time > 0 else None,
                'min_delay': self.min_delay,
                'max_delay': self.max_delay,
                'ready_to_request': (current_time - self.last_request_time) >= self.min_delay
            },
            'circuit_breaker': {
                'state': self.circuit_state,
                'failure_count': self.failure_count,
                'max_failures': self.max_failures,
                'cooldown_remaining': max(0, self.cooldown_period - (current_time - self.last_failure_time)) if self.last_failure_time > 0 else 0
            },
            'health': {
                'pytrends_available': PYTRENDS_AVAILABLE,
                'session_active': self.current_session is not None,
                'last_success_ago': round(current_time - self.last_success_time, 1) if self.last_success_time > 0 else None,
                'overall_health': 'healthy' if self.circuit_state == 'CLOSED' and self.failure_count < 2 else 'degraded' if self.circuit_state != 'OPEN' else 'unhealthy'
            }
        }
    
    async def get_historical_trends_score(self, 
                                         keywords: List[str] = ['bitcoin'],
                                         max_retries: int = 3) -> Dict[str, Any]:
        """
        Get historical Google Trends sentiment scores for 365 days
        
        Args:
            keywords: List of crypto keywords to analyze
            max_retries: Maximum retry attempts
            
        Returns:
            Dict with daily sentiment scores for 365 days
            
        Example:
            client = SafeGoogleTrendsClient()
            historical = await client.get_historical_trends_score(['bitcoin'])
            
            # Returns:
            {
                'historical_scores': [
                    {
                        'date': '2024-11-07',
                        'google_trends_score': 67.3,
                        'interest_value': 85,
                        'normalized_score': 0.673
                    },
                    # ... 365 days of data
                ],
                'summary': {
                    'avg_score': 58.2,
                    'max_score': 89.5,
                    'min_score': 23.1,
                    'volatility': 15.8
                },
                'success': True
            }
        """
        # Get the raw trends data first
        trends_data = await self.get_crypto_trends_365_days(keywords, max_retries)
        
        if not trends_data.get('success'):
            return {
                'error': trends_data.get('error', 'Failed to get trends data'),
                'success': False,
                'keywords': keywords
            }
        
        try:
            # Extract interest data
            interest_data = trends_data.get('interest_over_time', {})
            primary_keyword = keywords[0]
            
            if primary_keyword not in interest_data:
                return {
                    'error': f'No data found for primary keyword: {primary_keyword}',
                    'success': False,
                    'keywords': keywords
                }
            
            # Get the raw values and dates
            raw_values = interest_data[primary_keyword]
            
            if not raw_values:
                return {
                    'error': 'No trend values found',
                    'success': False,
                    'keywords': keywords
                }
            
            # Process data to create daily scores
            historical_scores = []
            values_list = []
            
            # Convert data to list format for processing
            for date_str, value in raw_values.items():
                if value is not None and isinstance(value, (int, float)) and value > 0:
                    values_list.append({
                        'date': date_str,
                        'value': value
                    })
            
            # Sort by date
            values_list.sort(key=lambda x: x['date'])
            
            if len(values_list) < 10:
                return {
                    'error': 'Insufficient data points for historical analysis',
                    'success': False,
                    'keywords': keywords
                }
            
            # Calculate statistics for normalization
            all_values = [item['value'] for item in values_list]
            max_value = max(all_values)
            min_value = min(all_values)
            avg_value = sum(all_values) / len(all_values)
            
            # Calculate sentiment scores for each data point
            for i, item in enumerate(values_list):
                current_value = item['value']
                date = item['date']
                
                # Calculate moving averages for context
                if i >= 3:
                    recent_avg = sum(all_values[max(0, i-3):i+1]) / min(4, i+1)
                else:
                    recent_avg = avg_value
                
                # Normalize current value (0-100)
                if max_value > min_value:
                    normalized_current = ((current_value - min_value) / (max_value - min_value)) * 100
                else:
                    normalized_current = 50
                
                # Calculate trend component
                if i > 0:
                    trend_change = current_value - values_list[i-1]['value']
                    trend_component = max(-25, min(25, trend_change * 2))
                else:
                    trend_component = 0
                
                # Calculate final sentiment score
                base_score = normalized_current * 0.6  # Current position weight
                context_score = (recent_avg / avg_value * 50) * 0.3  # Context weight
                trend_score = (50 + trend_component) * 0.1  # Trend weight
                
                final_score = base_score + context_score + trend_score
                final_score = max(0, min(100, final_score))
                
                historical_scores.append({
                    'date': date,
                    'google_trends_score': round(final_score, 1),
                    'interest_value': current_value,
                    'normalized_score': round(final_score / 100, 3),
                    'trend_change': round(trend_change if i > 0 else 0, 1),
                    'recent_average': round(recent_avg, 1)
                })
            
            # Calculate summary statistics
            scores = [item['google_trends_score'] for item in historical_scores]
            summary = {
                'avg_score': round(sum(scores) / len(scores), 1),
                'max_score': round(max(scores), 1),
                'min_score': round(min(scores), 1),
                'volatility': round(self._calculate_volatility(scores), 1),
                'data_points': len(historical_scores),
                'date_range': {
                    'start': historical_scores[0]['date'] if historical_scores else None,
                    'end': historical_scores[-1]['date'] if historical_scores else None
                }
            }
            
            return {
                'historical_scores': historical_scores,
                'summary': summary,
                'keywords': keywords,
                'primary_keyword': primary_keyword,
                'success': True,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing historical trends data: {e}")
            return {
                'error': f'Failed to process historical data: {e}',
                'success': False,
                'keywords': keywords
            }
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility of a series of values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    async def ping(self) -> bool:
        """
        Test Google Trends connectivity with minimal impact
        
        Returns:
            bool: True if service is accessible
        """
        try:
            # Try a very simple request
            simple_data = await self.get_crypto_trends_365_days(['bitcoin'], max_retries=1)
            return simple_data.get('success', False)
        except Exception as e:
            logger.error(f"Google Trends ping failed: {e}")
            return False


# Utility functions

def is_pytrends_available() -> bool:
    """Check if pytrends is available"""
    return PYTRENDS_AVAILABLE


def install_pytrends_instructions() -> str:
    """Get instructions for installing pytrends"""
    return """
    To use Google Trends functionality, install pytrends:
    
    pip install pytrends
    
    Note: pytrends is unofficial and may be subject to rate limiting or blocking by Google.
    Use with caution in production environments.
    """


async def get_crypto_trends_safe(keywords: List[str] = ['bitcoin']) -> Dict[str, Any]:
    """
    Convenience function for getting crypto trends safely
    
    Args:
        keywords: List of crypto keywords to search
        
    Returns:
        Dict with trends data or error information
    """
    if not PYTRENDS_AVAILABLE:
        return {
            'error': 'pytrends not available',
            'instructions': install_pytrends_instructions(),
            'success': False
        }
    
    client = SafeGoogleTrendsClient()
    
    try:
        result = await client.get_crypto_trends_365_days(keywords)
        return result
    except Exception as e:
        return {
            'error': str(e),
            'success': False,
            'keywords': keywords
        }


async def get_crypto_sentiment_safe(keywords: List[str] = ['bitcoin']) -> Dict[str, Any]:
    """
    Convenience function for getting crypto sentiment from trends safely
    
    Args:
        keywords: List of crypto keywords to analyze
        
    Returns:
        Dict with sentiment analysis or error information
    """
    if not PYTRENDS_AVAILABLE:
        return {
            'error': 'pytrends not available',
            'instructions': install_pytrends_instructions(),
            'success': False
        }
    
    client = SafeGoogleTrendsClient()
    
    try:
        result = await client.get_crypto_sentiment_from_trends(keywords)
        return result
    except Exception as e:
        return {
            'error': str(e),
            'success': False,
            'keywords': keywords
        }


async def get_historical_trends_score_safe(keywords: List[str] = ['bitcoin']) -> Dict[str, Any]:
    """
    Convenience function for getting historical Google Trends scores safely
    
    Args:
        keywords: List of crypto keywords to analyze
        
    Returns:
        Dict with 365 days of historical sentiment scores or error information
        
    Example:
        historical = await get_historical_trends_score_safe(['bitcoin'])
        if historical['success']:
            for day in historical['historical_scores'][:5]:
                print(f"{day['date']}: {day['google_trends_score']}")
    """
    if not PYTRENDS_AVAILABLE:
        return {
            'error': 'pytrends not available',
            'instructions': install_pytrends_instructions(),
            'success': False
        }
    
    client = SafeGoogleTrendsClient()
    
    try:
        result = await client.get_historical_trends_score(keywords)
        return result
    except Exception as e:
        return {
            'error': str(e),
            'success': False,
            'keywords': keywords
        }


async def get_historical_google_trends_scores_safe(keywords: List[str] = ['bitcoin'], 
                                                  days: int = 365) -> Dict[str, Any]:
    """
    Convenience function for getting historical Google Trends scores safely
    
    Args:
        keywords: List of crypto keywords to analyze
        days: Number of days to get historical scores for (max 365)
        
    Returns:
        Dict with historical Google Trends scores or error information
        
    Example:
        # Get 365 days of Bitcoin Google Trends sentiment scores
        result = await get_historical_google_trends_scores_safe(['bitcoin'])
        
        if result['success']:
            for record in result['historical_scores']:
                print(f"{record['date']}: {record['google_trends_score']}")
    """
    if not PYTRENDS_AVAILABLE:
        return {
            'error': 'pytrends not available',
            'instructions': install_pytrends_instructions(),
            'success': False
        }
    
    client = SafeGoogleTrendsClient()
    
    try:
        result = await client.get_historical_google_trends_scores(keywords, days)
        return result
    except Exception as e:
        return {
            'error': str(e),
            'success': False,
            'keywords': keywords
        }