# backend/app/models/ai/jobs.py
# Unified model job management (training, prediction, evaluation, etc.)

from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Numeric, DateTime, ForeignKey, CheckConstraint, Index, Boolean, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..base import BaseModel, TimestampMixin
from ..enums import JobStatus, JobCategory, Priority


class ModelJob(BaseModel, TimestampMixin):
    """
    Unified model job management for training, prediction, evaluation, and optimization
    
    Comprehensive job tracking with execution monitoring, resource management,
    scheduling capabilities, and dependency management. Replaces separate
    ModelTrainingJob and ModelPredictionJob classes.
    """
    __tablename__ = 'model_jobs'
    
    # 🔗 Model Reference
    model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=False, index=True)
    
    # 🎯 Job Classification & Control
    job_status = Column(String(20), nullable=False, default=JobStatus.PENDING.value, index=True,
                       comment="Status: 'pending', 'running', 'completed', 'failed', 'cancelled', 'paused'")
    job_category = Column(String(15), nullable=False, index=True,
                         comment="Category: 'training', 'prediction', 'evaluation', 'optimization', 'deployment'")
    job_type = Column(String(25), nullable=False, index=True,
                     comment="Specific job type within category")
    job_name = Column(String(30), nullable=True, comment="Human-readable job name/description")
    
    # 📊 Execution Tracking
    progress_pct = Column(Numeric(5,2), nullable=False, default=0, comment="Job progress (0-100)")
    current_phase = Column(String(20), nullable=True, comment="Current execution phase/stage")
    total_steps = Column(Integer, nullable=True, comment="Total number of steps in job")
    completed_steps = Column(Integer, nullable=True, comment="Number of completed steps")
    
    # ⚙️ Comprehensive Job Configuration
    job_config = Column(JSONB, nullable=False, default={}, comment="Complete job configuration and parameters")
    
    # 📈 Real-time Job Metrics & Statistics
    job_metrics = Column(JSONB, nullable=True, default={}, comment="Real-time job metrics")
    
    # ⏱️ Comprehensive Timing Information
    queued_at = Column(DateTime(timezone=True), nullable=True, comment="When job was queued")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="When job actually started")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="When job completed")
    last_heartbeat = Column(DateTime(timezone=True), nullable=True, comment="Last activity timestamp")
    execution_duration_sec = Column(Integer, nullable=True, comment="Total execution time")
    estimated_duration_sec = Column(Integer, nullable=True, comment="Estimated duration")
    
    # 📋 Job Outputs & Results
    job_outputs = Column(JSONB, nullable=True, default={}, comment="Job results and outputs")
    
    # 🔄 Scheduling & Automation
    is_scheduled = Column(Boolean, nullable=False, default=False, comment="Whether this is a recurring job")
    schedule_expression = Column(String(50), nullable=True, comment="Cron expression for recurring jobs")
    next_scheduled_run = Column(DateTime(timezone=True), nullable=True, comment="Next scheduled execution")
    auto_retry_enabled = Column(Boolean, nullable=False, default=True, comment="Enable automatic retries")
    
    # 👥 Job Management & Ownership
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    priority = Column(String(10), nullable=False, default=Priority.NORMAL.value, index=True,
                     comment="Priority: 'low', 'normal', 'high', 'urgent', 'critical'")
    queue_name = Column(String(20), nullable=True, comment="Job queue name")
    
    # 🔁 Error Handling & Retry Logic
    retry_count = Column(Integer, nullable=False, default=0, comment="Number of retries attempted")
    max_retries = Column(Integer, nullable=False, default=3, comment="Maximum retries allowed")
    error_message = Column(Text, nullable=True, comment="Detailed error message if failed")
    failure_details = Column(JSONB, nullable=True, default={}, comment="Detailed failure information")
    
    # 💾 Resource Management & Limits
    resource_allocation = Column(JSONB, nullable=True, default={}, comment="Resource limits and allocation")
    
    # 📝 Job Logging & Monitoring
    execution_log = Column(Text, nullable=True, comment="Job execution logs")
    job_events = Column(JSONB, nullable=True, default={}, comment="Job lifecycle events")
    monitoring_webhook = Column(String(50), nullable=True, comment="Webhook URL for notifications")
    
    # 🔗 Dependencies & Relationships
    job_dependencies = Column(JSONB, nullable=True, default={}, comment="Job dependencies configuration")
    parent_job_id = Column(Integer, ForeignKey('model_jobs.id'), nullable=True, index=True)
    blocks_other_jobs = Column(Boolean, nullable=False, default=False, comment="Whether this job blocks others")
    
    # 🔗 Relationships
    model = relationship("AIModel", back_populates="jobs")
    creator = relationship("User", foreign_keys=[created_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    parent_job = relationship("ModelJob", remote_side="ModelJob.id", back_populates="child_jobs")
    child_jobs = relationship("ModelJob", back_populates="parent_job")
    performance_evaluations = relationship("ModelPerformance", back_populates="source_job")
    
    # 📋 Enhanced Business Logic Constraints
    __table_args__ = (
        CheckConstraint('progress_pct >= 0 AND progress_pct <= 100', name='chk_jobs_progress_range'),
        CheckConstraint('retry_count >= 0 AND retry_count <= max_retries', name='chk_jobs_retry_logic'),
        CheckConstraint('max_retries >= 0 AND max_retries <= 20', name='chk_jobs_max_retries'),
        CheckConstraint('completed_steps IS NULL OR total_steps IS NULL OR completed_steps <= total_steps', 
                       name='chk_jobs_steps_logic'),
        CheckConstraint('started_at IS NULL OR completed_at IS NULL OR started_at <= completed_at', 
                       name='chk_jobs_timing_logic'),
        CheckConstraint('execution_duration_sec IS NULL OR execution_duration_sec >= 0', 
                       name='chk_jobs_duration_positive'),
        CheckConstraint('schedule_expression IS NULL OR is_scheduled = true', 
                       name='chk_jobs_schedule_logic'),
        
        CheckConstraint(
            "job_status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused')",
            name='chk_jobs_status_valid'
        ),
        CheckConstraint(
            "job_category IN ('training', 'prediction', 'evaluation', 'optimization', 'deployment')",
            name='chk_jobs_category_valid'
        ),
        CheckConstraint(
            "priority IN ('low', 'normal', 'high', 'urgent', 'critical')",
            name='chk_jobs_priority_valid'
        ),
        
        # Optimized Indexes for Performance
        Index('idx_model_jobs_active', 'job_status', 'priority', 'created_at', 
              postgresql_where=text("job_status IN ('pending', 'running')")),
        Index('idx_model_jobs_model_category', 'model_id', 'job_category', 'job_status', 'created_at'),
        Index('idx_model_jobs_scheduled', 'is_scheduled', 'next_scheduled_run',
              postgresql_where=text('is_scheduled = true')),
        Index('idx_model_jobs_monitoring', 'job_status', 'progress_pct', 'last_heartbeat',
              postgresql_where=text("job_status = 'running'")),
        Index('idx_model_jobs_user_jobs', 'created_by', 'job_status', 'created_at'),
        Index('idx_model_jobs_queue_management', 'queue_name', 'priority', 'queued_at',
              postgresql_where=text("job_status = 'pending'")),
        Index('idx_model_jobs_parent_child', 'parent_job_id', 'job_status',
              postgresql_where=text('parent_job_id IS NOT NULL')),
        Index('idx_model_jobs_category_type', 'job_category', 'job_type', 'created_at'),
        Index('idx_model_jobs_completion', 'completed_at', 'job_status'),
    )
    
    def __repr__(self):
        return f"<ModelJob(id={self.id}, model_id={self.model_id}, category='{self.job_category}', status='{self.job_status}')>"
    
    @property
    def is_active(self):
        """Check if job is currently active (pending or running)"""
        return self.job_status in [JobStatus.PENDING.value, JobStatus.RUNNING.value]
    
    @property
    def is_completed(self):
        """Check if job has completed successfully"""
        return self.job_status == JobStatus.COMPLETED.value
    
    @property
    def is_failed(self):
        """Check if job has failed"""
        return self.job_status in [JobStatus.FAILED.value, JobStatus.CANCELLED.value]
    
    @property
    def execution_duration_minutes(self):
        """Get execution duration in minutes"""
        if self.execution_duration_sec:
            return round(self.execution_duration_sec / 60, 2)
        return None
    
    @property
    def estimated_completion_time(self):
        """Calculate estimated completion time"""
        if (self.started_at and self.estimated_duration_sec and 
            self.job_status == JobStatus.RUNNING.value):
            from datetime import timedelta
            return self.started_at + timedelta(seconds=self.estimated_duration_sec)
        return None
    
    @property
    def steps_progress(self):
        """Get progress based on completed steps"""
        if self.total_steps and self.completed_steps:
            return min(100, (self.completed_steps / self.total_steps) * 100)
        return float(self.progress_pct)
    
    @property
    def can_retry(self):
        """Check if job can be retried"""
        return (self.is_failed and 
                self.retry_count < self.max_retries and 
                self.auto_retry_enabled)
    
    def start_job(self):
        """Mark job as started"""
        self.job_status = JobStatus.RUNNING.value
        self.started_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        if not self.queued_at:
            self.queued_at = self.created_at
    
    def update_progress(self, progress_pct: float = None, completed_steps: int = None, 
                       current_phase: str = None, metrics: dict = None):
        """Update job progress and metrics"""
        if progress_pct is not None:
            self.progress_pct = max(0, min(100, progress_pct))
        
        if completed_steps is not None:
            self.completed_steps = completed_steps
            if self.total_steps:
                self.progress_pct = min(100, (completed_steps / self.total_steps) * 100)
        
        if current_phase:
            self.current_phase = current_phase
        
        if metrics:
            if not self.job_metrics:
                self.job_metrics = {}
            self.job_metrics.update(metrics)
        
        self.last_heartbeat = datetime.utcnow()
    
    def complete_job(self, outputs: dict = None, final_metrics: dict = None):
        """Mark job as completed"""
        self.job_status = JobStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.progress_pct = 100
        
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.execution_duration_sec = int(delta.total_seconds())
        
        if outputs:
            self.job_outputs = outputs
        
        if final_metrics:
            if not self.job_metrics:
                self.job_metrics = {}
            self.job_metrics['final'] = final_metrics
    
    def fail_job(self, error_message: str, error_details: dict = None, 
                retry: bool = True):
        """Mark job as failed"""
        self.error_message = error_message
        if error_details:
            self.failure_details = error_details
        
        if retry and self.can_retry:
            self.retry_count += 1
            self.job_status = JobStatus.PENDING.value  # Queue for retry
            self.error_message = f"Retry {self.retry_count}/{self.max_retries}: {error_message}"
        else:
            self.job_status = JobStatus.FAILED.value
            self.completed_at = datetime.utcnow()
            
            if self.started_at:
                delta = self.completed_at - self.started_at
                self.execution_duration_sec = int(delta.total_seconds())
    
    def pause_job(self, reason: str = None):
        """Pause a running job"""
        if self.job_status == JobStatus.RUNNING.value:
            self.job_status = JobStatus.PAUSED.value
            if reason:
                if not self.job_events:
                    self.job_events = {}
                self.job_events['paused'] = {
                    'reason': reason,
                    'timestamp': datetime.utcnow().isoformat()
                }
    
    def resume_job(self):
        """Resume a paused job"""
        if self.job_status == JobStatus.PAUSED.value:
            self.job_status = JobStatus.RUNNING.value
            self.last_heartbeat = datetime.utcnow()
    
    def cancel_job(self, reason: str = None):
        """Cancel a job"""
        if self.job_status in [JobStatus.PENDING.value, JobStatus.RUNNING.value, JobStatus.PAUSED.value]:
            self.job_status = JobStatus.CANCELLED.value
            self.completed_at = datetime.utcnow()
            if reason:
                if not self.job_events:
                    self.job_events = {}
                self.job_events['cancelled'] = {
                    'reason': reason,
                    'timestamp': datetime.utcnow().isoformat()
                }
    
    def add_dependency(self, job_id: int, dependency_type: str = 'completion'):
        """Add job dependency"""
        if not self.job_dependencies:
            self.job_dependencies = {}
        
        if 'dependencies' not in self.job_dependencies:
            self.job_dependencies['dependencies'] = []
        
        self.job_dependencies['dependencies'].append({
            'job_id': job_id,
            'type': dependency_type,
            'added_at': datetime.utcnow().isoformat()
        })
    
    def log_event(self, event_type: str, details: dict = None):
        """Log job lifecycle event"""
        if not self.job_events:
            self.job_events = {}
        
        if 'events' not in self.job_events:
            self.job_events['events'] = []
        
        self.job_events['events'].append({
            'type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        })
    
    @classmethod
    def get_active_jobs(cls, session, model_id: int = None):
        """Get active jobs (pending or running)"""
        query = session.query(cls).filter(
            cls.job_status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value])
        )
        
        if model_id:
            query = query.filter(cls.model_id == model_id)
        
        return query.order_by(cls.priority.desc(), cls.created_at.asc()).all()
    
    @classmethod
    def get_by_category(cls, session, category: str, model_id: int = None):
        """Get jobs by category"""
        query = session.query(cls).filter(cls.job_category == category)
        
        if model_id:
            query = query.filter(cls.model_id == model_id)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_failed_jobs(cls, session, retry_eligible_only: bool = False):
        """Get failed jobs"""
        query = session.query(cls).filter(cls.job_status == JobStatus.FAILED.value)
        
        if retry_eligible_only:
            query = query.filter(
                cls.retry_count < cls.max_retries,
                cls.auto_retry_enabled == True
            )
        
        return query.order_by(cls.completed_at.desc()).all()
    
    @classmethod
    def get_scheduled_jobs(cls, session):
        """Get jobs scheduled for execution"""
        return session.query(cls).filter(
            cls.is_scheduled == True,
            cls.next_scheduled_run <= datetime.utcnow()
        ).order_by(cls.next_scheduled_run.asc()).all()
    
    @classmethod
    def get_recent_completions(cls, session, limit: int = 50):
        """Get recently completed jobs"""
        return session.query(cls).filter(
            cls.job_status == JobStatus.COMPLETED.value
        ).order_by(cls.completed_at.desc()).limit(limit).all()
    
    def to_dict(self, include_detailed: bool = False) -> dict:
        """Convert job to dictionary"""
        data = {
            'id': self.id,
            'model_id': self.model_id,
            'job_status': self.job_status,
            'job_category': self.job_category,
            'job_type': self.job_type,
            'job_name': self.job_name,
            'progress_pct': float(self.progress_pct),
            'current_phase': self.current_phase,
            'priority': self.priority,
            'is_active': self.is_active,
            'is_completed': self.is_completed,
            'is_failed': self.is_failed,
            'can_retry': self.can_retry,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_detailed:
            data.update({
                'job_config': self.job_config,
                'job_metrics': self.job_metrics,
                'job_outputs': self.job_outputs,
                'total_steps': self.total_steps,
                'completed_steps': self.completed_steps,
                'steps_progress': self.steps_progress,
                'queued_at': self.queued_at.isoformat() if self.queued_at else None,
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None,
                'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                'execution_duration_sec': self.execution_duration_sec,
                'execution_duration_minutes': self.execution_duration_minutes,
                'estimated_duration_sec': self.estimated_duration_sec,
                'estimated_completion_time': self.estimated_completion_time.isoformat() if self.estimated_completion_time else None,
                'is_scheduled': self.is_scheduled,
                'schedule_expression': self.schedule_expression,
                'next_scheduled_run': self.next_scheduled_run.isoformat() if self.next_scheduled_run else None,
                'auto_retry_enabled': self.auto_retry_enabled,
                'created_by': self.created_by,
                'assigned_to': self.assigned_to,
                'queue_name': self.queue_name,
                'retry_count': self.retry_count,
                'max_retries': self.max_retries,
                'error_message': self.error_message,
                'failure_details': self.failure_details,
                'resource_allocation': self.resource_allocation,
                'execution_log': self.execution_log,
                'job_events': self.job_events,
                'monitoring_webhook': self.monitoring_webhook,
                'job_dependencies': self.job_dependencies,
                'parent_job_id': self.parent_job_id,
                'blocks_other_jobs': self.blocks_other_jobs
            })
        
        return data