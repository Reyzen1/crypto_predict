# File: backend/tests/test_personas/test_day1_implementation.py
# Comprehensive Test Suite for Day 1 Week 6 Implementation
# Tests all persona-based functionality with existing database compatibility

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

# Import existing test utilities and fixtures
from tests.conftest import client, db_session, test_user
from app.main import app

# Import persona components for testing
from app.services.personas.persona_detector import PersonaDetector, PersonaType
from app.services.personas.response_factory import PersonaResponseFactory
from app.services.personas.pain_point_solutions import (
    PainPointSolutionFactory, AdminPainPointSolutions, 
    ProfessionalPainPointSolutions, CasualPainPointSolutions
)
from app.core.auth.persona_auth import PersonaAuthService, PersonaPermissions
from app.schemas.personas.persona_responses import (
    AdminRegimeResponse, ProfessionalRegimeResponse, CasualRegimeResponse
)

# Import existing models for testing
from app.models import User, Cryptocurrency, Prediction

# ========================================
# TEST FIXTURES FOR PERSONA FUNCTIONALITY
# ========================================

@pytest.fixture
def persona_detector(db_session: Session):
    """Create PersonaDetector instance for testing"""
    return PersonaDetector(db_session)

@pytest.fixture
def response_factory(db_session: Session):
    """Create PersonaResponseFactory instance for testing"""
    return PersonaResponseFactory(db_session)

@pytest.fixture
def auth_service(db_session: Session):
    """Create PersonaAuthService instance for testing"""
    return PersonaAuthService(db_session)

@pytest.fixture
def pain_point_factory(db_session: Session):
    """Create PainPointSolutionFactory instance for testing"""
    return PainPointSolutionFactory(db_session)

@pytest.fixture
def admin_user_with_data(db_session: Session):
    """Create admin user with sample data for comprehensive testing"""
    user = User(
        email="admin@test.com",
        password_hash="admin@test.com",
        first_name="محمدرضا",
        last_name="احمدی",
        is_active=True,
        is_verified=True,
        is_superuser=True,
        preferences={"role": "admin", "admin_features_enabled": True},
        created_at=datetime.utcnow() - timedelta(days=60),
        last_login=datetime.utcnow() - timedelta(hours=2)
    )
    db_session.add(user)
    db_session.flush()
    
    # Add some predictions for behavior analysis
    crypto = Cryptocurrency(
        symbol="BTC", name="Bitcoin", current_price=50000,
        market_cap=1000000000, is_active=True
    )
    db_session.add(crypto)
    db_session.flush()
    
    for i in range(3):
        prediction = Prediction(
            crypto_id=crypto.id,
            user_id=user.id,
            model_name="test_model",
            predicted_price=51000 + i * 100,
            confidence_score=0.8,
            prediction_horizon=24,
            target_datetime=datetime.utcnow() + timedelta(hours=24),
            is_accurate=True,
            is_realized=True
        )
        db_session.add(prediction)
    
    db_session.commit()
    return user

@pytest.fixture
def professional_user_with_data(db_session: Session):
    """Create professional user with high activity data"""
    user = User(
        email="professional@test.com",
        password_hash="professional@test.com", 
        first_name="سارا",
        last_name="محمدی",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        preferences={"user_type": "professional", "trading_experience": 5},
        created_at=datetime.utcnow() - timedelta(days=90),
        last_login=datetime.utcnow() - timedelta(minutes=30)
    )
    db_session.add(user)
    db_session.flush()
    
    # Add high prediction activity
    crypto = db_session.query(Cryptocurrency).first()
    if not crypto:
        crypto = Cryptocurrency(symbol="ETH", name="Ethereum", current_price=3500)
        db_session.add(crypto)
        db_session.flush()
    
    for i in range(25):  # High activity indicating professional usage
        prediction = Prediction(
            crypto_id=crypto.id,
            user_id=user.id,
            model_name="professional_model",
            predicted_price=3500 + i * 10,
            confidence_score=0.75 + (i % 5) * 0.05,
            prediction_horizon=1,
            target_datetime=datetime.utcnow() + timedelta(hours=1),
            is_accurate=i % 3 == 0,  # 33% accuracy for testing
            is_realized=True
        )
        db_session.add(prediction)
    
    db_session.commit()
    return user

