# Base Model Classes
# Foundation classes for all SQLAlchemy models

from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

class CreatedAtMixin:
    """Mixin for created_at timestamp only"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class UpdatedAtMixin:
    """Mixin for updated_at timestamp only"""
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class TimestampMixin(CreatedAtMixin, UpdatedAtMixin):
    """Mixin for both created_at and updated_at timestamps"""
    pass

class IDMixin:
    """Mixin for primary key ID"""
    id = Column(Integer, primary_key=True, nullable=False)

class BaseModel(Base, IDMixin, TimestampMixin):
    """Abstract base model with common functionality"""
    __abstract__ = True
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }