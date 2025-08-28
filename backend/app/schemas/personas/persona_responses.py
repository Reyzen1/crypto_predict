# File: backend/app/schemas/personas/persona_responses.py
# Persona-specific response schemas 
# Compatible with existing schema patterns from app/schemas/__init__.py

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal
from enum import Enum

# Import existing schemas for compatibility
from app.schemas.common import BaseSchema
from app.schemas.prediction import PredictionResult
from app.schemas.cryptocurrency import CryptocurrencyResponse

# ==============================
# BASE PERSONA RESPONSE CLASSES
# ==============================

class PersonaType(str, Enum):
    """Persona types matching PersonaDetector"""
    ADMIN = "admin"
    PROFESSIONAL = "professional" 
    CASUAL = "casual"

class BasePersonaResponse(BaseSchema):
    """
    Base response class that adapts to user persona
    Compatible with existing BaseSchema pattern from schemas/common.py
    """
    persona_type: PersonaType = Field(description="User persona type")
    user_id: int = Field(description="User ID from existing User model")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
    )

# ==============================
# ADMIN PERSONA RESPONSES (محمدرضا)
# ==============================

class SystemMetrics(BaseModel):
    """System performance metrics for admin dashboard"""
    total_users: int = Field(description="Total users in system")
    active_users_24h: int = Field(description="Active users in last 24 hours")
    total_predictions: int = Field(description="Total predictions made")
    system_accuracy: float = Field(description="Overall system accuracy percentage")
    uptime_percentage: float = Field(description="System uptime percentage")
    response_time_avg_ms: float = Field(description="Average API response time")

class BulkAction(BaseModel):
    """Available bulk actions for admin"""
    action_id: str = Field(description="Unique action identifier")
    name: str = Field(description="Human-readable action name")
    description: str = Field(description="Action description")
    max_items: int = Field(description="Maximum items per bulk operation")
    estimated_time_seconds: int = Field(description="Estimated completion time")
    usage_count_today: int = Field(description="Times used today")

class AdminInsight(BaseModel):
    """AI-generated insights for admin decision making"""
    insight_type: str = Field(description="Type of insight (trend, alert, recommendation)")
    title: str = Field(description="Insight title")
    description: str = Field(description="Detailed insight description")
    confidence: float = Field(description="Confidence level 0-1")
    priority: str = Field(description="Priority level (low, medium, high, urgent)")
    actionable: bool = Field(description="Whether insight requires immediate action")
    suggested_actions: List[str] = Field(description="Recommended actions")

class AdminRegimeResponse(BasePersonaResponse):
    """
    Response schema for Admin persona (محمدرضا - 35-45 years old)
    Provides comprehensive system data and management tools
    """
    # Core regime data
    regime: str = Field(description="Market regime (bull/bear/neutral/volatile)")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")
    regime_strength: str = Field(description="Strength of regime (weak/moderate/strong)")
    
    # Comprehensive metrics for admin oversight
    detailed_metrics: Dict[str, Any] = Field(
        description="Complete technical metrics and indicators"
    )
    system_performance: SystemMetrics = Field(
        description="System-wide performance metrics"
    )
    
    # Bulk management capabilities
    bulk_actions_available: List[BulkAction] = Field(
        description="Available bulk management actions"
    )
    
    # AI-driven insights for decision making
    admin_insights: List[AdminInsight] = Field(
        description="AI-generated insights for system optimization"
    )
    
    # Efficiency tracking (targeting 70% improvement per design docs)
    efficiency_metrics: Dict[str, float] = Field(
        description="Efficiency improvements and time savings"
    )
    
    # User distribution by persona (for oversight)
    user_distribution: Dict[str, int] = Field(
        description="Current user distribution by persona type"
    )
    
    # System alerts requiring admin attention
    pending_alerts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Alerts requiring admin review"
    )

# ==============================
# PROFESSIONAL PERSONA RESPONSES (سارا)
# ==============================

class TradingSignal(BaseModel):
    """Real-time trading signal for professionals"""
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    signal_type: str = Field(description="Signal type (buy/sell/hold)")
    strength: float = Field(ge=0, le=1, description="Signal strength 0-1")
    timeframe: str = Field(description="Recommended timeframe")
    entry_price: Optional[Decimal] = Field(None, description="Suggested entry price")
    target_price: Optional[Decimal] = Field(None, description="Target price")
    stop_loss: Optional[Decimal] = Field(None, description="Stop loss price")
    confidence: float = Field(description="Signal confidence level")
    expires_at: datetime = Field(description="Signal expiration time")

class RiskAssessment(BaseModel):
    """Risk assessment for professional traders"""
    overall_risk_level: str = Field(description="Overall risk (low/medium/high/extreme)")
    risk_score: float = Field(ge=0, le=1, description="Numeric risk score")
    risk_factors: List[str] = Field(description="Identified risk factors")
    portfolio_exposure: Dict[str, float] = Field(description="Current exposure by asset")
    recommended_adjustments: List[str] = Field(description="Risk management suggestions")
    max_position_size: float = Field(description="Maximum recommended position size")

class PerformanceMetrics(BaseModel):
    """Performance tracking for professional users"""
    total_trades: int = Field(description="Total trades executed")
    win_rate: float = Field(description="Win rate percentage")
    average_return: float = Field(description="Average return percentage")
    sharpe_ratio: float = Field(description="Sharpe ratio")
    max_drawdown: float = Field(description="Maximum drawdown percentage")
    current_streak: int = Field(description="Current winning/losing streak")