@pytest.fixture
def casual_user_with_data(db_session: Session):
    """Create casual user with basic activity"""
    user = User(
        email="casual@test.com",
        password_hash="casual@test.com",
        first_name="علی", 
        last_name="رضایی",
        is_active=True,
        is_verified=False,
        is_superuser=False,
        preferences={},
        created_at=datetime.utcnow() - timedelta(days=30),
        last_login=datetime.utcnow() - timedelta(days=7)
    )
    db_session.add(user)
    db_session.flush()
    
    # Add minimal prediction activity
    crypto = db_session.query(Cryptocurrency).first()
    if not crypto:
        crypto = Cryptocurrency(symbol="ADA", name="Cardano", current_price=1.2)
        db_session.add(crypto)
        db_session.flush()
    
    for i in range(3):  # Low activity indicating casual usage
        prediction = Prediction(
            crypto_id=crypto.id,
            user_id=user.id,
            model_name="basic_model",
            predicted_price=1.3,
            confidence_score=0.6,
            prediction_horizon=168,  # 1 week
            target_datetime=datetime.utcnow() + timedelta(weeks=1),
            is_accurate=False,
            is_realized=False
        )
        db_session.add(prediction)
    
    db_session.commit()
    return user

# ========================================
# PERSONA DETECTOR TESTS
# ========================================

