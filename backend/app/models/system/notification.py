# File: backend\app\models\system\notification.py
# SQLAlchemy model for notification data

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import timedelta

from app.core.database import Base

class Notification(Base):
    """
    User notification system
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification details
    notification_type = Column(String(20), nullable=False, index=True)  # signal, alert, system, educational
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, default={})  # Additional notification data
    
    # Status and priority
    status = Column(String(20), default='unread', index=True)  # unread, read, dismissed, archived
    priority = Column(String(20), default='normal', index=True)  # low, normal, high, urgent
    
    # Delivery settings
    channel = Column(String(20), default='in_app')  # in_app, email, push, sms
    source = Column(String(50), default='system')
    
    # Reference tracking
    reference_id = Column(Integer)        # Reference to related entity
    reference_type = Column(String(30))   # Type of referenced entity
    
    # Scheduling and expiration
    scheduled_for = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    sent_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), default=lambda: func.now() + timedelta(days=30))
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, user_id={self.user_id})>"

# Performance indexes
Index('idx_notifications_user_status', Notification.user_id, Notification.status, Notification.scheduled_for.desc())
Index('idx_notifications_type', Notification.notification_type, Notification.priority, Notification.scheduled_for.desc())
Index('idx_notifications_expires', Notification.expires_at).where(Notification.status != 'expired')
Index('idx_notifications_reference', Notification.reference_type, Notification.reference_id)
