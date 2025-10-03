# Reusable Mixins
# Common functionality shared across multiple models

from sqlalchemy import Column, Boolean, Integer, Text, DateTime, String, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

class ActiveMixin:
    """Mixin for is_active field"""
    is_active = Column(Boolean, nullable=False, default=True)

class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    @hybrid_property
    def is_deleted(self):
        return self.deleted_at is not None

class UserTrackingMixin:
    """Mixin for tracking user who created/modified records"""
    added_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    last_modified_by = Column(Integer, ForeignKey('users.id'), nullable=False)

class ValidationMixin:
    """Mixin for data validation fields"""
    is_validated = Column(Boolean, nullable=False, default=False)
    
class AIAnalysisMixin:
    """Mixin for AI analysis common fields"""
    ai_confidence_score = Column(Numeric(4,2), nullable=True)
    signal_agreement_score = Column(Numeric(4,2), nullable=True) 
    analysis_data = Column(JSON, nullable=True, default={})

class DataQualityMixin:
    """Mixin for data quality tracking
    
    Usage: assets table (track data quality from external APIs)
    """
    data_quality_score = Column(Integer, nullable=False, default=100)
    collection_duration_ms = Column(Integer, nullable=True)
    data_source = Column(String(50), nullable=False, default='internal')

class AccessTrackingMixin:
    """Mixin for tracking access patterns
    
    Usage: assets table (track which assets are accessed most)
    """
    access_count = Column(Integer, nullable=False, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

class UserPreferencesMixin:
    """Mixin for user preferences and settings
    
    Usage: users table (preferences, timezone, language)
    """
    preferences = Column(JSON, nullable=True, default={})
    timezone = Column(String(50), nullable=True)
    language = Column(String(5), nullable=False, default='en')

class ExternalIdsMixin:
    """Mixin for external API identifiers
    
    Usage: assets table (coingecko, coinmarketcap IDs)
    """
    external_ids = Column(JSON, nullable=True, default={})