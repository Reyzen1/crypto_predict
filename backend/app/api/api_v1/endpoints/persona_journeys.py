# File: backend/app/api/api_v1/endpoints/persona_journeys.py
# Journey-based API endpoints 
# Based on User Journey Maps from design documentation
# Compatible with existing API structure and authentication

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

# Import existing dependencies and models
from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_current_user
from app.models import User, Cryptocurrency, Prediction

# Import persona services and schemas
from app.services.personas.persona_detector import PersonaDetector, PersonaType
from app.services.personas.response_factory import PersonaResponseFactory
from app.schemas.personas.persona_responses import (
    AdminRegimeResponse, ProfessionalRegimeResponse, CasualRegimeResponse,
    PersonaAwareResponse, PersonaResponseWrapper
)
from app.schemas import SuccessResponse, CryptocurrencyResponse, PredictionResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# ========================================
# ADMIN JOURNEY ENDPOINTS (محمدرضا persona)  
# Journey: Entry → Watchlist Management → Suggestion Review → System Monitoring
# ========================================

@router.get(
    "/admin/dashboard",
    response_model=AdminRegimeResponse,
    summary="Admin Main Dashboard",
    description="Entry point for admin journey - System overview and management tools"
)
async def admin_dashboard(
    include_metadata: bool = Query(False, description="Include response generation metadata"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Admin Journey Entry Point (محمدرضا persona)
    
    Provides comprehensive system overview:
    - System performance metrics
    - Pending suggestions requiring review
    - Bulk action capabilities  
    - User distribution analytics
    - Efficiency tracking metrics
    
    Compatible with existing User model and database structure.
    """
    try:
        # Initialize persona services
        persona_detector = PersonaDetector(db)
        response_factory = PersonaResponseFactory(db)
        
        # Verify admin persona (uses existing User.is_superuser field)
        detected_persona = await persona_detector.detect_persona(current_user)
        if detected_persona != PersonaType.ADMIN:
            logger.warning(f"Non-admin user {current_user.id} attempted admin dashboard access")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required for this endpoint"
            )
        
        # Generate mock regime data (in production, this would come from Layer 1 AI)
        regime_data = await _get_current_regime_data(db)
        
        # Generate admin-specific response
        response = await response_factory.create_regime_response(
            user=current_user,
            regime_data=regime_data,
            include_metadata=include_metadata
        )
        
        logger.info(f"Admin dashboard accessed by user {current_user.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin dashboard endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate admin dashboard"
        )

@router.get(
    "/admin/suggestions/pending",
    response_model=Dict[str, Any],
    summary="Pending Suggestions Review",
    description="Admin journey step 2 - Review AI-generated suggestions requiring approval"
)
async def admin_pending_suggestions(
    limit: int = Query(25, ge=1, le=100, description="Maximum suggestions to return"),
    priority_filter: Optional[str] = Query(None, description="Filter by priority (high, medium, low)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Admin suggestion review workflow
    Addresses pain point: Manual review is time-consuming
    """
    try:
        # Verify admin access
        persona_detector = PersonaDetector(db)
        if await persona_detector.detect_persona(current_user) != PersonaType.ADMIN:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get pending suggestions (mock implementation - would integrate with AI suggestion system)
        pending_suggestions = await _get_pending_suggestions(db, limit, priority_filter)
        
        return {
            "total_pending": len(pending_suggestions),
            "suggestions": pending_suggestions,
            "bulk_actions_available": [
                "approve_all_high_confidence",
                "reject_all_low_confidence", 
                "update_priority_scores"
            ],
            "estimated_review_time_minutes": len(pending_suggestions) * 1.5,
            "time_saved_with_bulk_actions": len(pending_suggestions) * 0.8
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pending suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending suggestions")

@router.post(
    "/admin/watchlist/bulk_actions",
    response_model=SuccessResponse,
    summary="Execute Bulk Watchlist Actions", 
    description="Admin journey step 3 - Execute bulk operations on watchlist"
)
async def admin_bulk_watchlist_actions(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    action_type: str = Query(..., description="Action type (add, remove, update_tier)"),
    crypto_ids: List[int] = Query(..., description="List of cryptocurrency IDs"),
    target_tier: Optional[int] = Query(None, description="Target tier for updates")
):
    """
    Bulk watchlist management
    Addresses admin pain point: Bulk operations for efficiency
    """
    try:
        # Verify admin access and validate action
        persona_detector = PersonaDetector(db)
        if await persona_detector.detect_persona(current_user) != PersonaType.ADMIN:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if action_type not in ["add", "remove", "update_tier"]:
            raise HTTPException(status_code=400, detail="Invalid action type")
        
        # Validate crypto_ids exist in database
        existing_cryptos = db.query(Cryptocurrency).filter(
            Cryptocurrency.id.in_(crypto_ids)
        ).count()
        
        if existing_cryptos != len(crypto_ids):
            raise HTTPException(status_code=400, detail="Some cryptocurrency IDs not found")
        
        # Execute bulk action in background for better UX
        background_tasks.add_task(
            _execute_bulk_watchlist_action,
            db, action_type, crypto_ids, target_tier, current_user.id
        )
        
        logger.info(f"Bulk {action_type} action initiated by admin {current_user.id} for {len(crypto_ids)} cryptos")
        
        return SuccessResponse(
            message=f"Bulk {action_type} action initiated for {len(crypto_ids)} cryptocurrencies",
            data={
                "action_id": f"bulk_{action_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "affected_count": len(crypto_ids),
                "estimated_completion_seconds": len(crypto_ids) * 0.5,
                "status": "processing"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk watchlist action: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to execute bulk action")

# ========================================
# PROFESSIONAL JOURNEY ENDPOINTS (سارا persona)
# Journey: Entry → Multi-Layer Analysis → Signal Action → Performance Review
# ========================================

@router.get(
    "/professional/analysis/entry",
    response_model=ProfessionalRegimeResponse,
    summary="Professional Analysis Entry Point",
    description="Entry point for professional trader journey - Fast market analysis"
)
async def professional_analysis_entry(
    timeframe: str = Query("1h", description="Analysis timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
    include_signals: bool = Query(True, description="Include immediate trading signals"),
    speed_mode: bool = Query(True, description="Enable speed-optimized response"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Professional Journey Entry Point (سارا persona)
    
    Optimized for speed (<500ms requirement):
    - Real-time market regime analysis
    - Immediate trading signals
    - Risk assessment
    - Performance tracking
    
    Designed for high-frequency professional usage.
    """
    try:
        start_time = datetime.utcnow()
        
        # Initialize services with speed optimizations
        persona_detector = PersonaDetector(db)
        response_factory = PersonaResponseFactory(db)
        
        # Verify professional persona (or allow admin)
        detected_persona = await persona_detector.detect_persona(current_user)
        if detected_persona not in [PersonaType.PROFESSIONAL, PersonaType.ADMIN]:
            # Log access attempt but allow with degraded features
            logger.info(f"Non-professional user {current_user.id} accessing professional endpoint")
        
        # Get regime data with timeframe-specific analysis
        regime_data = await _get_regime_data_for_timeframe(db, timeframe, speed_mode)
        
        # Generate professional-specific response
        response = await response_factory.create_regime_response(
            user=current_user,
            regime_data=regime_data,
            include_metadata=False  # Skip metadata for speed
        )
        
        # Validate response time requirement (< 500ms for professionals)
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        if response_time > 500:
            logger.warning(f"Professional endpoint exceeded 500ms: {response_time}ms")
        
        # Add response time to professional response
        if isinstance(response, ProfessionalRegimeResponse):
            response.response_time_ms = response_time
        
        logger.info(f"Professional analysis provided to user {current_user.id} in {response_time:.1f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error in professional analysis endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate professional analysis"
        )

@router.get(
    "/professional/signals/realtime",
    response_model=Dict[str, Any],
    summary="Real-time Trading Signals",
    description="Professional journey step 2 - Get actionable trading signals"
)
async def professional_realtime_signals(
    asset_filter: Optional[str] = Query(None, description="Filter by asset (BTC, ETH, ALT)"),
    min_confidence: float = Query(0.6, ge=0.0, le=1.0, description="Minimum signal confidence"),
    signal_types: List[str] = Query(["buy", "sell", "hold"], description="Signal types to include"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Real-time trading signals for professional traders
    Updated every 30 seconds maximum for freshness
    """
    try:
        # Get latest signals (mock implementation - would integrate with signal generation system)
        signals = await _get_realtime_signals(db, asset_filter, min_confidence, signal_types)
        
        # Calculate signal statistics
        signal_stats = _calculate_signal_statistics(signals)
        
        return {
            "signals": signals,
            "statistics": signal_stats,
            "last_updated": datetime.utcnow().isoformat(),
            "next_update": (datetime.utcnow() + timedelta(seconds=30)).isoformat(),
            "signal_freshness_seconds": 15,  # Signals are 15 seconds old
            "total_opportunities": len(signals)
        }
        
    except Exception as e:
        logger.error(f"Error getting realtime signals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trading signals")

@router.get(
    "/professional/risk/assessment",
    response_model=Dict[str, Any],
    summary="Risk Assessment Analysis",
    description="Professional journey step 3 - Comprehensive risk analysis"
)
async def professional_risk_assessment(
    portfolio_snapshot: bool = Query(True, description="Include current portfolio risk"),
    scenario_analysis: bool = Query(False, description="Include scenario analysis"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Professional-grade risk assessment
    Addresses professional pain point: Need for sophisticated risk analysis
    """
    try:
        # Get user's trading history for risk calculation
        user_predictions = db.query(Prediction).filter(
            Prediction.user_id == current_user.id
        ).limit(100).all()
        
        # Calculate risk metrics from trading history
        risk_metrics = _calculate_risk_metrics(user_predictions)
        
        # Get current market risk factors
        market_risk_factors = await _get_market_risk_factors(db)
        
        # Portfolio risk analysis (if requested)
        portfolio_risk = {}
        if portfolio_snapshot:
            portfolio_risk = await _analyze_portfolio_risk(db, current_user.id)
        
        return {
            "overall_risk_score": risk_metrics["overall_score"],
            "risk_breakdown": risk_metrics["breakdown"],
            "market_risk_factors": market_risk_factors,
            "portfolio_risk": portfolio_risk,
            "risk_recommendations": risk_metrics["recommendations"],
            "risk_limits": {
                "max_position_size": 0.1,  # 10% max
                "daily_var": risk_metrics.get("daily_var", 0.02),
                "correlation_limit": 0.7
            },
            "last_calculated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in risk assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate risk assessment")

# ========================================
# CASUAL JOURNEY ENDPOINTS (علی persona)
# Journey: Entry → Simple Dashboard → Guided Decisions → Learning Progress
# ========================================

@router.get(
    "/casual/dashboard/simple",
    response_model=CasualRegimeResponse,
    summary="Simple Dashboard for Casual Users",
    description="Entry point for casual investor journey - Simplified market overview"
)
async def casual_simple_dashboard(
    show_learning: bool = Query(True, description="Include educational content"),
    guidance_level: str = Query("detailed", description="Guidance level (basic, detailed, comprehensive)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Casual Journey Entry Point (علی persona)
    
    Focused on simplicity and education:
    - Easy-to-understand market overview
    - Educational content
    - Guided next steps
    - Progress tracking
    - Risk awareness
    
    Designed to build confidence and knowledge.
    """
    try:
        # Initialize services
        persona_detector = PersonaDetector(db)
        response_factory = PersonaResponseFactory(db)
        
        # Get simplified regime data
        regime_data = await _get_simplified_regime_data(db)
        
        # Generate casual-specific response
        response = await response_factory.create_regime_response(
            user=current_user,
            regime_data=regime_data,
            include_metadata=False
        )
        
        # Ensure we got a casual response (should always be the case)
        if not isinstance(response, CasualRegimeResponse):
            logger.warning(f"Expected CasualRegimeResponse, got {type(response)} for user {current_user.id}")
        
        logger.info(f"Casual dashboard provided to user {current_user.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in casual dashboard endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate simple dashboard"
        )

@router.get(
    "/casual/education/guided",
    response_model=Dict[str, Any],
    summary="Guided Educational Content",
    description="Casual journey step 2 - Personalized learning content"
)
async def casual_guided_education(
    topic: Optional[str] = Query(None, description="Specific topic to learn about"),
    difficulty: str = Query("beginner", description="Difficulty level (beginner, intermediate)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Guided educational content for casual investors
    Addresses casual pain point: Lack of knowledge and confidence
    """
    try:
        # Get user's learning progress
        learning_progress = await _get_user_learning_progress(db, current_user.id)
        
        # Generate appropriate educational content
        educational_content = await _generate_educational_content(
            topic, difficulty, learning_progress
        )
        
        return {
            "current_lesson": educational_content["lesson"],
            "learning_objectives": educational_content["objectives"],
            "estimated_time_minutes": educational_content["time_estimate"],
            "difficulty_level": difficulty,
            "progress": learning_progress,
            "next_topics": educational_content["next_topics"],
            "practice_exercises": educational_content.get("exercises", []),
            "resources": educational_content.get("resources", [])
        }
        
    except Exception as e:
        logger.error(f"Error generating educational content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate educational content")

@router.get(
    "/casual/decisions/help",
    response_model=Dict[str, Any],
    summary="Decision Making Help",
    description="Casual journey step 3 - Get help with investment decisions"
)
async def casual_decision_help(
    decision_type: str = Query("investment", description="Type of decision (investment, sell, hold)"),
    risk_comfort: str = Query("conservative", description="Risk comfort level"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Decision-making assistance for casual users
    Provides step-by-step guidance and reduces anxiety
    """
    try:
        # Get user context for personalized advice
        user_context = await PersonaDetector(db).get_persona_context(current_user)
        
        # Generate decision guidance
        decision_guidance = await _generate_decision_guidance(
            decision_type, risk_comfort, user_context
        )
        
        return {
            "decision_framework": decision_guidance["framework"],
            "step_by_step_guide": decision_guidance["steps"],
            "things_to_consider": decision_guidance["considerations"],
            "red_flags": decision_guidance["warnings"],
            "confidence_builders": decision_guidance["confidence_tips"],
            "when_to_seek_help": decision_guidance["escalation_triggers"],
            "practice_scenarios": decision_guidance.get("practice", [])
        }
        
    except Exception as e:
        logger.error(f"Error generating decision help: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate decision guidance")

@router.get(
    "/casual/progress/tracking",
    response_model=Dict[str, Any],
    summary="Learning Progress Tracking",
    description="Casual journey step 4 - Track learning and investment progress"
)
async def casual_progress_tracking(
    timeframe: str = Query("all", description="Progress timeframe (week, month, all)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Progress tracking to motivate and guide casual users
    Shows achievements and next steps
    """
    try:
        # Get comprehensive progress data
        progress_data = await _get_comprehensive_progress(db, current_user.id, timeframe)
        
        return {
            "learning_progress": progress_data["learning"],
            "prediction_progress": progress_data["predictions"], 
            "achievements": progress_data["achievements"],
            "milestones": progress_data["milestones"],
            "areas_for_improvement": progress_data["improvement_areas"],
            "recommended_next_steps": progress_data["next_steps"],
            "encouragement": progress_data["encouragement"],
            "streak_data": progress_data["streaks"]
        }
        
    except Exception as e:
        logger.error(f"Error tracking progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track progress")

# ========================================
# UTILITY FUNCTIONS
# ========================================

async def _get_current_regime_data(db: Session) -> Dict[str, Any]:
    """Get current market regime data (mock implementation)"""
    # In production, this would integrate with Layer 1 AI system
    return {
        "regime": "bull",
        "confidence": 0.78,
        "strength": "moderate",
        "change_probability": 0.25,
        "technical_data": {
            "momentum": 0.65,
            "volatility": 0.42,
            "trend_strength": 0.71
        },
        "support_resistance": {
            "support": 45000,
            "resistance": 52000
        }
    }

async def _get_regime_data_for_timeframe(db: Session, timeframe: str, speed_mode: bool) -> Dict[str, Any]:
    """Get regime data optimized for specific timeframe and speed"""
    base_data = await _get_current_regime_data(db)
    
    # Add timeframe-specific adjustments
    timeframe_multipliers = {
        "1m": {"volatility": 1.2, "momentum": 0.9},
        "5m": {"volatility": 1.1, "momentum": 0.95},
        "15m": {"volatility": 1.0, "momentum": 1.0},
        "1h": {"volatility": 0.9, "momentum": 1.1},
        "4h": {"volatility": 0.8, "momentum": 1.2},
        "1d": {"volatility": 0.7, "momentum": 1.3}
    }
    
    multiplier = timeframe_multipliers.get(timeframe, {"volatility": 1.0, "momentum": 1.0})
    
    if "technical_data" in base_data:
        base_data["technical_data"]["volatility"] *= multiplier["volatility"]
        base_data["technical_data"]["momentum"] *= multiplier["momentum"]
    
    if speed_mode:
        # Add pre-calculated fields for speed
        base_data["speed_optimized"] = True
        base_data["cached_analysis"] = f"Analysis for {timeframe} timeframe"
    
    return base_data

async def _get_simplified_regime_data(db: Session) -> Dict[str, Any]:
    """Get simplified regime data for casual users"""
    base_data = await _get_current_regime_data(db)
    
    # Simplify the data structure
    return {
        "regime": base_data["regime"],
        "confidence": base_data["confidence"],
        "simple_trend": "prices going up" if base_data["regime"] == "bull" else "prices stable",
        "emoji_sentiment": "🚀" if base_data["regime"] == "bull" else "😐",
        "beginner_friendly": True
    }

async def _get_pending_suggestions(db: Session, limit: int, priority_filter: Optional[str]) -> List[Dict[str, Any]]:
    """Get pending AI suggestions for admin review (mock implementation)"""
    # Mock suggestions - in production would query suggestion system
    suggestions = [
        {
            "suggestion_id": "sugg_001",
            "crypto_symbol": "BTC",
            "action": "add_to_tier_1",
            "confidence": 0.87,
            "priority": "high",
            "reason": "Strong volume breakout detected",
            "created_at": datetime.utcnow().isoformat(),
            "requires_review": True
        },
        {
            "suggestion_id": "sugg_002", 
            "crypto_symbol": "ETH",
            "action": "move_to_tier_2",
            "confidence": 0.64,
            "priority": "medium", 
            "reason": "Momentum weakening slightly",
            "created_at": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
            "requires_review": True
        }
    ]
    
    # Apply priority filter if specified
    if priority_filter:
        suggestions = [s for s in suggestions if s["priority"] == priority_filter]
    
    return suggestions[:limit]

async def _execute_bulk_watchlist_action(
    db: Session, action_type: str, crypto_ids: List[int], target_tier: Optional[int], user_id: int
):
    """Execute bulk watchlist action in background"""
    try:
        # Mock implementation - in production would perform actual bulk operations
        logger.info(f"Executing bulk {action_type} for {len(crypto_ids)} cryptos by user {user_id}")
        
        # Simulate processing time
        import asyncio
        await asyncio.sleep(len(crypto_ids) * 0.1)
        
        logger.info(f"Bulk {action_type} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in bulk action execution: {str(e)}")

async def _get_realtime_signals(
    db: Session, asset_filter: Optional[str], min_confidence: float, signal_types: List[str]
) -> List[Dict[str, Any]]:
    """Get real-time trading signals (mock implementation)"""
    # Mock signals - in production would query signal generation system
    all_signals = [
        {
            "signal_id": "sig_001",
            "crypto_symbol": "BTC",
            "signal_type": "buy",
            "confidence": 0.84,
            "entry_price": 48500,
            "target_price": 51000,
            "stop_loss": 46000,
            "timeframe": "1h",
            "expires_in_minutes": 45
        },
        {
            "signal_id": "sig_002",
            "crypto_symbol": "ETH", 
            "signal_type": "hold",
            "confidence": 0.71,
            "entry_price": 3200,
            "target_price": None,
            "stop_loss": 3000,
            "timeframe": "4h",
            "expires_in_minutes": 180
        }
    ]
    
    # Apply filters
    filtered_signals = []
    for signal in all_signals:
        if signal["confidence"] >= min_confidence and signal["signal_type"] in signal_types:
            if not asset_filter or signal["crypto_symbol"] == asset_filter:
                filtered_signals.append(signal)
    
    return filtered_signals

def _calculate_signal_statistics(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics for trading signals"""
    if not signals:
        return {"total": 0, "by_type": {}, "avg_confidence": 0}
    
    by_type = {}
    total_confidence = 0
    
    for signal in signals:
        signal_type = signal["signal_type"]
        by_type[signal_type] = by_type.get(signal_type, 0) + 1
        total_confidence += signal["confidence"]
    
    return {
        "total": len(signals),
        "by_type": by_type,
        "avg_confidence": total_confidence / len(signals),
        "strongest_signal": max(signals, key=lambda x: x["confidence"]) if signals else None
    }

def _calculate_risk_metrics(user_predictions: List[Prediction]) -> Dict[str, Any]:
    """Calculate risk metrics from user's prediction history"""
    if not user_predictions:
        return {
            "overall_score": 0.5,
            "breakdown": {"market_risk": 0.5, "model_risk": 0.5},
            "recommendations": ["Start with small positions", "Learn risk management"]
        }
    
    # Calculate basic risk metrics from prediction history
    total_predictions = len(user_predictions)
    accurate_predictions = len([p for p in user_predictions if p.is_accurate])
    accuracy_rate = accurate_predictions / total_predictions if total_predictions > 0 else 0
    
    # Risk score based on accuracy and activity
    risk_score = max(0.2, 1.0 - accuracy_rate)
    
    return {
        "overall_score": risk_score,
        "breakdown": {
            "accuracy_based_risk": risk_score,
            "activity_risk": min(0.8, total_predictions / 100),
            "confidence_risk": 0.4  # Mock value
        },
        "recommendations": [
            "Review prediction accuracy",
            "Consider position sizing",
            "Monitor market correlation"
        ] if risk_score > 0.6 else ["Continue current approach"],
        "daily_var": risk_score * 0.05  # 5% max daily value at risk
    }

async def _get_market_risk_factors(db: Session) -> List[Dict[str, Any]]:
    """Get current market risk factors"""
    return [
        {
            "factor": "high_volatility",
            "impact": "medium",
            "description": "Market volatility above historical average",
            "mitigation": "Reduce position sizes"
        },
        {
            "factor": "regulatory_uncertainty", 
            "impact": "low",
            "description": "Ongoing regulatory developments",
            "mitigation": "Monitor news and compliance"
        }
    ]

async def _analyze_portfolio_risk(db: Session, user_id: int) -> Dict[str, Any]:
    """Analyze portfolio risk for a specific user"""
    # Mock implementation - would analyze user's actual portfolio
    return {
        "concentration_risk": "medium",
        "correlation_risk": "low",
        "liquidity_risk": "low",
        "recommendations": [
            "Consider diversifying beyond top 3 assets",
            "Monitor correlation between holdings"
        ]
    }

async def _get_user_learning_progress(db: Session, user_id: int) -> Dict[str, Any]:
    """Get user's learning progress"""
    # Calculate from user's activity in existing database
    prediction_count = db.query(Prediction).filter(Prediction.user_id == user_id).count()
    
    return {
        "lessons_completed": min(prediction_count // 3, 20),  # Estimate from activity
        "total_lessons": 20,
        "current_level": "beginner" if prediction_count < 10 else "intermediate",
        "strengths": ["Basic market understanding"],
        "areas_to_improve": ["Risk management", "Technical analysis"]
    }

async def _generate_educational_content(
    topic: Optional[str], difficulty: str, progress: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate educational content based on user needs"""
    content = {
        "lesson": {
            "title": "Understanding Market Cycles",
            "content": "Markets move in cycles of growth and decline. Learning to recognize these patterns helps make better investment decisions.",
            "key_concepts": ["Bull markets", "Bear markets", "Market psychology"],
            "examples": ["2017 crypto boom", "2018 crypto winter", "2020-2021 recovery"]
        },
        "objectives": [
            "Understand what causes market cycles",
            "Learn to identify different market phases", 
            "Develop appropriate strategies for each phase"
        ],
        "time_estimate": 15,
        "next_topics": ["Risk Management Basics", "Dollar-Cost Averaging", "Portfolio Diversification"],
        "exercises": [
            "Identify current market phase",
            "Practice with historical examples"
        ],
        "resources": [
            "Market cycle visualization tool",
            "Historical data explorer"
        ]
    }
    
    return content

async def _generate_decision_guidance(
    decision_type: str, risk_comfort: str, user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate decision-making guidance for casual users"""
    return {
        "framework": [
            "Assess your financial situation",
            "Define your investment goals",
            "Research the opportunity", 
            "Consider the risks",
            "Start small and learn"
        ],
        "steps": [
            "Review your budget - only invest what you can afford to lose",
            "Set clear goals - are you saving for long-term or short-term?",
            "Research the cryptocurrency and its fundamentals",
            "Understand the risks involved",
            "Make a small initial investment to gain experience"
        ],
        "considerations": [
            "Your risk tolerance level",
            "Time horizon for investment",
            "Current portfolio diversification",
            "Market conditions",
            "Personal financial stability"
        ],
        "warnings": [
            "Investing more than you can afford to lose",
            "Making decisions based on emotions",
            "Following others without research",
            "Expecting guaranteed returns"
        ],
        "confidence_tips": [
            "Start with small amounts",
            "Learn from each decision",
            "Keep detailed records",
            "Celebrate small wins"
        ],
        "escalation_triggers": [
            "Feeling overwhelmed or stressed",
            "Considering large investments",
            "Facing significant losses",
            "Unsure about tax implications"
        ]
    }

async def _get_comprehensive_progress(
    db: Session, user_id: int, timeframe: str
) -> Dict[str, Any]:
    """Get comprehensive progress data for casual users"""
    # Get user's prediction activity
    prediction_count = db.query(Prediction).filter(Prediction.user_id == user_id).count()
    
    return {
        "learning": {
            "lessons_completed": min(prediction_count // 2, 15),
            "concepts_mastered": ["Basic market understanding"],
            "progress_percentage": min(prediction_count / 20 * 100, 100)
        },
        "predictions": {
            "total_made": prediction_count,
            "accuracy_improving": prediction_count > 5,
            "best_streak": max(3, prediction_count // 10)
        },
        "achievements": [
            "First prediction made! 🎉" if prediction_count >= 1 else None,
            "Getting consistent 📈" if prediction_count >= 5 else None,
            "Market analyst 🧠" if prediction_count >= 20 else None
        ],
        "milestones": {
            "next_milestone": f"Make {max(1, (prediction_count // 5 + 1) * 5)} predictions",
            "progress_to_next": prediction_count % 5,
            "milestone_reward": "Unlock advanced features"
        },
        "improvement_areas": [
            "Risk management understanding",
            "Market timing skills", 
            "Portfolio diversification"
        ],
        "next_steps": [
            "Complete risk assessment lesson",
            "Try dollar-cost averaging strategy",
            "Learn about portfolio balance"
        ],
        "encouragement": {
            "message": f"Great progress! You've made {prediction_count} predictions and are building valuable experience.",
            "motivation": "Every expert was once a beginner. Keep learning and growing!",
            "next_achievement": "You're on track to become a confident investor"
        },
        "streaks": {
            "current_learning_streak": min(prediction_count, 7),
            "longest_streak": min(prediction_count, 12),
            "streak_goal": 30
        }
    }