class ProfessionalRegimeResponse(BasePersonaResponse):
    """
    Response schema for Professional persona (سارا - 28-40 years old)
    Optimized for speed (<500ms) and trading precision
    """
    # Core regime data (speed-optimized)
    regime: str = Field(description="Market regime")
    confidence: float = Field(ge=0, le=1, description="Confidence score")
    regime_change_probability: float = Field(description="Probability of regime change soon")
    
    # Immediate actionable signals (< 30 seconds requirement)
    immediate_signals: List[TradingSignal] = Field(
        description="Real-time trading signals ready for execution"
    )
    
    # Professional-grade risk assessment
    risk_assessment: RiskAssessment = Field(
        description="Comprehensive risk analysis"
    )
    
    # Trading recommendations with precise timing
    trading_recommendations: List[Dict[str, Any]] = Field(
        description="Specific trading recommendations with timing"
    )
    
    # Performance tracking (professionals track everything)
    performance_tracking: PerformanceMetrics = Field(
        description="Detailed performance metrics"
    )
    
    # Speed-optimized data (pre-calculated for fast response)
    speed_optimized_data: Dict[str, Any] = Field(
        description="Pre-calculated data for minimal latency"
    )
    
    # Market conditions context
    market_context: Dict[str, Any] = Field(
        description="Current market conditions affecting trades"
    )
    
    # Expected response time validation
    response_time_ms: float = Field(
        description="Actual response generation time in milliseconds"
    )

# ==============================
# CASUAL PERSONA RESPONSES (علی)  
# ==============================

class EducationalContent(BaseModel):
    """Educational content for casual investors"""
    topic: str = Field(description="Educational topic")
    explanation: str = Field(description="Simple explanation")
    why_important: str = Field(description="Why this matters for investing")
    example: Optional[str] = Field(None, description="Real-world example")
    next_steps: List[str] = Field(description="What to learn next")

class GuidedAction(BaseModel):
    """Guided action for casual users"""
    action_id: str = Field(description="Action identifier")
    title: str = Field(description="Action title")
    description: str = Field(description="What this action does")
    difficulty: str = Field(description="Difficulty level (easy/medium/hard)")
    time_required: str = Field(description="Estimated time needed")
    step_by_step: List[str] = Field(description="Step-by-step instructions")
    benefits: List[str] = Field(description="Benefits of taking this action")
    risks: List[str] = Field(description="Potential risks to be aware of")

class ProgressTracking(BaseModel):
    """Learning and investment progress for casual users"""
    learning_score: float = Field(ge=0, le=1, description="Learning progress 0-1")
    lessons_completed: int = Field(description="Number of educational lessons completed")
    predictions_made: int = Field(description="Total predictions made")
    accuracy_trend: str = Field(description="Accuracy trend (improving/stable/declining)")
    next_milestone: str = Field(description="Next learning milestone")
    achievements: List[str] = Field(description="Unlocked achievements")

class CasualRegimeResponse(BasePersonaResponse):
    """
    Response schema for Casual persona (علی - 25-35 years old)
    Simplified, educational, and encouraging
    """
    # Simplified regime data (no complex numbers)
    regime: str = Field(description="Market regime in simple terms")
    confidence_description: str = Field(
        description="Confidence level in plain English (e.g., 'Very confident', 'Somewhat sure')"
    )
    regime_emoji: str = Field(description="Emoji representing current market mood")
    
    # Simple explanation without jargon
    simple_explanation: str = Field(
        description="Easy-to-understand explanation of what this means"
    )
    
    # Educational content to build knowledge
    learning_content: EducationalContent = Field(
        description="Educational content related to current market situation"
    )
    
    # Step-by-step guided actions
    guided_actions: List[GuidedAction] = Field(
        description="Specific actions the user can take with guidance"
    )
    
    # Progress tracking for motivation
    progress_tracking: ProgressTracking = Field(
        description="User's learning and investment progress"
    )
    
    # Confidence building elements
    encouragement: Dict[str, Any] = Field(
        description="Encouraging messages and positive reinforcement"
    )
    
    # Related educational topics
    suggested_learning: List[str] = Field(
        description="Suggested topics to learn more about"
    )
    
    # Safety reminders
    risk_reminders: List[str] = Field(
        description="Important risk management reminders"
    )

# ==============================
# FACTORY RESPONSE TYPES
# ==============================

# Union type for all persona responses
PersonaAwareResponse = Union[AdminRegimeResponse, ProfessionalRegimeResponse, CasualRegimeResponse]

# Response metadata for debugging and analytics
class PersonaResponseMetadata(BaseModel):
    """Metadata about persona response generation"""
    detected_persona: PersonaType = Field(description="Auto-detected persona")
    response_generation_time_ms: float = Field(description="Time to generate response")
    data_sources_used: List[str] = Field(description="Data sources consulted")
    personalization_applied: List[str] = Field(description="Personalization features applied")
    user_context_factors: Dict[str, Any] = Field(description="User context factors considered")

class PersonaResponseWrapper(BaseModel):
    """
    Wrapper for any persona response with metadata
    Useful for debugging and analytics
    """
    response_data: PersonaAwareResponse = Field(description="The actual persona response")
    metadata: PersonaResponseMetadata = Field(description="Response generation metadata")
    cache_key: Optional[str] = Field(None, description="Cache key if response was cached")
    expires_at: Optional[datetime] = Field(None, description="When this response expires")