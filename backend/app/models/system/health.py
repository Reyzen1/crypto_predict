# File: backend\app\models\system\health.py
# SQLAlchemy model for health data

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, JSON, Boolean, Index
from sqlalchemy.sql import func

from app.core.database import Base

class SystemHealth(Base):
    """
    System health monitoring and metrics tracking
    """
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Health check timestamp
    check_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Component health status
    api_status = Column(JSON, default=dict)
    database_status = Column(JSON, default=dict)
    ml_models_status = Column(JSON, default=dict)
    data_pipeline_status = Column(JSON, default=dict)
    external_apis_status = Column(JSON, default=dict)
    
    # Overall health metrics
    overall_health_score = Column(DECIMAL(5, 2), default=100)
    response_time_ms = Column(DECIMAL(10, 2))
    
    # System resource usage
    cpu_usage_percent = Column(DECIMAL(5, 2))
    memory_usage_percent = Column(DECIMAL(5, 2))
    disk_usage_percent = Column(DECIMAL(5, 2))
    
    # Database metrics
    active_connections = Column(Integer)
    slow_queries_count = Column(Integer, default=0)
    database_size_mb = Column(DECIMAL(15, 2))
    
    # Application metrics
    active_users_count = Column(Integer, default=0)
    requests_per_minute = Column(DECIMAL(10, 2))
    error_rate_percent = Column(DECIMAL(5, 4), default=0)
    
    # Additional monitoring data
    performance_metrics = Column(JSON, default=dict)
    error_logs = Column(JSON, default=[])
    warnings = Column(JSON, default=[])
    
    # Alert management
    alert_level = Column(String(10), default='normal', index=True)  # normal, warning, critical
    alerts_sent = Column(JSON, default=[])
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemHealth(score={self.overall_health_score}, alert_level={self.alert_level})>"

# Performance indexes
Index('idx_system_health_score', SystemHealth.overall_health_score, SystemHealth.check_time.desc())
Index('idx_system_health_alert', SystemHealth.alert_level, SystemHealth.check_time.desc())