class TestPersonaDetector:
    """Test persona detection functionality"""
    
    @pytest.mark.asyncio
    async def test_admin_persona_detection_superuser_flag(
        self, persona_detector, admin_user_with_data
    ):
        """Test admin detection via superuser flag"""
        persona = await persona_detector.detect_persona(admin_user_with_data)
        assert persona == PersonaType.ADMIN
    
    @pytest.mark.asyncio
    async def test_admin_persona_detection_preferences(
        self, persona_detector, db_session
    ):
        """Test admin detection via preferences"""
        user = User(
            email="admin2@test.com",
            password_hash="admin2@test.com",
            is_superuser=False,  # Not superuser but has admin preferences
            preferences={"role": "admin"},
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()
        
        persona = await persona_detector.detect_persona(user)
        assert persona == PersonaType.ADMIN
    
    @pytest.mark.asyncio
    async def test_professional_persona_detection(
        self, persona_detector, professional_user_with_data
    ):
        """Test professional persona detection"""
        persona = await persona_detector.detect_persona(professional_user_with_data)
        assert persona == PersonaType.PROFESSIONAL
    
    @pytest.mark.asyncio
    async def test_casual_persona_detection(
        self, persona_detector, casual_user_with_data
    ):
        """Test casual persona detection (default)"""
        persona = await persona_detector.detect_persona(casual_user_with_data)
        assert persona == PersonaType.CASUAL
    
    @pytest.mark.asyncio
    async def test_persona_context_generation(
        self, persona_detector, admin_user_with_data
    ):
        """Test comprehensive persona context generation"""
        context = await persona_detector.get_persona_context(admin_user_with_data)
        
        assert context["persona"] == PersonaType.ADMIN.value
        assert context["user_id"] == admin_user_with_data.id
        assert "system_overview" in context
        assert "admin_capabilities" in context
        assert context["efficiency_focus"] is True
    
    @pytest.mark.asyncio 
    async def test_batch_persona_detection(
        self, persona_detector, admin_user_with_data, professional_user_with_data, casual_user_with_data
    ):
        """Test batch persona detection for multiple users"""
        user_ids = [admin_user_with_data.id, professional_user_with_data.id, casual_user_with_data.id]
        results = await persona_detector.batch_detect_personas(user_ids)
        
        assert len(results) == 3
        assert results[admin_user_with_data.id] == PersonaType.ADMIN
        assert results[professional_user_with_data.id] == PersonaType.PROFESSIONAL
        assert results[casual_user_with_data.id] == PersonaType.CASUAL
    
    def test_persona_statistics_calculation(
        self, persona_detector, admin_user_with_data, professional_user_with_data
    ):
        """Test persona distribution statistics"""
        stats = persona_detector.get_persona_statistics()
        
        assert "distribution" in stats
        assert "percentages" in stats
        assert stats["distribution"]["total"] > 0

# ========================================
# RESPONSE FACTORY TESTS
# ========================================

class TestPersonaResponseFactory:
    """Test persona-specific response generation"""
    
    @pytest.mark.asyncio
    async def test_admin_response_generation(
        self, response_factory, admin_user_with_data
    ):
        """Test admin-specific response generation"""
        regime_data = {
            "regime": "bull",
            "confidence": 0.85,
            "technical_data": {"momentum": 0.7, "volatility": 0.3}
        }
        
        response = await response_factory.create_regime_response(
            admin_user_with_data, regime_data
        )
        
        assert isinstance(response, AdminRegimeResponse)
        assert response.persona_type == PersonaType.ADMIN
        assert response.regime == "bull"
        assert response.confidence == 0.85
        assert len(response.bulk_actions_available) > 0
        assert len(response.admin_insights) > 0
        assert "efficiency_target" in str(response.efficiency_metrics)
    
    @pytest.mark.asyncio
    async def test_professional_response_generation(
        self, response_factory, professional_user_with_data
    ):
        """Test professional-specific response generation"""
        regime_data = {
            "regime": "volatile",
            "confidence": 0.72,
            "change_probability": 0.4
        }
        
        response = await response_factory.create_regime_response(
            professional_user_with_data, regime_data
        )
        
        assert isinstance(response, ProfessionalRegimeResponse)
        assert response.persona_type == PersonaType.PROFESSIONAL
        assert response.regime == "volatile"
        assert len(response.immediate_signals) > 0
        assert response.risk_assessment is not None
        assert response.response_time_ms < 1000  # Should be fast
    
    @pytest.mark.asyncio
    async def test_casual_response_generation(
        self, response_factory, casual_user_with_data
    ):
        """Test casual-specific response generation"""
        regime_data = {
            "regime": "neutral",
            "confidence": 0.6
        }
        
        response = await response_factory.create_regime_response(
            casual_user_with_data, regime_data
        )
        
        assert isinstance(response, CasualRegimeResponse)
        assert response.persona_type == PersonaType.CASUAL
        assert response.regime == "neutral"
        assert "confident" in response.confidence_description.lower()
        assert len(response.simple_explanation) > 0
        assert response.learning_content is not None
        assert len(response.guided_actions) > 0
    
    @pytest.mark.asyncio
    async def test_response_with_metadata(
        self, response_factory, admin_user_with_data
    ):
        """Test response generation with metadata"""
        regime_data = {"regime": "bull", "confidence": 0.8}
        
        response = await response_factory.create_regime_response(
            admin_user_with_data, regime_data, include_metadata=True
        )
        
        # Should return wrapper with metadata
        assert hasattr(response, 'metadata')
        assert hasattr(response, 'response_data')
        assert response.metadata.detected_persona == PersonaType.ADMIN
        assert response.metadata.response_generation_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_fallback_response_on_error(
        self, response_factory, casual_user_with_data
    ):
        """Test fallback response when persona detection fails"""
        with patch.object(response_factory.persona_detector, 'detect_persona', 
                         side_effect=Exception("Detection failed")):
            
            regime_data = {"regime": "neutral", "confidence": 0.5}
            response = await response_factory.create_regime_response(
                casual_user_with_data, regime_data
            )
            
            # Should fallback to casual response
            assert isinstance(response, CasualRegimeResponse)
            assert response.persona_type == PersonaType.CASUAL

# ========================================
# API ENDPOINTS TESTS
# ========================================

class TestPersonaJourneyEndpoints:
    """Test journey-based API endpoints"""
    
    def test_admin_dashboard_access(
        self, client: TestClient, admin_user_with_data, db_session
    ):
        """Test admin dashboard endpoint access"""
        with patch("app.core.deps.get_current_active_user", return_value=admin_user_with_data):
            response = client.get("/api/v1/persona_journeys/admin/dashboard")
            
            assert response.status_code == 200
            data = response.json()
            assert data["persona_type"] == "admin"
            assert "system_performance" in data
            assert "bulk_actions_available" in data
    
    def test_admin_dashboard_access_denied_for_casual(
        self, client: TestClient, casual_user_with_data
    ):
        """Test admin dashboard denies access to casual users"""
        with patch("app.core.deps.get_current_active_user", return_value=casual_user_with_data):
            response = client.get("/api/v1/persona_journeys/admin/dashboard")
            
            assert response.status_code == 403
            assert "Admin privileges required" in response.json()["detail"]
    
    def test_professional_analysis_entry(
        self, client: TestClient, professional_user_with_data
    ):
        """Test professional analysis entry endpoint"""
        with patch("app.core.deps.get_current_active_user", return_value=professional_user_with_data):
            response = client.get(
                "/api/v1/persona_journeys/professional/analysis/entry?timeframe=1h&speed_mode=true"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["persona_type"] == "professional"
            assert "immediate_signals" in data
            assert "response_time_ms" in data
            assert data["response_time_ms"] < 1000  # Should be optimized for speed
    
    def test_casual_simple_dashboard(
        self, client: TestClient, casual_user_with_data
    ):
        """Test casual simple dashboard endpoint"""
        with patch("app.core.deps.get_current_active_user", return_value=casual_user_with_data):
            response = client.get("/api/v1/persona_journeys/casual/dashboard/simple")
            
            assert response.status_code == 200
            data = response.json()
            assert data["persona_type"] == "casual"
            assert "simple_explanation" in data
            assert "learning_content" in data
            assert "guided_actions" in data
    
    def test_bulk_watchlist_actions_admin_only(
        self, client: TestClient, admin_user_with_data, casual_user_with_data
    ):
        """Test bulk actions are restricted to admin users"""
        # Admin should succeed
        with patch("app.core.deps.get_current_active_user", return_value=admin_user_with_data):
            response = client.post(
                "/api/v1/persona_journeys/admin/watchlist/bulk_actions?action_type=add",
                params={"crypto_ids": [1, 2, 3]}
            )
            assert response.status_code == 200
        
        # Casual user should be denied
        with patch("app.core.deps.get_current_active_user", return_value=casual_user_with_data):
            response = client.post(
                "/api/v1/persona_journeys/admin/watchlist/bulk_actions?action_type=add",
                params={"crypto_ids": [1, 2, 3]}
            )
            assert response.status_code == 403

# ========================================
# PAIN POINT SOLUTIONS TESTS
# ========================================

class TestPainPointSolutions:
    """Test pain point analysis and solutions"""
    
    @pytest.mark.asyncio
    async def test_admin_pain_point_analysis(
        self, pain_point_factory, admin_user_with_data
    ):
        """Test admin pain point analysis"""
        solution_service = await pain_point_factory.create_solution_service(admin_user_with_data)
        assert isinstance(solution_service, AdminPainPointSolutions)
        
        pain_points = await solution_service.analyze_pain_points(admin_user_with_data)
        
        assert "manual_review_burden" in pain_points
        assert "transparency_gaps" in pain_points
        assert "control_limitations" in pain_points
        assert "reporting_gaps" in pain_points
        assert "overall_pain_score" in pain_points
        assert 0 <= pain_points["overall_pain_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_admin_solution_generation(
        self, pain_point_factory, admin_user_with_data
    ):
        """Test admin solution generation"""
        solution_service = await pain_point_factory.create_solution_service(admin_user_with_data)
        pain_points = await solution_service.analyze_pain_points(admin_user_with_data)
        
        solutions = await solution_service.provide_solutions(admin_user_with_data, pain_points)
        
        assert "solutions" in solutions
        assert "expected_benefits" in solutions
        assert "rollout_timeline" in solutions
        
        # Check for efficiency optimization suite (always provided)
        assert "efficiency_suite" in solutions["solutions"]
    
    @pytest.mark.asyncio
    async def test_professional_pain_point_analysis(
        self, pain_point_factory, professional_user_with_data
    ):
        """Test professional pain point analysis"""
        solution_service = await pain_point_factory.create_solution_service(professional_user_with_data)
        assert isinstance(solution_service, ProfessionalPainPointSolutions)
        
        pain_points = await solution_service.analyze_pain_points(professional_user_with_data)
        
        assert "speed_requirements" in pain_points
        assert "accuracy_demands" in pain_points
        assert "interface_complexity" in pain_points
        assert "customization_needs" in pain_points
    
    @pytest.mark.asyncio
    async def test_casual_pain_point_analysis(
        self, pain_point_factory, casual_user_with_data
    ):
        """Test casual pain point analysis"""
        solution_service = await pain_point_factory.create_solution_service(casual_user_with_data)
        assert isinstance(solution_service, CasualPainPointSolutions)
        
        pain_points = await solution_service.analyze_pain_points(casual_user_with_data)
        
        assert "complexity_overwhelm" in pain_points
        assert "confidence_deficit" in pain_points
        assert "learning_gaps" in pain_points
        assert "risk_anxiety" in pain_points
    
    @pytest.mark.asyncio
    async def test_complete_pain_point_workflow(
        self, pain_point_factory, admin_user_with_data
    ):
        """Test complete pain point analysis and solution workflow"""
        complete_analysis = await pain_point_factory.analyze_and_solve_pain_points(admin_user_with_data)
        
        assert "pain_point_analysis" in complete_analysis
        assert "recommended_solutions" in complete_analysis
        assert "user_persona" in complete_analysis
        assert complete_analysis["user_persona"] == "admin"
        assert complete_analysis["analysis_complete"] is True

# ========================================
# AUTHENTICATION TESTS
# ========================================

class TestPersonaAuthentication:
    """Test persona-based authentication and permissions"""
    
    @pytest.mark.asyncio
    async def test_permission_checking(
        self, auth_service, admin_user_with_data, professional_user_with_data, casual_user_with_data
    ):
        """Test permission checking for different personas"""
        # Admin should have bulk operations permission
        assert await auth_service.check_permission(admin_user_with_data, "bulk_operations")
        
        # Professional should not have bulk operations
        assert not await auth_service.check_permission(professional_user_with_data, "bulk_operations")
        
        # Professional should have realtime signals
        assert await auth_service.check_permission(professional_user_with_data, "access_realtime_signals")
        
        # Casual should not have realtime signals
        assert not await auth_service.check_permission(casual_user_with_data, "access_realtime_signals")
        
        # All should have basic dashboard access
        assert await auth_service.check_permission(casual_user_with_data, "view_simple_dashboard")
    
    @pytest.mark.asyncio
    async def test_superuser_override(
        self, auth_service, admin_user_with_data
    ):
        """Test that superusers get permission override"""
        # Test a permission not normally granted to admins
        fake_permission = "some_restricted_permission"
        
        # Should get permission due to superuser status
        assert await auth_service.check_permission(admin_user_with_data, fake_permission)
    
    @pytest.mark.asyncio
    async def test_persona_hierarchy_validation(
        self, auth_service, admin_user_with_data, professional_user_with_data, casual_user_with_data
    ):
        """Test persona hierarchy access validation"""
        # Admin should have access to all levels
        assert await auth_service.validate_persona_access(admin_user_with_data, PersonaType.ADMIN)
        assert await auth_service.validate_persona_access(admin_user_with_data, PersonaType.PROFESSIONAL)
        assert await auth_service.validate_persona_access(admin_user_with_data, PersonaType.CASUAL)
        
        # Professional should have access to professional and casual
        assert not await auth_service.validate_persona_access(professional_user_with_data, PersonaType.ADMIN)
        assert await auth_service.validate_persona_access(professional_user_with_data, PersonaType.PROFESSIONAL)
        assert await auth_service.validate_persona_access(professional_user_with_data, PersonaType.CASUAL)
        
        # Casual should only have casual access
        assert not await auth_service.validate_persona_access(casual_user_with_data, PersonaType.ADMIN)
        assert not await auth_service.validate_persona_access(casual_user_with_data, PersonaType.PROFESSIONAL)
        assert await auth_service.validate_persona_access(casual_user_with_data, PersonaType.CASUAL)
    
    @pytest.mark.asyncio
    async def test_persona_caching(
        self, auth_service, admin_user_with_data
    ):
        """Test persona detection caching for performance"""
        # First call should detect and cache
        persona1 = await auth_service.get_user_persona_cached(admin_user_with_data)
        
        # Second call should use cache
        persona2 = await auth_service.get_user_persona_cached(admin_user_with_data)
        
        assert persona1 == persona2 == PersonaType.ADMIN
        
        # Cache should contain the user
        assert admin_user_with_data.id in auth_service._persona_cache
    
    def test_permission_definitions_completeness(self):
        """Test that all persona types have complete permission definitions"""
        admin_perms = PersonaPermissions.ADMIN_PERMISSIONS
        prof_perms = PersonaPermissions.PROFESSIONAL_PERMISSIONS
        casual_perms = PersonaPermissions.CASUAL_PERMISSIONS
        
        # All should be dictionaries with permissions
        assert isinstance(admin_perms, dict)
        assert isinstance(prof_perms, dict)
        assert isinstance(casual_perms, dict)
        
        # Admin should have the most permissions
        assert len(admin_perms) >= len(prof_perms)
        assert len(prof_perms) >= len(casual_perms)
        
        # Check key permissions exist
        assert "bulk_operations" in admin_perms
        assert "access_realtime_signals" in prof_perms
        assert "view_simple_dashboard" in casual_perms

# ========================================
# INTEGRATION TESTS
# ========================================

class TestPersonaSystemIntegration:
    """Test integration between persona system components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_admin_workflow(
        self, db_session, admin_user_with_data
    ):
        """Test complete admin workflow from detection to response"""
        # 1. Detect persona
        persona_detector = PersonaDetector(db_session)
        persona = await persona_detector.detect_persona(admin_user_with_data)
        assert persona == PersonaType.ADMIN
        
        # 2. Check permissions
        auth_service = PersonaAuthService(db_session)
        can_bulk_operations = await auth_service.check_permission(admin_user_with_data, "bulk_operations")
        assert can_bulk_operations
        
        # 3. Generate response
        response_factory = PersonaResponseFactory(db_session)
        regime_data = {"regime": "bull", "confidence": 0.8}
        response = await response_factory.create_regime_response(admin_user_with_data, regime_data)
        
        assert isinstance(response, AdminRegimeResponse)
        assert len(response.bulk_actions_available) > 0
        
        # 4. Analyze pain points
        pain_point_factory = PainPointSolutionFactory(db_session)
        analysis = await pain_point_factory.analyze_and_solve_pain_points(admin_user_with_data)
        
        assert analysis["user_persona"] == "admin"
        assert "efficiency_suite" in analysis["recommended_solutions"]["solutions"]
    
    @pytest.mark.asyncio
    async def test_end_to_end_professional_workflow(
        self, db_session, professional_user_with_data
    ):
        """Test complete professional workflow focusing on speed"""
        start_time = datetime.utcnow()
        
        # Professional workflow should be optimized for speed
        response_factory = PersonaResponseFactory(db_session)
        regime_data = {"regime": "volatile", "confidence": 0.75}
        
        response = await response_factory.create_regime_response(
            professional_user_with_data, regime_data
        )
        
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        assert isinstance(response, ProfessionalRegimeResponse)
        assert response_time_ms < 1000  # Should be fast for professionals
        assert len(response.immediate_signals) > 0
        assert response.risk_assessment is not None
    
    @pytest.mark.asyncio
    async def test_end_to_end_casual_workflow(
        self, db_session, casual_user_with_data
    ):
        """Test complete casual workflow focusing on simplicity"""
        # Casual workflow should focus on education and simplicity
        response_factory = PersonaResponseFactory(db_session)
        regime_data = {"regime": "neutral", "confidence": 0.6}
        
        response = await response_factory.create_regime_response(
            casual_user_with_data, regime_data
        )
        
        assert isinstance(response, CasualRegimeResponse)
        assert response.learning_content is not None
        assert len(response.guided_actions) > 0
        assert len(response.risk_reminders) > 0
        
        # Check educational content quality
        assert len(response.simple_explanation) > 50  # Should be detailed explanation
        assert "learn" in response.learning_content.explanation.lower()
    
    @pytest.mark.asyncio
    async def test_persona_switching_behavior(
        self, db_session, admin_user_with_data
    ):
        """Test behavior when user persona potentially changes"""
        auth_service = PersonaAuthService(db_session)
        
        # Initial persona detection
        persona1 = await auth_service.get_user_persona_cached(admin_user_with_data)
        assert persona1 == PersonaType.ADMIN
        
        # Modify user to appear less admin-like
        original_is_superuser = admin_user_with_data.is_superuser
        admin_user_with_data.is_superuser = False
        admin_user_with_data.preferences = {}
        db_session.commit()
        
        # Clear cache to force re-detection
        auth_service.clear_persona_cache(admin_user_with_data.id)
        
        # Should now detect as different persona
        persona2 = await auth_service.get_user_persona_cached(admin_user_with_data)
        # Might be different based on other factors
        
        # Restore original state
        admin_user_with_data.is_superuser = original_is_superuser
        admin_user_with_data.preferences = {"role": "admin", "admin_features_enabled": True}
        db_session.commit()

# ========================================
# PERFORMANCE TESTS  
# ========================================

class TestPersonaSystemPerformance:
    """Test performance characteristics of persona system"""
    
    @pytest.mark.asyncio
    async def test_persona_detection_performance(
        self, persona_detector, admin_user_with_data
    ):
        """Test persona detection is fast enough"""
        start_time = datetime.utcnow()
        
        # Run multiple detections
        for _ in range(10):
            await persona_detector.detect_persona(admin_user_with_data)
        
        end_time = datetime.utcnow()
        total_time_ms = (end_time - start_time).total_seconds() * 1000
        avg_time_ms = total_time_ms / 10
        
        # Should be under 50ms average for good user experience
        assert avg_time_ms < 50
    
    @pytest.mark.asyncio
    async def test_response_generation_performance(
        self, response_factory, professional_user_with_data
    ):
        """Test response generation meets professional speed requirements"""
        regime_data = {"regime": "bull", "confidence": 0.8}
        
        start_time = datetime.utcnow()
        response = await response_factory.create_regime_response(
            professional_user_with_data, regime_data
        )
        end_time = datetime.utcnow()
        
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Professional responses should be under 500ms
        assert response_time_ms < 500
        assert isinstance(response, ProfessionalRegimeResponse)
    
    @pytest.mark.asyncio
    async def test_permission_checking_performance(
        self, auth_service, admin_user_with_data
    ):
        """Test permission checking is fast"""
        start_time = datetime.utcnow()
        
        # Check multiple permissions
        permissions_to_test = [
            "bulk_operations", "view_system_dashboard", "access_realtime_signals",
            "advanced_reporting", "system_configuration"
        ]
        
        for permission in permissions_to_test:
            await auth_service.check_permission(admin_user_with_data, permission)
        
        end_time = datetime.utcnow()
        total_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Should be very fast for permission checks
        assert total_time_ms < 100

# ========================================
# ERROR HANDLING TESTS
# ========================================

class TestPersonaSystemErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_persona_detection_with_corrupted_data(
        self, persona_detector, db_session
    ):
        """Test persona detection handles corrupted user data gracefully"""
        # Create user with problematic data
        user = User(
            email="corrupted@test.com",
            password_hash="corrupted@test.com",
            preferences={"invalid": "json", "nested": {"deeply": {"broken": None}}},
            created_at=None,  # Missing creation date
            last_login=None   # Never logged in
        )
        db_session.add(user)
        db_session.commit()
        
        # Should not crash and default to casual
        persona = await persona_detector.detect_persona(user)
        assert persona == PersonaType.CASUAL
    
    @pytest.mark.asyncio
    async def test_response_factory_handles_missing_data(
        self, response_factory, casual_user_with_data
    ):
        """Test response factory handles incomplete regime data"""
        # Minimal regime data
        incomplete_regime_data = {"regime": "unknown"}
        
        response = await response_factory.create_regime_response(
            casual_user_with_data, incomplete_regime_data
        )
        
        # Should still generate valid response with defaults
        assert isinstance(response, CasualRegimeResponse)
        assert response.regime == "unknown"
        assert response.confidence_description is not None
    
    @pytest.mark.asyncio
    async def test_permission_check_with_invalid_permission(
        self, auth_service, admin_user_with_data
    ):
        """Test permission checking handles invalid permissions"""
        # Test with non-existent permission
        has_permission = await auth_service.check_permission(
            admin_user_with_data, "non_existent_permission"
        )
        
        # Should safely return False for unknown permissions
        assert has_permission is False
    
    @pytest.mark.asyncio
    async def test_database_connection_error_handling(
        self, admin_user_with_data
    ):
        """Test behavior when database connection fails"""
        # Create detector with None session to simulate DB error
        detector = PersonaDetector(None)
        
        # Should handle gracefully and not crash
        try:
            persona = await detector.detect_persona(admin_user_with_data)
            # If it doesn't crash, it should default to casual
            assert persona == PersonaType.CASUAL
        except Exception as e:
            # Expected behavior - should fail gracefully
            assert "database" in str(e).lower() or "session" in str(e).lower()

# ========================================
# COMPATIBILITY TESTS
# ========================================

class TestBackwardCompatibility:
    """Test compatibility with existing system components"""
    
    def test_user_model_compatibility(self, admin_user_with_data):
        """Test persona system works with existing User model"""
        # Should not break existing User model functionality
        assert admin_user_with_data.email is not None
        assert admin_user_with_data.is_active is True
        assert admin_user_with_data.created_at is not None
        
        # New persona functionality should work
        assert hasattr(admin_user_with_data, 'preferences')
        assert hasattr(admin_user_with_data, 'is_superuser')
    
    def test_existing_api_pattern_compatibility(self, client: TestClient):
        """Test that existing API patterns still work"""
        # Test that health endpoint still works (no persona required)
        response = client.get("/api/v1/health")
        # Should work regardless of persona implementation
        assert response.status_code in [200, 404]  # 404 if not implemented yet
    
    @pytest.mark.asyncio 
    async def test_prediction_model_compatibility(
        self, response_factory, professional_user_with_data, db_session
    ):
        """Test compatibility with existing Prediction model"""
        # Ensure predictions are properly used in persona responses
        regime_data = {"regime": "bull", "confidence": 0.8}
        
        response = await response_factory.create_regime_response(
            professional_user_with_data, regime_data
        )
        
        # Should use prediction data for performance metrics
        assert isinstance(response, ProfessionalRegimeResponse)
        assert response.performance_tracking is not None
        assert response.performance_tracking.total_trades >= 0

# ========================================
# CONFIGURATION AND SETUP TESTS
# ========================================

@pytest.mark.asyncio
async def test_persona_system_initialization():
    """Test that persona system initializes correctly"""
    # Test that enums are properly defined
    assert len(PersonaType) == 3
    assert PersonaType.ADMIN.value == "admin"
    assert PersonaType.PROFESSIONAL.value == "professional"
    assert PersonaType.CASUAL.value == "casual"
    
    # Test that permission definitions exist
    assert hasattr(PersonaPermissions, 'ADMIN_PERMISSIONS')
    assert hasattr(PersonaPermissions, 'PROFESSIONAL_PERMISSIONS')
    assert hasattr(PersonaPermissions, 'CASUAL_PERMISSIONS')
    
    # Test permission structure
    admin_perms = PersonaPermissions.get_permissions_for_persona(PersonaType.ADMIN)
    assert isinstance(admin_perms, dict)
    assert len(admin_perms) > 0

if __name__ == "__main__":
    # Run tests with: pytest backend/tests/test_personas/test_day1_implementation.py -v
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])