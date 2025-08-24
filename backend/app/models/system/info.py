# File: backend\app\models\system\info.py
# SQLAlchemy model for info data

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.sql import func

from app.core.database import Base

class SystemInfo(Base):
    """
    System configuration and metadata storage
    """
    __tablename__ = "system_info"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Key-value storage
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemInfo(key={self.key}, value={self.value[:50]}...)>"
