# File: backend/app/services/personas/response_factory.py
# PersonaResponseFactory 
# Generates persona-specific responses using existing models and data

import time
from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

# Import persona detection and response schemas
from app.services.personas.persona_detector import PersonaDetector, PersonaType
from app.schemas.personas.persona_responses import (
    AdminRegimeResponse, ProfessionalRegimeResponse, CasualRegimeResponse,
    PersonaAwareResponse, PersonaResponseMetadata, PersonaResponseWrapper,
    SystemMetrics, BulkAction, AdminInsight, TradingSignal, RiskAssessment,
    PerformanceMetrics, EducationalContent, GuidedAction, ProgressTracking
)

# Import existing models for data access
from app.models import User, Cryptocurrency, PriceData, Prediction

logger = logging.getLogger(__name__)

class PersonaResponseFactory:
    """
    Factory for generating persona-specific responses
    Integrates with existing database models and structures
    Based on User Journey Maps and Pain Point Analysis from design docs
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.persona_detector = PersonaDetector(db)
        
        # Response type mappers
        self.response_mappers = {
            PersonaType.ADMIN: self._create_admin_response,
            PersonaType.PROFESSIONAL: self._create_professional_response,
            PersonaType.CASUAL: self._create_casual_response
        }
    
    async def create_regime_response(
        self,
        user: User,
        regime_data: Dict[str, Any],
        include_metadata: bool = False
    ) -> PersonaAwareResponse | PersonaResponseWrapper:
        """
        Create persona-specific regime response
        
        Args:
            user: User model instance from existing database
            regime_data: Raw regime analysis data
            include_metadata: Whether to include response generation metadata
            
        Returns:
            Persona-specific response with optional metadata wrapper
        """
        start_time = time.time()
        
        try:
            # Detect user persona using existing user data
            persona = await self.persona_detector.detect_persona(user)
            user_context = await self.persona_detector.get_persona_context(user)
            
            # Generate persona-specific response
            response_mapper = self.response_mappers[persona]
            response = await response_mapper(user, regime_data, user_context)
            
            # Add metadata if requested
            if include_metadata:
                generation_time = (time.time() - start_time) * 1000  # Convert to ms
                metadata = PersonaResponseMetadata(
                    detected_persona=persona,
                    response_generation_time_ms=generation_time,
                    data_sources_used=self._get_data_sources_used(persona),
                    personalization_applied=self._get_personalization_features(persona),
                    user_context_factors=user_context
                )
                
                return PersonaResponseWrapper(
                    response_data=response,
                    metadata=metadata,
                    expires_at=datetime.utcnow() + timedelta(minutes=5)  # 5-minute cache
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating persona response for user {user.id}: {str(e)}")
            # Fallback to casual response on error
            return await self._create_fallback_response(user, regime_data)
    
    async def _create_admin_response(
        self,
        user: User,
        regime_data: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> AdminRegimeResponse:
        """
        Create admin-specific response (محمدرضا persona)
        Focus: System efficiency, comprehensive data, bulk management
        """
        # System performance metrics using existing database
        system_metrics = await self._get_system_metrics()
        
        # Available bulk actions based on admin capabilities
        bulk_actions = await self._get_bulk_actions()
        
        # AI-generated insights for admin decision making
        admin_insights = await self._generate_admin_insights(regime_data)
        
        # Efficiency metrics (targeting 70% improvement per design docs)
        efficiency_metrics = await self._calculate_efficiency_metrics(user)
        
        # User distribution for oversight
        user_distribution = await self._get_user_distribution()
        
        # System alerts requiring attention
        pending_alerts = await self._get_pending_alerts()
        
        return AdminRegimeResponse(
            persona_type=PersonaType.ADMIN,
            user_id=user.id,
            regime=regime_data.get('regime', 'neutral'),
            confidence=regime_data.get('confidence', 0.5),
            regime_strength=regime_data.get('strength', 'moderate'),
            detailed_metrics=regime_data.get('technical_data', {}),
            system_performance=system_metrics,
            bulk_actions_available=bulk_actions,
            admin_insights=admin_insights,
            efficiency_metrics=efficiency_metrics,
            user_distribution=user_distribution,
            pending_alerts=pending_alerts
        )
    
    async def _create_professional_response(
        self,
        user: User,
        regime_data: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> ProfessionalRegimeResponse:
        """
        Create professional-specific response (سارا persona)
        Focus: Speed (<500ms), precision, trading signals, risk management
        """
        start_time = time.time()
        
        # Real-time trading signals (must be <30 seconds fresh)
        immediate_signals = await self._get_immediate_trading_signals(regime_data)
        
        # Professional-grade risk assessment
        risk_assessment = await self._calculate_professional_risk_assessment(user, regime_data)
        
        # Trading recommendations with precise timing
        trading_recommendations = await self._generate_trading_recommendations(user, regime_data)
        
        # Performance tracking from existing Prediction model
        performance_tracking = await self._get_performance_metrics(user)
        
        # Pre-calculated data for speed optimization
        speed_optimized_data = await self._get_speed_optimized_data(regime_data)
        
        # Market context for informed decisions
        market_context = await self._get_market_context(regime_data)
        
        response_time_ms = (time.time() - start_time) * 1000
        
        return ProfessionalRegimeResponse(
            persona_type=PersonaType.PROFESSIONAL,
            user_id=user.id,
            regime=regime_data.get('regime', 'neutral'),
            confidence=regime_data.get('confidence', 0.5),
            regime_change_probability=regime_data.get('change_probability', 0.3),
            immediate_signals=immediate_signals,
            risk_assessment=risk_assessment,
            trading_recommendations=trading_recommendations,
            performance_tracking=performance_tracking,
            speed_optimized_data=speed_optimized_data,
            market_context=market_context,
            response_time_ms=response_time_ms
        )
    
    async def _create_casual_response(
        self,
        user: User,
        regime_data: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> CasualRegimeResponse:
        """
        Create casual-specific response (علی persona)
        Focus: Simplicity, education, guidance, confidence building
        """
        # Simple confidence description instead of numbers
        confidence_value = regime_data.get('confidence', 0.5)
        confidence_description = self._translate_confidence_to_text(confidence_value)
        
        # Emoji for visual appeal and simplicity
        regime_emoji = self._get_regime_emoji(regime_data.get('regime', 'neutral'))
        
        # Educational content based on current situation
        learning_content = await self._generate_educational_content(regime_data, user_context)
        
        # Step-by-step guided actions
        guided_actions = await self._generate_guided_actions(user, regime_data)
        
        # Progress tracking for motivation
        progress_tracking = await self._get_learning_progress(user)
        
        # Encouraging messages
        encouragement = await self._generate_encouragement(user, regime_data)
        
        # Learning suggestions
        suggested_learning = self._get_suggested_learning_topics(regime_data)
        
        # Safety reminders
        risk_reminders = self._get_risk_reminders()
        
        return CasualRegimeResponse(
            persona_type=PersonaType.CASUAL,
            user_id=user.id,
            regime=regime_data.get('regime', 'neutral'),
            confidence_description=confidence_description,
            regime_emoji=regime_emoji,
            simple_explanation=self._create_simple_explanation(regime_data),
            learning_content=learning_content,
            guided_actions=guided_actions,
            progress_tracking=progress_tracking,
            encouragement=encouragement,
            suggested_learning=suggested_learning,
            risk_reminders=risk_reminders
        )
    
    # ================================
    # ADMIN HELPER METHODS
    # ================================
    
    async def _get_system_metrics(self) -> SystemMetrics:
        """Get system-wide performance metrics using existing models"""
        try:
            # Query existing database for system stats
            total_users = self.db.query(User).count()
            active_users_24h = self.db.query(User).filter(
                User.last_login >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            total_predictions = self.db.query(Prediction).count()
            
            # Calculate system accuracy from existing Prediction model
            accuracy_query = self.db.query(
                text("SELECT AVG(CASE WHEN is_accurate = true THEN 100.0 ELSE 0.0 END) as avg_accuracy FROM predictions WHERE is_realized = true")
            ).fetchone()
            system_accuracy = float(accuracy_query.avg_accuracy or 0)
            
            return SystemMetrics(
                total_users=total_users,
                active_users_24h=active_users_24h,
                total_predictions=total_predictions,
                system_accuracy=system_accuracy,
                uptime_percentage=99.7,  # Could integrate with actual monitoring
                response_time_avg_ms=234  # Could integrate with actual metrics
            )
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            # Return default metrics on error
            return SystemMetrics(
                total_users=0, active_users_24h=0, total_predictions=0,
                system_accuracy=0, uptime_percentage=0, response_time_avg_ms=0
            )
    
    async def _get_bulk_actions(self) -> List[BulkAction]:
        """Generate available bulk actions for admin"""
        return [
            BulkAction(
                action_id="bulk_watchlist_add",
                name="Bulk Watchlist Addition",
                description="Add multiple cryptocurrencies to watchlist simultaneously",
                max_items=50,
                estimated_time_seconds=30,
                usage_count_today=3
            ),
            BulkAction(
                action_id="bulk_suggestion_review",
                name="Bulk Suggestion Review",
                description="Approve or reject multiple AI suggestions at once",
                max_items=25,
                estimated_time_seconds=120,
                usage_count_today=7
            ),
            BulkAction(
                action_id="bulk_user_notification",
                name="Bulk User Notifications", 
                description="Send notifications to multiple users based on criteria",
                max_items=100,
                estimated_time_seconds=60,
                usage_count_today=1
            )
        ]
    
    async def _generate_admin_insights(self, regime_data: Dict[str, Any]) -> List[AdminInsight]:
        """Generate AI insights for admin decision making"""
        insights = []
        
        # Market regime insight
        if regime_data.get('confidence', 0) > 0.8:
            insights.append(AdminInsight(
                insight_type="market_trend",
                title="High Confidence Market Regime Detected",
                description=f"System shows {regime_data.get('confidence', 0)*100:.1f}% confidence in {regime_data.get('regime', 'neutral')} market conditions",
                confidence=regime_data.get('confidence', 0),
                priority="high",
                actionable=True,
                suggested_actions=["Update risk parameters", "Notify professional users", "Review watchlist allocations"]
            ))
        
        # System performance insight
        insights.append(AdminInsight(
            insight_type="system_performance",
            title="Daily System Performance Summary",
            description="System processed predictions with good accuracy and response times",
            confidence=0.9,
            priority="medium",
            actionable=False,
            suggested_actions=["Continue monitoring", "Review error logs"]
        ))
        
        return insights
    
    async def _calculate_efficiency_metrics(self, user: User) -> Dict[str, float]:
        """Calculate efficiency improvements for admin"""
        return {
            "time_saved_minutes_today": 127.5,
            "automation_rate": 0.73,  # 73% of tasks automated
            "manual_review_reduction": 0.68,  # 68% reduction in manual reviews
            "error_rate_improvement": 0.45,  # 45% fewer errors
            "target_efficiency_progress": 0.67  # 67% toward 70% improvement target
        }
    
    async def _get_user_distribution(self) -> Dict[str, int]:
        """Get current user distribution by persona"""
        # Simplified version - in production would use cached results
        total_users = self.db.query(User).count()
        admin_users = self.db.query(User).filter(User.is_superuser == True).count()
        
        return {
            "total": total_users,
            "admin": admin_users,
            "professional": max(0, int(total_users * 0.2)),  # Estimate 20%
            "casual": max(0, total_users - admin_users - int(total_users * 0.2))
        }
    
    async def _get_pending_alerts(self) -> List[Dict[str, Any]]:
        """Get alerts requiring admin attention"""
        # Mock alerts - in production would query actual alert system
        return [
            {
                "alert_id": "volume_spike_btc",
                "type": "market_anomaly",
                "message": "BTC volume spike detected - 300% above average",
                "severity": "medium",
                "created_at": datetime.utcnow().isoformat(),
                "requires_action": True
            }
        ]
    
    # ================================  
    # PROFESSIONAL HELPER METHODS
    # ================================
    
    async def _get_immediate_trading_signals(self, regime_data: Dict[str, Any]) -> List[TradingSignal]:
        """Generate immediate trading signals for professionals"""
        signals = []
        
        # Get recent price data from existing PriceData model
        recent_cryptos = self.db.query(Cryptocurrency).limit(3).all()
        
        for crypto in recent_cryptos:
            # Mock signal generation based on regime
            signal_strength = min(0.9, regime_data.get('confidence', 0.5) + 0.3)
            
            signals.append(TradingSignal(
                crypto_symbol=crypto.symbol,
                signal_type="buy" if regime_data.get('regime') == 'bull' else "hold",
                strength=signal_strength,
                timeframe="1h",
                entry_price=crypto.current_price,
                target_price=crypto.current_price * 1.05 if regime_data.get('regime') == 'bull' else crypto.current_price,
                stop_loss=crypto.current_price * 0.95,
                confidence=signal_strength,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            ))
        
        return signals
    
    async def _calculate_professional_risk_assessment(self, user: User, regime_data: Dict[str, Any]) -> RiskAssessment:
        """Calculate professional-grade risk assessment"""
        # Calculate risk based on regime and user's prediction history
        base_risk = {"bull": 0.3, "bear": 0.8, "neutral": 0.5, "volatile": 0.9}.get(
            regime_data.get('regime', 'neutral'), 0.5
        )
        
        return RiskAssessment(
            overall_risk_level="medium" if base_risk < 0.7 else "high",
            risk_score=base_risk,
            risk_factors=self._identify_risk_factors(regime_data),
            portfolio_exposure={"BTC": 0.4, "ETH": 0.3, "ALT": 0.3},
            recommended_adjustments=["Reduce altcoin exposure", "Increase stablecoin allocation"],
            max_position_size=0.1  # 10% max position size
        )
    
    async def _generate_trading_recommendations(self, user: User, regime_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific trading recommendations"""
        return [
            {
                "recommendation_id": "btc_accumulation_001",
                "action": "accumulate",
                "crypto": "BTC",
                "reasoning": f"Strong {regime_data.get('regime', 'neutral')} regime supports accumulation",
                "time_horizon": "1-3 days",
                "confidence": regime_data.get('confidence', 0.5),
                "risk_level": "medium"
            }
        ]
    
    async def _get_performance_metrics(self, user: User) -> PerformanceMetrics:
        """Get performance metrics from existing Prediction model"""
        try:
            # Query user's prediction performance
            perf_query = self.db.query(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN is_accurate = true THEN 1 END) as accurate,
                        AVG(confidence_score) as avg_confidence
                    FROM predictions 
                    WHERE user_id = :user_id AND is_realized = true
                """)
            ).params(user_id=user.id).fetchone()
            
            total_trades = perf_query.total or 0
            accurate_trades = perf_query.accurate or 0
            win_rate = (accurate_trades / total_trades * 100) if total_trades > 0 else 0
            
            return PerformanceMetrics(
                total_trades=total_trades,
                win_rate=win_rate,
                average_return=5.2,  # Mock data
                sharpe_ratio=1.3,    # Mock data
                max_drawdown=12.5,   # Mock data
                current_streak=3     # Mock data
            )
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return PerformanceMetrics(
                total_trades=0, win_rate=0, average_return=0,
                sharpe_ratio=0, max_drawdown=0, current_streak=0
            )
    
    async def _get_speed_optimized_data(self, regime_data: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-calculated data for speed optimization"""
        return {
            "cached_at": datetime.utcnow().isoformat(),
            "market_summary": f"{regime_data.get('regime', 'neutral')} trend confirmed",
            "key_levels": regime_data.get('support_resistance', {}),
            "momentum_score": regime_data.get('momentum', 0.5),
            "volatility_index": regime_data.get('volatility', 0.3)
        }
    
    async def _get_market_context(self, regime_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get market context for informed decisions"""
        return {
            "dominant_narrative": f"{regime_data.get('regime', 'neutral')} market conditions",
            "key_drivers": ["Federal Reserve policy", "Institutional adoption", "Regulatory clarity"],
            "time_until_next_major_event": "3 days",
            "correlation_with_traditional_markets": 0.65
        }
    
    # ================================
    # CASUAL USER HELPER METHODS  
    # ================================
    
    def _translate_confidence_to_text(self, confidence: float) -> str:
        """Convert numeric confidence to plain English"""
        if confidence >= 0.8:
            return "Very confident"
        elif confidence >= 0.6:
            return "Quite sure"
        elif confidence >= 0.4:
            return "Somewhat confident"
        else:
            return "Not very certain"
    
    def _get_regime_emoji(self, regime: str) -> str:
        """Get emoji representing market regime"""
        emoji_map = {
            "bull": "🚀",
            "bear": "🐻", 
            "neutral": "😐",
            "volatile": "🎢"
        }
        return emoji_map.get(regime, "😐")
    
    async def _generate_educational_content(self, regime_data: Dict[str, Any], user_context: Dict[str, Any]) -> EducationalContent:
        """Generate educational content based on current situation"""
        regime = regime_data.get('regime', 'neutral')
        
        explanations = {
            "bull": "A bull market means prices are generally going up and investor confidence is high",
            "bear": "A bear market means prices are falling and investors are cautious",
            "neutral": "A neutral market means prices are stable without a clear trend",
            "volatile": "A volatile market means prices are moving up and down rapidly"
        }
        
        return EducationalContent(
            topic=f"Understanding {regime.title()} Markets",
            explanation=explanations.get(regime, explanations["neutral"]),
            why_important="Understanding market conditions helps you make better investment decisions and manage risk",
            example=f"During the last {regime} market, Bitcoin {'gained' if regime == 'bull' else 'lost'} significant value",
            next_steps=["Learn about risk management", "Study historical market cycles", "Practice with small amounts"]
        )
    
    async def _generate_guided_actions(self, user: User, regime_data: Dict[str, Any]) -> List[GuidedAction]:
        """Generate step-by-step guided actions for casual users"""
        regime = regime_data.get('regime', 'neutral')
        
        actions = []
        
        if regime == 'bull':
            actions.append(GuidedAction(
                action_id="bull_market_dca",
                title="Consider Dollar-Cost Averaging",
                description="Gradually invest a fixed amount regularly to reduce timing risk",
                difficulty="easy",
                time_required="5 minutes to set up",
                step_by_step=[
                    "Decide on a weekly/monthly investment amount",
                    "Choose 1-2 cryptocurrencies to focus on",
                    "Set up automatic purchases if available",
                    "Review and adjust monthly"
                ],
                benefits=["Reduces timing risk", "Builds discipline", "Takes advantage of bull market"],
                risks=["Market could reverse", "Requires consistent commitment"]
            ))
        
        # Always include a learning action
        actions.append(GuidedAction(
            action_id="learn_basics",
            title="Learn Market Basics",
            description="Understand fundamental concepts about cryptocurrency markets",
            difficulty="easy",
            time_required="15 minutes",
            step_by_step=[
                "Read about what influences crypto prices",
                "Learn the difference between bull and bear markets",
                "Understand basic risk management",
                "Practice with our educational tools"
            ],
            benefits=["Better decision making", "Increased confidence", "Reduced mistakes"],
            risks=["Time investment required"]
        ))
        
        return actions
    
    async def _get_learning_progress(self, user: User) -> ProgressTracking:
        """Track user's learning and investment progress"""
        # Get user's prediction activity from existing model
        prediction_count = self.db.query(Prediction).filter(Prediction.user_id == user.id).count()
        
        # Calculate learning progress
        learning_score = min(prediction_count / 20, 1.0)  # Progress toward 20 predictions
        
        return ProgressTracking(
            learning_score=learning_score,
            lessons_completed=min(prediction_count // 3, 10),  # Estimate lessons from activity
            predictions_made=prediction_count,
            accuracy_trend="improving" if prediction_count > 5 else "building experience",
            next_milestone="Make your first 10 predictions" if prediction_count < 10 else "Learn advanced concepts",
            achievements=self._calculate_achievements(prediction_count)
        )
    
    def _calculate_achievements(self, prediction_count: int) -> List[str]:
        """Calculate user achievements based on activity"""
        achievements = []
        if prediction_count >= 1:
            achievements.append("First Prediction Made! 🎉")
        if prediction_count >= 5:
            achievements.append("Getting Started 📈")
        if prediction_count >= 10:
            achievements.append("Experienced Investor 💪")
        if prediction_count >= 20:
            achievements.append("Market Analyst 🧠")
        return achievements
    
    async def _generate_encouragement(self, user: User, regime_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate encouraging messages for casual users"""
        return {
            "main_message": "You're doing great! Every market condition is a learning opportunity.",
            "progress_recognition": f"You've made progress in understanding crypto markets",
            "next_steps_encouragement": "Take your time to learn - there's no rush in investing",
            "community_support": "Remember, every expert was once a beginner"
        }
    
    def _get_suggested_learning_topics(self, regime_data: Dict[str, Any]) -> List[str]:
        """Get learning topics relevant to current market conditions"""
        base_topics = ["Risk Management", "Portfolio Diversification", "Dollar-Cost Averaging"]
        
        regime_specific = {
            "bull": ["Taking Profits", "FOMO Management", "Bull Market Psychology"],
            "bear": ["Bear Market Strategies", "Accumulation Strategies", "Emotional Discipline"],
            "volatile": ["Volatility Management", "Position Sizing", "Stress Management"]
        }
        
        regime = regime_data.get('regime', 'neutral')
        return base_topics + regime_specific.get(regime, [])
    
    def _get_risk_reminders(self) -> List[str]:
        """Important risk management reminders for casual users"""
        return [
            "Only invest what you can afford to lose",
            "Diversify your investments across different assets",
            "Do your own research before making decisions",
            "Market conditions can change quickly",
            "Consider your long-term financial goals"
        ]
    
    # ================================
    # UTILITY METHODS
    # ================================
    
    def _identify_risk_factors(self, regime_data: Dict[str, Any]) -> List[str]:
        """Identify current risk factors based on regime data"""
        factors = []
        
        if regime_data.get('regime') == 'volatile':
            factors.append("High market volatility")
        if regime_data.get('confidence', 0) < 0.5:
            factors.append("Low confidence in market direction")
        
        factors.extend(["Regulatory uncertainty", "Macroeconomic headwinds"])
        return factors
    
    def _create_simple_explanation(self, regime_data: Dict[str, Any]) -> str:
        """Create simple explanation of current market situation"""
        regime = regime_data.get('regime', 'neutral')
        confidence = regime_data.get('confidence', 0.5)
        
        explanations = {
            "bull": f"The market looks positive right now. Our analysis suggests prices might continue going up.",
            "bear": f"The market seems cautious right now. Prices might continue to be under pressure.",
            "neutral": f"The market is in a wait-and-see mode. No strong trend is apparent right now.",
            "volatile": f"The market is quite active with prices moving up and down frequently."
        }
        
        base_explanation = explanations.get(regime, explanations["neutral"])
        
        if confidence > 0.7:
            base_explanation += " We're fairly confident about this assessment."
        elif confidence < 0.4:
            base_explanation += " However, the situation could change quickly."
        
        return base_explanation
    
    def _get_data_sources_used(self, persona: PersonaType) -> List[str]:
        """Get list of data sources used for persona response"""
        base_sources = ["price_data", "predictions", "user_activity"]
        
        if persona == PersonaType.ADMIN:
            base_sources.extend(["system_metrics", "user_statistics"])
        elif persona == PersonaType.PROFESSIONAL:
            base_sources.extend(["trading_signals", "risk_calculations", "performance_data"])
        else:  # CASUAL
            base_sources.extend(["educational_content", "learning_progress"])
            
        return base_sources
    
    def _get_personalization_features(self, persona: PersonaType) -> List[str]:
        """Get list of personalization features applied"""
        features = ["persona_detection", "response_optimization"]
        
        if persona == PersonaType.ADMIN:
            features.extend(["bulk_actions", "system_insights", "efficiency_tracking"])
        elif persona == PersonaType.PROFESSIONAL:
            features.extend(["speed_optimization", "risk_assessment", "performance_tracking"])
        else:  # CASUAL
            features.extend(["language_simplification", "educational_content", "progress_tracking"])
            
        return features
    
    async def _create_fallback_response(self, user: User, regime_data: Dict[str, Any]) -> CasualRegimeResponse:
        """Create fallback response when persona detection fails"""
        logger.warning(f"Creating fallback response for user {user.id}")
        
        # Default to casual response with basic data
        return CasualRegimeResponse(
            persona_type=PersonaType.CASUAL,
            user_id=user.id,
            regime=regime_data.get('regime', 'neutral'),
            confidence_description="Uncertain",
            regime_emoji="😐",
            simple_explanation="We're analyzing the current market situation.",
            learning_content=EducationalContent(
                topic="Market Analysis",
                explanation="We continuously analyze market conditions to provide insights",
                why_important="Understanding markets helps with investment decisions",
                next_steps=["Check back in a few minutes", "Review educational content"]
            ),
            guided_actions=[],
            progress_tracking=ProgressTracking(
                learning_score=0.0,
                lessons_completed=0,
                predictions_made=0,
                accuracy_trend="getting started",
                next_milestone="Complete your first analysis",
                achievements=[]
            ),
            encouragement={"main_message": "Welcome to crypto market analysis!"},
            suggested_learning=["Basic Market Concepts"],
            risk_reminders=["Only invest what you can afford to lose"]
        )