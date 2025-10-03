# backend/app/models/macro/regime_analysis.py

"""
AI Market Regime Analysis Model
AI-powered comprehensive market regime analysis and predictions
"""
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Text, DateTime,
    ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from ..base import BaseModel, TimestampMixin
from ..mixins import AIAnalysisMixin, ValidationMixin
from ..enums import TimeframeEnum, MarketRegime


class TradingStrategy(str, Enum):
    """Recommended trading strategy enum"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    RANGE_TRADING = "range_trading"
    DEFENSIVE = "defensive"


class PositionSizing(str, Enum):
    """Position sizing guidance enum"""
    CONSERVATIVE = "conservative"
    NORMAL = "normal"
    AGGRESSIVE = "aggressive"
    MAXIMUM = "maximum"


class RiskAppetite(str, Enum):
    """Global risk appetite enum"""
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    MIXED = "mixed"
    TRANSITIONING = "transitioning"


class MacroAlignment(str, Enum):
    """Macro environment alignment enum"""
    SUPPORTIVE = "supportive"
    NEUTRAL = "neutral"
    HEADWIND = "headwind"


class LiquidityRegime(str, Enum):
    """Liquidity environment classification"""
    ABUNDANT = "abundant"
    NORMAL = "normal"
    TIGHT = "tight"
    STRESSED = "stressed"


class SentimentRegime(str, Enum):
    """Sentiment-based regime classification"""
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"


class RegimeAnalysisTimeframes:
    """Valid timeframes for regime analysis"""
    VALID_TIMEFRAMES = [
        TimeframeEnum.ONE_HOUR.value,
        TimeframeEnum.FOUR_HOURS.value, 
        TimeframeEnum.ONE_DAY.value,
        TimeframeEnum.ONE_WEEK.value,
        TimeframeEnum.ONE_MONTH.value
    ]
    
    @classmethod
    def is_valid_timeframe(cls, timeframe: str) -> bool:
        """Check if timeframe is valid for regime analysis"""
        return timeframe in cls.VALID_TIMEFRAMES
    
    @classmethod
    def get_valid_timeframes(cls) -> list:
        """Get list of valid timeframes"""
        return cls.VALID_TIMEFRAMES.copy()
    
    @classmethod
    def get_timeframe_enum(cls, timeframe: str):
        """Get TimeframeEnum from string value"""
        timeframe_map = {
            TimeframeEnum.ONE_HOUR.value: TimeframeEnum.ONE_HOUR,
            TimeframeEnum.FOUR_HOURS.value: TimeframeEnum.FOUR_HOURS,
            TimeframeEnum.ONE_DAY.value: TimeframeEnum.ONE_DAY,
            TimeframeEnum.ONE_WEEK.value: TimeframeEnum.ONE_WEEK,
            TimeframeEnum.ONE_MONTH.value: TimeframeEnum.ONE_MONTH
        }
        return timeframe_map.get(timeframe)
    
    @classmethod
    def get_default_timeframe(cls) -> str:
        """Get default timeframe for regime analysis"""
        return TimeframeEnum.ONE_DAY.value


class AIMarketRegimeAnalysis(BaseModel, TimestampMixin, AIAnalysisMixin, ValidationMixin):
    """
    AI Market Regime Analysis Model
    
    Comprehensive AI-powered market regime analysis including:
    - Regime classification and prediction
    - Market structure and breakout analysis
    - Multi-timeframe regime alignment
    - Trading implications and risk assessment
    - Historical context and statistical analysis
    """
    __tablename__ = "ai_market_regime_analysis"
    
    # Primary key
    id = Column(Integer, primary_key=True, nullable=False)
    
    # Foreign key relationships
    metrics_snapshot_id = Column(
        Integer, 
        ForeignKey("metrics_snapshot.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to metrics snapshot"
    )
    ai_model_id = Column(
        Integer,
        ForeignKey("ai_models.id", ondelete="CASCADE"),
        nullable=False,
        comment="AI model used for analysis"
    )
    
    # Analysis metadata
    analysis_time = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="When this analysis was executed"
    )
    analysis_timeframe = Column(
        String(10),
        nullable=False,
        comment="Analysis timeframe: '1h','4h','1d','1w','1M'"
    )
    data_source = Column(
        String(20),
        nullable=False,
        default="live",
        comment="Data source: live, backtest, simulation"
    )
    
    # Regime classification
    current_regime = Column(
        String(15),
        nullable=False,
        comment="Detected current regime"
    )
    predicted_regime = Column(
        String(15),
        comment="AI-predicted next regime"
    )
    regime_confidence = Column(
        Numeric(4, 2),
        nullable=False,
        comment="AI confidence in regime classification (0–1)"
    )
    regime_transition_prob = Column(
        Numeric(4, 2),
        comment="Probability of regime change in next period (0–1)"
    )
    regime_duration_days = Column(
        Integer,
        comment="Current regime duration in days"
    )
    regime_duration_estimate = Column(
        Integer,
        comment="Estimated remaining duration of current regime (hours)"
    )
    
    # Regime strength & quality metrics
    trend_strength_score = Column(
        Numeric(6, 2),
        comment="AI trend strength assessment (0–1)"
    )
    regime_quality_score = Column(
        Numeric(6, 2),
        comment="Quality/clarity of current regime (0–1)"
    )
    volatility_regime_score = Column(
        Numeric(6, 2),
        comment="Volatility assessment: low(0-0.3), medium(0.3-0.7), high(0.7-1)"
    )
    momentum_alignment_score = Column(
        Numeric(6, 2),
        comment="Alignment between price and momentum indicators (0–1)"
    )
    
    # Market structure analysis
    trend_intact = Column(
        Boolean,
        comment="Whether primary trend remains intact"
    )
    structure_break = Column(
        Boolean,
        comment="TRUE if market structure was broken"
    )
    structure_change_type = Column(
        String(20),
        comment="Type of structure change: 'higher_high', 'lower_low', 'consolidation', 'reversal'"
    )
    structure_strength = Column(
        Numeric(8, 4),
        comment="Strength of current market structure (0–1)"
    )
    
    # Technical breakout & pattern analysis
    breakout_signal = Column(
        Boolean,
        comment="TRUE if price broke key technical level"
    )
    breakout_type = Column(
        String(30),
        comment="Type of breakout: 'resistance', 'support', 'trendline', 'pattern', 'range'"
    )
    breakout_level = Column(
        Numeric(18, 8),
        comment="Price level of the breakout"
    )
    volume_confirmation = Column(
        Boolean,
        comment="TRUE if breakout volume ≥ threshold above average"
    )
    volume_surge_ratio = Column(
        Numeric(6, 2),
        comment="Volume surge ratio vs average (1.0 = average)"
    )
    retest_confirmation = Column(
        Boolean,
        comment="TRUE if breakout level was retested successfully"
    )
    volatility_expansion_score = Column(
        Numeric(6, 2),
        comment="Volatility expansion during breakout (0–1)"
    )
    
    # Multi-timeframe analysis
    timeframe_alignment = Column(
        JSONB,
        comment="Cross-timeframe regime alignment data"
    )
    multi_timeframe_agreement = Column(
        Boolean,
        comment="TRUE if multiple timeframes agree on regime"
    )
    timeframe_consensus_score = Column(
        Numeric(4, 2),
        comment="Consensus strength across timeframes (0–1)"
    )
    
    # AI-detected key levels & zones
    key_levels = Column(
        JSONB,
        comment="Enhanced key levels with context and strength"
    )
    
    # Market psychology & sentiment integration
    sentiment_regime = Column(
        String(20),
        comment="Sentiment-based regime: 'extreme_fear', 'fear', 'neutral', 'greed', 'extreme_greed'"
    )
    fear_greed_impact = Column(
        Numeric(6, 2),
        comment="Impact of fear/greed on regime (0–1)"
    )
    sentiment_regime_conflict = Column(
        Boolean,
        comment="TRUE if price and sentiment regimes conflict"
    )
    psychological_level_score = Column(
        Numeric(4, 2),
        comment="Proximity to psychological levels impact (0–1)"
    )
    
    # Flow & liquidity analysis
    liquidity_regime = Column(
        String(20),
        comment="Liquidity environment: 'abundant', 'normal', 'tight', 'stressed'"
    )
    institutional_flow_score = Column(
        Numeric(6, 2),
        comment="Institutional flow impact on regime (0–1)"
    )
    retail_participation_score = Column(
        Numeric(6, 2),
        comment="Retail participation level (0–1)"
    )
    whale_activity_influence = Column(
        Boolean,
        comment="TRUE if whale activity significantly influenced regime"
    )
    
    # Intermarket & macro context
    macro_regime_alignment = Column(
        String(20),
        comment="Alignment with macro environment: 'supportive', 'neutral', 'headwind'"
    )
    correlation_stability = Column(
        Numeric(4, 2),
        comment="Stability of crypto-traditional market correlations (0–1)"
    )
    risk_on_off_regime = Column(
        Boolean,
        comment="TRUE if in clear risk-on/risk-off regime"
    )
    global_risk_appetite = Column(
        String(15),
        comment="Global risk appetite: 'risk_on', 'risk_off', 'mixed', 'transitioning'"
    )
    
    # Regime transition signals
    transition_indicators = Column(
        JSONB,
        comment="Early regime transition signals and probabilities"
    )
    
    # Trading & investment implications
    recommended_strategy = Column(
        String(20),
        comment="Recommended strategy: 'trend_following', 'mean_reversion', 'breakout', 'range_trading', 'defensive'"
    )
    risk_adjustment_factor = Column(
        Numeric(4, 2),
        comment="Suggested risk adjustment (0.5=half risk, 2.0=double risk)"
    )
    position_sizing_guidance = Column(
        String(20),
        comment="Position sizing: 'conservative', 'normal', 'aggressive', 'maximum'"
    )
    sector_regime_impact = Column(
        JSONB,
        comment="Impact on different sectors and their expected performance"
    )
    
    # Enhanced AI meta-signals
    # ai_confidence_score and signal_agreement_score inherited from AIAnalysisMixin
    prediction_stability = Column(
        Numeric(4, 2),
        comment="Stability of predictions over recent periods (0–1)"
    )
    model_performance_rating = Column(
        String(20),
        comment="Recent model performance: 'excellent', 'good', 'average', 'poor'"
    )
    
    # Historical context & comparison
    historical_analogue = Column(
        String(30),
        comment="Similar historical market period"
    )
    historical_similarity = Column(
        Numeric(4, 2),
        comment="Similarity to historical pattern (0–1)"
    )
    regime_statistics = Column(
        JSONB,
        comment="Statistical analysis of current regime vs historical data"
    )
    
    # Quality assurance & validation
    # is_validated field inherited from ValidationMixin
    validation_flags = Column(
        JSONB,
        comment="Quality flags and warnings from validation process"
    )
    analysis_version = Column(
        String(50),
        comment="Version of analysis pipeline used"
    )
    analyst_notes = Column(
        Text,
        comment="Manual analyst notes and observations"
    )
    
    # Comprehensive analysis rationale
    # analysis_data field inherited from AIAnalysisMixin
    
    # Relationships
    metrics_snapshot = relationship("MetricsSnapshot", back_populates="regime_analyses")
    ai_model = relationship("AIModel", back_populates="regime_analyses")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "regime_confidence BETWEEN 0 AND 1",
            name="chk_regime_confidence"
        ),
        CheckConstraint(
            "regime_transition_prob IS NULL OR regime_transition_prob BETWEEN 0 AND 1",
            name="chk_transition_prob"
        ),
        CheckConstraint(
            "trend_strength_score IS NULL OR trend_strength_score BETWEEN 0 AND 1",
            name="chk_trend_strength"
        ),
        CheckConstraint(
            "risk_adjustment_factor IS NULL OR risk_adjustment_factor BETWEEN 0.1 AND 5.0",
            name="chk_risk_adjustment"
        ),
        CheckConstraint(
            "regime_duration_days IS NULL OR regime_duration_days >= 0",
            name="chk_regime_duration_positive"
        ),
        CheckConstraint(
            "current_regime IN ('Bull', 'Bear', 'Sideways', 'Transition', 'Accumulation', 'Distribution')",
            name="chk_current_regime_valid"
        ),
        CheckConstraint(
            "analysis_timeframe IN ('1h', '4h', '1d', '1w')",
            name="chk_analysis_timeframe_valid"
        ),
        Index("idx_regime_analysis_time", "analysis_time"),
        Index("idx_regime_analysis_regime", "current_regime"),
        Index("idx_regime_analysis_timeframe", "analysis_timeframe"),
        Index("idx_regime_analysis_confidence", "regime_confidence"),
        Index("idx_regime_analysis_snapshot", "metrics_snapshot_id"),
    )
    
    def __repr__(self):
        return f"<AIMarketRegimeAnalysis(id={self.id}, regime={self.current_regime}, confidence={self.regime_confidence}, time={self.analysis_time})>"
    
    @property
    def is_bullish_regime(self) -> bool:
        """Check if current regime is bullish"""
        return self.current_regime in [MarketRegime.BULL.value, MarketRegime.ACCUMULATION.value]
    
    @property
    def is_bearish_regime(self) -> bool:
        """Check if current regime is bearish"""
        return self.current_regime in [MarketRegime.BEAR.value, MarketRegime.DISTRIBUTION.value]
    
    @property
    def is_neutral_regime(self) -> bool:
        """Check if current regime is neutral/sideways"""
        return self.current_regime in [MarketRegime.SIDEWAYS.value, MarketRegime.TRANSITION.value]
    
    @property
    def high_confidence_regime(self) -> bool:
        """Check if regime classification has high confidence (>0.8)"""
        return self.regime_confidence and self.regime_confidence > 0.8
    
    @property
    def regime_change_likely(self) -> bool:
        """Check if regime change is likely (>0.6 probability)"""
        return self.regime_transition_prob and self.regime_transition_prob > 0.6
    
    @property
    def strong_trend(self) -> bool:
        """Check if trend strength is strong (>0.7)"""
        return self.trend_strength_score and self.trend_strength_score > 0.7
    
    @property
    def breakout_confirmed(self) -> bool:
        """Check if breakout is confirmed with volume"""
        return (self.breakout_signal and 
                self.volume_confirmation and 
                self.volatility_expansion_score and 
                self.volatility_expansion_score > 0.6)
    
    @property
    def timeframes_aligned(self) -> bool:
        """Check if multiple timeframes are aligned"""
        return (self.multi_timeframe_agreement and 
                self.timeframe_consensus_score and 
                self.timeframe_consensus_score > 0.7)
    
    @property
    def sentiment_price_divergence(self) -> bool:
        """Check if there's sentiment-price divergence"""
        return self.sentiment_regime_conflict or False
    
    @property
    def risk_level(self) -> str:
        """Get current risk level assessment"""
        if not self.volatility_regime_score:
            return "unknown"
        
        if self.volatility_regime_score <= 0.3:
            return "low"
        elif self.volatility_regime_score <= 0.7:
            return "medium"
        else:
            return "high"
    
    @property
    def timeframe_enum(self):
        """Get TimeframeEnum for analysis_timeframe"""
        return RegimeAnalysisTimeframes.get_timeframe_enum(self.analysis_timeframe)
    
    @property
    def current_regime_enum(self):
        """Get MarketRegime enum for current_regime"""
        regime_map = {
            MarketRegime.BULL.value: MarketRegime.BULL,
            MarketRegime.BEAR.value: MarketRegime.BEAR,
            MarketRegime.SIDEWAYS.value: MarketRegime.SIDEWAYS,
            MarketRegime.TRANSITION.value: MarketRegime.TRANSITION,
            MarketRegime.ACCUMULATION.value: MarketRegime.ACCUMULATION,
            MarketRegime.DISTRIBUTION.value: MarketRegime.DISTRIBUTION
        }
        return regime_map.get(self.current_regime)
    
    @classmethod
    def get_latest_analysis(cls, session, timeframe: str = TimeframeEnum.ONE_DAY.value):
        """Get the most recent regime analysis for a timeframe"""
        return session.query(cls).filter(
            cls.analysis_timeframe == timeframe
        ).order_by(cls.analysis_time.desc()).first()
    
    @classmethod
    def get_regime_history(cls, session, days: int = 30, timeframe: str = TimeframeEnum.ONE_DAY.value):
        """Get regime analysis history for the past N days"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return session.query(cls).filter(
            cls.analysis_timeframe == timeframe,
            cls.analysis_time >= cutoff_date
        ).order_by(cls.analysis_time.desc()).all()
    
    @classmethod
    def get_high_confidence_analyses(cls, session, min_confidence: float = 0.8):
        """Get analyses with high confidence scores"""
        return session.query(cls).filter(
            cls.regime_confidence >= min_confidence
        ).order_by(cls.analysis_time.desc()).all()
    
    def validate_timeframe(self) -> bool:
        """Validate that the analysis timeframe is supported"""
        return RegimeAnalysisTimeframes.is_valid_timeframe(self.analysis_timeframe)
    
    def set_regime_from_enum(self, regime: MarketRegime) -> None:
        """Set current regime using MarketRegime enum"""
        self.current_regime = regime.value
    
    def set_timeframe_from_enum(self, timeframe: TimeframeEnum) -> None:
        """Set analysis timeframe using TimeframeEnum"""
        if timeframe.value in RegimeAnalysisTimeframes.VALID_TIMEFRAMES:
            self.analysis_timeframe = timeframe.value
        else:
            raise ValueError(f"Timeframe {timeframe.value} is not valid for regime analysis")
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'analysis_time': self.analysis_time.isoformat() if self.analysis_time else None,
            'analysis_timeframe': self.analysis_timeframe,
            'current_regime': self.current_regime,
            'predicted_regime': self.predicted_regime,
            'regime_confidence': float(self.regime_confidence) if self.regime_confidence else None,
            'regime_transition_prob': float(self.regime_transition_prob) if self.regime_transition_prob else None,
            'trend_strength_score': float(self.trend_strength_score) if self.trend_strength_score else None,
            'regime_quality_score': float(self.regime_quality_score) if self.regime_quality_score else None,
            'breakout_signal': self.breakout_signal,
            'volume_confirmation': self.volume_confirmation,
            'multi_timeframe_agreement': self.multi_timeframe_agreement,
            'recommended_strategy': self.recommended_strategy,
            'risk_adjustment_factor': float(self.risk_adjustment_factor) if self.risk_adjustment_factor else None,
            'ai_confidence_score': float(self.ai_confidence_score) if self.ai_confidence_score else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
