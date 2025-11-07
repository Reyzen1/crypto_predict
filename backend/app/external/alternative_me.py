# File: ./backend/app/external/alternative_me.py
# Alternative.me API client for Fear & Greed Index

import httpx
import asyncio
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime, timezone

from app.core.rate_limiter import rate_limiter
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlternativeMeAPIError(Exception):
    """Custom exception for Alternative.me API errors"""
    pass


class AlternativeMeRateLimitError(AlternativeMeAPIError):
    """Exception for rate limit errors"""
    pass


class AlternativeMeClient:
    """
    Alternative.me API client for Fear & Greed Index data
    
    Features:
    - Rate limiting integration
    - Simple retry logic
    - Circuit breaker pattern
    - Data validation
    - Error handling and logging
    
    Alternative.me API:
    - Free API with no key required
    - Fear & Greed Index data
    - Historical data available
    - No official rate limits documented
    """
    
    def __init__(self, base_url: str = "https://api.alternative.me"):
        """
        Initialize Alternative.me client
        
        Args:
            base_url: Alternative.me API base URL
        """
        self.base_url = base_url.rstrip("/")
        self.session: Optional[httpx.AsyncClient] = None
        
        # Default headers
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "CryptoPredict-AlternativeMe/1.0"
        }
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                headers=self.headers,
                timeout=httpx.Timeout(30.0),  # 30 second timeout
                limits=httpx.Limits(max_connections=5, max_keepalive_connections=2)
            )
        return self.session
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        validate_response: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Alternative.me API with rate limiting and error handling
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            validate_response: Whether to validate response format
            max_retries: Maximum number of retries
            
        Returns:
            dict: API response data
            
        Raises:
            AlternativeMeAPIError: For API errors
            AlternativeMeRateLimitError: For rate limit errors
        """
        # Check circuit breaker
        if not await rate_limiter.check_circuit_breaker("alternative_me"):
            raise AlternativeMeAPIError("Alternative.me API is temporarily unavailable (circuit breaker open)")
        
        # Wait for rate limit (conservative approach)
        await rate_limiter.wait_for_rate_limit("alternative_me")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        session = await self._get_session()
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Making request to Alternative.me (attempt {attempt + 1}): {url}")
                
                response = await session.get(url, params=params or {})
                
                # Handle rate limiting (though not officially documented)
                if response.status_code == 429:
                    await rate_limiter.record_api_failure("alternative_me")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Alternative.me rate limited, waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise AlternativeMeRateLimitError("Rate limit exceeded")
                
                # Handle other HTTP errors
                if response.status_code >= 400:
                    await rate_limiter.record_api_failure("alternative_me")
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"Alternative.me API error: {error_msg}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise AlternativeMeAPIError(error_msg)
                
                # Parse JSON response
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    await rate_limiter.record_api_failure("alternative_me")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise AlternativeMeAPIError(f"Invalid JSON response: {e}")
                
                # Basic response validation
                if validate_response and not isinstance(data, dict):
                    await rate_limiter.record_api_failure("alternative_me")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        raise AlternativeMeAPIError("Invalid response format")
                
                # Record successful API call
                await rate_limiter.record_api_success("alternative_me")
                
                logger.debug(f"Alternative.me request successful: {url}")
                return data
                
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request timeout, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    await rate_limiter.record_api_failure("alternative_me")
                    raise AlternativeMeAPIError("Request timeout after all retries")
                    
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request error, retrying in {wait_time} seconds: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    await rate_limiter.record_api_failure("alternative_me")
                    raise AlternativeMeAPIError(f"Request failed after all retries: {e}")
        
        # Should not reach here
        raise AlternativeMeAPIError("Request failed after all retries")
    
    async def get_fear_greed_index(self, limit: int = 1, date_format: str = None) -> Dict[str, Any]:
        """
        Get Fear & Greed Index data
        
        Args:
            limit: Number of results (1-365, default: 1 for latest)
            date_format: Date format ("us" or "cn", default: None for Unix timestamp)
            
        Returns:
            dict: Fear & Greed Index data
            
        Example:
            # Get latest Fear & Greed Index
            data = await client.get_fear_greed_index()
            
            # Get last 30 days
            data = await client.get_fear_greed_index(limit=30)
            
            # Get full year of data
            data = await client.get_fear_greed_index(limit=365)
            
            Response format:
            {
                "name": "Fear and Greed Index",
                "data": [
                    {
                        "value": "74",
                        "value_classification": "Greed",
                        "timestamp": "1635724800",
                        "time_until_update": "86398"
                    }
                ],
                "metadata": {
                    "error": null
                }
            }
        """
        # Validate parameters
        if limit < 1 or limit > 365:
            raise ValueError("Limit must be between 1 and 365")
        
        if date_format and date_format not in ["us", "cn"]:
            raise ValueError("Date format must be 'us' or 'cn'")
        
        params = {
            "limit": limit,
            "format": "json"
        }
        
        # Only add date_format if explicitly specified
        if date_format:
            params["date_format"] = date_format
        
        data = await self._make_request("fng/", params)
        
        # Validate response structure
        if not self._validate_fear_greed_response(data):
            raise AlternativeMeAPIError("Invalid Fear & Greed Index response format")
        
        logger.info(f"Retrieved Fear & Greed Index data: {len(data.get('data', []))} records")
        return data
    
    async def get_latest_fear_greed_index(self) -> Dict[str, Any]:
        """
        Get the latest Fear & Greed Index value
        
        Returns:
            dict: Latest Fear & Greed Index data with parsed values
            
        Example:
            latest = await client.get_latest_fear_greed_index()
            print(f"Current Fear & Greed: {latest['value']} ({latest['classification']})")
            
            Response format:
            {
                "value": 74,
                "value_classification": "Greed",
                "timestamp": datetime object,
                "time_until_update": 86398,
                "last_updated": "2023-11-01 12:00:00 UTC"
            }
        """
        response = await self.get_fear_greed_index(limit=1)
        
        if not response.get("data") or len(response["data"]) == 0:
            raise AlternativeMeAPIError("No Fear & Greed Index data available")
        
        raw_data = response["data"][0]
        
        # Parse and enhance the data
        parsed_data = {
            "value": int(raw_data["value"]),
            "value_classification": raw_data["value_classification"],
            "timestamp": datetime.fromtimestamp(int(raw_data["timestamp"]), tz=timezone.utc),
            "time_until_update": int(raw_data.get("time_until_update", 0)),
            "last_updated": datetime.fromtimestamp(int(raw_data["timestamp"]), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "sentiment_score": self._calculate_sentiment_score(int(raw_data["value"])),
            "sentiment_description": self._get_sentiment_description(int(raw_data["value"]))
        }
        
        return parsed_data
    
    async def get_historical_fear_greed_index(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical Fear & Greed Index data
        
        Args:
            days: Number of days to retrieve (1-365)
            
        Returns:
            List of Fear & Greed Index records with parsed values
            
        Example:
            history = await client.get_historical_fear_greed_index(days=7)
            for record in history:
                print(f"{record['date']}: {record['value']} ({record['classification']})")
                
            # Get full year of data
            yearly_data = await client.get_historical_fear_greed_index(days=365)
        """
        if days < 1 or days > 365:
            raise ValueError("Days must be between 1 and 365")
        
        response = await self.get_fear_greed_index(limit=days)
        
        if not response.get("data"):
            raise AlternativeMeAPIError("No historical Fear & Greed Index data available")
        
        # Parse all historical records
        historical_data = []
        for raw_record in response["data"]:
            try:
                value = int(raw_record["value"])
                timestamp = datetime.fromtimestamp(int(raw_record["timestamp"]), tz=timezone.utc)
                
                parsed_record = {
                    "value": value,
                    "value_classification": raw_record["value_classification"],
                    "timestamp": timestamp,
                    "date": timestamp.strftime("%Y-%m-%d"),
                    "time_until_update": int(raw_record.get("time_until_update", 0)),
                    "sentiment_score": self._calculate_sentiment_score(value),
                    "sentiment_description": self._get_sentiment_description(value)
                }
                
                historical_data.append(parsed_record)
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing historical record: {e}")
                continue
        
        logger.info(f"Retrieved {len(historical_data)} historical Fear & Greed Index records")
        return historical_data
    
    def _validate_fear_greed_response(self, data: Dict[str, Any]) -> bool:
        """
        Validate Fear & Greed Index response format
        
        Args:
            data: Response data from API
            
        Returns:
            bool: True if response is valid
        """
        try:
            # Check basic structure
            if not isinstance(data, dict):
                logger.warning("Response is not a dictionary")
                return False
            
            if "data" not in data:
                logger.warning("'data' field missing from response")
                return False
                
            if not isinstance(data["data"], list):
                logger.warning("'data' field is not a list")
                return False
            
            if len(data["data"]) == 0:
                logger.warning("'data' field is empty")
                return False
            
            # Check each data record
            for i, record in enumerate(data["data"]):
                if not isinstance(record, dict):
                    logger.warning(f"Record {i} is not a dictionary")
                    return False
                
                required_fields = ["value", "value_classification", "timestamp"]
                missing_fields = [field for field in required_fields if field not in record]
                if missing_fields:
                    logger.warning(f"Record {i} missing fields: {missing_fields}")
                    return False
                
                # Validate data types and values
                try:
                    value = int(record["value"])  # Value should be convertible to int
                    timestamp = int(record["timestamp"])  # Timestamp should be convertible to int
                except ValueError as e:
                    logger.warning(f"Record {i} has invalid numeric values: {e}")
                    return False
                
                # Validate value range (0-100)
                if value < 0 or value > 100:
                    logger.warning(f"Record {i} has invalid value range: {value}")
                    return False
                
                # Validate classification (be more permissive)
                classification = record["value_classification"]
                if not isinstance(classification, str) or len(classification.strip()) == 0:
                    logger.warning(f"Record {i} has invalid classification: {classification}")
                    return False
            
            logger.debug("Fear & Greed response validation successful")
            return True
            
        except Exception as e:
            logger.warning(f"Validation error: {e}")
            return False
    
    def _calculate_sentiment_score(self, fear_greed_value: int) -> float:
        """
        Calculate normalized sentiment score from Fear & Greed value
        
        Args:
            fear_greed_value: Fear & Greed Index value (0-100)
            
        Returns:
            float: Normalized sentiment score (-1.0 to 1.0)
                  -1.0 = Extreme Fear, 0.0 = Neutral, 1.0 = Extreme Greed
        """
        # Convert 0-100 scale to -1.0 to 1.0 scale
        return (fear_greed_value - 50) / 50.0
    
    def _get_sentiment_description(self, fear_greed_value: int) -> str:
        """
        Get detailed sentiment description based on Fear & Greed value
        
        Args:
            fear_greed_value: Fear & Greed Index value (0-100)
            
        Returns:
            str: Detailed sentiment description
        """
        if fear_greed_value <= 20:
            return "Extreme Fear - Market is oversold, potential buying opportunity"
        elif fear_greed_value <= 40:
            return "Fear - Market sentiment is negative, caution advised"
        elif fear_greed_value <= 60:
            return "Neutral - Market sentiment is balanced"
        elif fear_greed_value <= 80:
            return "Greed - Market sentiment is positive, potential overheating"
        else:
            return "Extreme Greed - Market may be overbought, consider taking profits"
    
    async def get_market_sentiment_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive market sentiment analysis based on current Fear & Greed Index
        
        Returns:
            dict: Comprehensive sentiment analysis
            
        Example:
            analysis = await client.get_market_sentiment_analysis()
            print(f"Market Sentiment: {analysis['overall_sentiment']}")
            print(f"Recommendation: {analysis['trading_recommendation']}")
        """
        latest = await self.get_latest_fear_greed_index()
        value = latest["value"]
        
        # Calculate additional metrics
        analysis = {
            "current_value": value,
            "classification": latest["value_classification"],
            "sentiment_score": latest["sentiment_score"],
            "last_updated": latest["last_updated"],
            "overall_sentiment": self._get_overall_sentiment(value),
            "trading_recommendation": self._get_trading_recommendation(value),
            "risk_level": self._get_risk_level(value),
            "market_phase": self._get_market_phase(value),
            "confidence_level": self._get_confidence_level(value)
        }
        
        return analysis
    
    def _get_overall_sentiment(self, value: int) -> str:
        """Get overall market sentiment"""
        if value <= 25:
            return "Extremely Bearish"
        elif value <= 45:
            return "Bearish"
        elif value <= 55:
            return "Neutral"
        elif value <= 75:
            return "Bullish"
        else:
            return "Extremely Bullish"
    
    def _get_trading_recommendation(self, value: int) -> str:
        """Get trading recommendation based on Fear & Greed value"""
        if value <= 20:
            return "Strong Buy - Market fear creates opportunities"
        elif value <= 35:
            return "Buy - Good entry point during fear"
        elif value <= 45:
            return "Cautious Buy - Some fear present"
        elif value <= 55:
            return "Hold - Neutral market conditions"
        elif value <= 70:
            return "Cautious Sell - Greed building up"
        elif value <= 85:
            return "Sell - High greed, consider profit taking"
        else:
            return "Strong Sell - Extreme greed, major correction risk"
    
    def _get_risk_level(self, value: int) -> str:
        """Get risk level assessment"""
        if value <= 30 or value >= 80:
            return "High"
        elif value <= 45 or value >= 70:
            return "Medium"
        else:
            return "Low"
    
    def _get_market_phase(self, value: int) -> str:
        """Get current market phase"""
        if value <= 25:
            return "Capitulation"
        elif value <= 40:
            return "Accumulation"
        elif value <= 60:
            return "Consolidation"
        elif value <= 80:
            return "Distribution"
        else:
            return "Euphoria"
    
    def _get_confidence_level(self, value: int) -> str:
        """Get confidence level in the sentiment reading"""
        # Extreme values typically have higher confidence
        if value <= 15 or value >= 85:
            return "Very High"
        elif value <= 25 or value >= 75:
            return "High"
        elif value <= 35 or value >= 65:
            return "Medium"
        else:
            return "Low"
    
    async def ping(self) -> bool:
        """
        Test API connectivity
        
        Returns:
            bool: True if API is reachable, False otherwise
        """
        try:
            # Try to get latest data to test connectivity
            await self.get_fear_greed_index(limit=1)
            return True
        except Exception as e:
            logger.error(f"Alternative.me ping failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Utility functions for Fear & Greed Index analysis

def interpret_fear_greed_value(value: int) -> Dict[str, str]:
    """
    Interpret Fear & Greed Index value and provide insights
    
    Args:
        value: Fear & Greed Index value (0-100)
        
    Returns:
        dict: Interpretation with various insights
    """
    insights = {
        "value": str(value),
        "classification": "",
        "market_condition": "",
        "investor_behavior": "",
        "opportunity_type": "",
        "risk_assessment": ""
    }
    
    if value <= 20:
        insights.update({
            "classification": "Extreme Fear",
            "market_condition": "Oversold market conditions",
            "investor_behavior": "Panic selling, capitulation",
            "opportunity_type": "Strong buying opportunity",
            "risk_assessment": "Low downside risk, high upside potential"
        })
    elif value <= 40:
        insights.update({
            "classification": "Fear",
            "market_condition": "Bearish sentiment dominates",
            "investor_behavior": "Risk aversion, pessimism",
            "opportunity_type": "Good accumulation phase",
            "risk_assessment": "Moderate risk, good reward potential"
        })
    elif value <= 60:
        insights.update({
            "classification": "Neutral",
            "market_condition": "Balanced market sentiment",
            "investor_behavior": "Mixed signals, indecision",
            "opportunity_type": "Wait for clearer signals",
            "risk_assessment": "Balanced risk-reward"
        })
    elif value <= 80:
        insights.update({
            "classification": "Greed",
            "market_condition": "Bullish sentiment prevails",
            "investor_behavior": "FOMO, increased risk appetite",
            "opportunity_type": "Consider profit taking",
            "risk_assessment": "Increased risk, potential for correction"
        })
    else:
        insights.update({
            "classification": "Extreme Greed",
            "market_condition": "Potentially overheated market",
            "investor_behavior": "Euphoria, reckless speculation",
            "opportunity_type": "Strong selling opportunity",
            "risk_assessment": "High downside risk, limited upside"
        })
    
    return insights


def calculate_fear_greed_trend(historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate Fear & Greed Index trend analysis
    
    Args:
        historical_data: List of historical Fear & Greed data
        
    Returns:
        dict: Trend analysis results
    """
    if not historical_data or len(historical_data) < 2:
        return {"error": "Insufficient data for trend analysis"}
    
    # Sort by timestamp (newest first)
    sorted_data = sorted(historical_data, key=lambda x: x["timestamp"], reverse=True)
    
    # Calculate trends
    values = [record["value"] for record in sorted_data]
    current_value = values[0]
    previous_value = values[1] if len(values) > 1 else current_value
    
    # Short-term trend (last 7 days)
    short_term_values = values[:min(7, len(values))]
    short_term_avg = sum(short_term_values) / len(short_term_values)
    
    # Medium-term trend (last 30 days)
    medium_term_values = values[:min(30, len(values))]
    medium_term_avg = sum(medium_term_values) / len(medium_term_values)
    
    # Calculate changes
    daily_change = current_value - previous_value
    weekly_change = current_value - short_term_avg if len(short_term_values) > 1 else 0
    monthly_change = current_value - medium_term_avg if len(medium_term_values) > 1 else 0
    
    # Determine trend directions
    def get_trend_direction(change: float) -> str:
        if change > 2:
            return "Strongly Increasing"
        elif change > 0.5:
            return "Increasing"
        elif change < -2:
            return "Strongly Decreasing"
        elif change < -0.5:
            return "Decreasing"
        else:
            return "Stable"
    
    trend_analysis = {
        "current_value": current_value,
        "previous_value": previous_value,
        "daily_change": daily_change,
        "weekly_change": weekly_change,
        "monthly_change": monthly_change,
        "short_term_avg": round(short_term_avg, 1),
        "medium_term_avg": round(medium_term_avg, 1),
        "daily_trend": get_trend_direction(daily_change),
        "weekly_trend": get_trend_direction(weekly_change),
        "monthly_trend": get_trend_direction(monthly_change),
        "volatility": round(
            sum(abs(values[i] - values[i+1]) for i in range(len(values)-1)) / (len(values)-1), 1
        ) if len(values) > 1 else 0,
        "data_points": len(historical_data)
    }
    
    return trend_analysis