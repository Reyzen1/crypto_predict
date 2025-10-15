# backend/app/repositories/ai/jobs.py
# Repository for model job management

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from datetime import datetime, timedelta

from ..base_repository import BaseRepository
from ...models.ai.job import ModelJob
from ...models.enums import JobStatus, JobCategory, Priority


class ModelJobRepository(BaseRepository):
    """
    Repository for unified model job management
    """
    
    def __init__(self, db: Session):
        super().__init__(ModelJob, db)
    
    def get_active_jobs(self, model_id: int = None) -> List[ModelJob]:
        """Get active jobs (pending or running)"""
        query = self.db.query(ModelJob).filter(
            ModelJob.job_status.in_([JobStatus.PENDING.value, JobStatus.RUNNING.value])
        )
        
        if model_id:
            query = query.filter(ModelJob.model_id == model_id)
        
        return query.order_by(ModelJob.priority.desc(), ModelJob.created_at.asc()).all()
    
    def get_by_category(self, category: str, model_id: int = None) -> List[ModelJob]:
        """Get jobs by category"""
        query = self.db.query(ModelJob).filter(ModelJob.job_category == category)
        
        if model_id:
            query = query.filter(ModelJob.model_id == model_id)
        
        return query.order_by(ModelJob.created_at.desc()).all()
    
    def get_by_status(self, status: str) -> List[ModelJob]:
        """Get jobs by status"""
        return self.db.query(ModelJob).filter(
            ModelJob.job_status == status
        ).order_by(ModelJob.created_at.desc()).all()
    
    def get_failed_jobs(self, retry_eligible_only: bool = False) -> List[ModelJob]:
        """Get failed jobs"""
        query = self.db.query(ModelJob).filter(ModelJob.job_status == JobStatus.FAILED.value)
        
        if retry_eligible_only:
            query = query.filter(
                ModelJob.retry_count < ModelJob.max_retries,
                ModelJob.auto_retry_enabled == True
            )
        
        return query.order_by(ModelJob.completed_at.desc()).all()
    
    def get_scheduled_jobs(self) -> List[ModelJob]:
        """Get jobs scheduled for execution"""
        return self.db.query(ModelJob).filter(
            ModelJob.is_scheduled == True,
            ModelJob.next_scheduled_run <= datetime.utcnow()
        ).order_by(ModelJob.next_scheduled_run.asc()).all()
    
    def get_recent_completions(self, limit: int = 50) -> List[ModelJob]:
        """Get recently completed jobs"""
        return self.db.query(ModelJob).filter(
            ModelJob.job_status == JobStatus.COMPLETED.value
        ).order_by(ModelJob.completed_at.desc()).limit(limit).all()
    
    def get_user_jobs(self, user_id: int, status: str = None) -> List[ModelJob]:
        """Get jobs created by user"""
        query = self.db.query(ModelJob).filter(ModelJob.created_by == user_id)
        
        if status:
            query = query.filter(ModelJob.job_status == status)
        
        return query.order_by(ModelJob.created_at.desc()).all()
    
    def get_queue_jobs(self, queue_name: str) -> List[ModelJob]:
        """Get jobs in specific queue"""
        return self.db.query(ModelJob).filter(
            ModelJob.queue_name == queue_name,
            ModelJob.job_status == JobStatus.PENDING.value
        ).order_by(ModelJob.priority.desc(), ModelJob.queued_at.asc()).all()
    
    def get_job_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get job execution statistics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stats = self.db.query(
            func.count(ModelJob.id).label('total_jobs'),
            func.sum(func.case((ModelJob.job_status == JobStatus.COMPLETED.value, 1), else_=0)).label('completed'),
            func.sum(func.case((ModelJob.job_status == JobStatus.FAILED.value, 1), else_=0)).label('failed'),
            func.sum(func.case((ModelJob.job_status == JobStatus.RUNNING.value, 1), else_=0)).label('running'),
            func.sum(func.case((ModelJob.job_status == JobStatus.PENDING.value, 1), else_=0)).label('pending'),
            func.avg(ModelJob.execution_duration_sec).label('avg_duration')
        ).filter(ModelJob.created_at >= cutoff_date).first()
        
        if not stats:
            return {}
        
        return {
            'total_jobs': stats.total_jobs or 0,
            'completed': stats.completed or 0,
            'failed': stats.failed or 0,
            'running': stats.running or 0,
            'pending': stats.pending or 0,
            'success_rate': (stats.completed / stats.total_jobs * 100) if stats.total_jobs > 0 else 0,
            'average_duration_minutes': round(stats.avg_duration / 60, 2) if stats.avg_duration else 0
        }
    
    def get_long_running_jobs(self, threshold_hours: int = 1) -> List[ModelJob]:
        """Get jobs running longer than threshold"""
        threshold_time = datetime.utcnow() - timedelta(hours=threshold_hours)
        return self.db.query(ModelJob).filter(
            ModelJob.job_status == JobStatus.RUNNING.value,
            ModelJob.started_at <= threshold_time
        ).all()
    
    def get_dependency_chain(self, job_id: int) -> List[ModelJob]:
        """Get job dependency chain"""
        return self.db.query(ModelJob).filter(
            ModelJob.parent_job_id == job_id
        ).order_by(ModelJob.created_at.asc()).all()
    
    def cancel_job(self, job_id: int, reason: str = None) -> bool:
        """Cancel a job"""
        job = self.get(job_id)
        if not job:
            return False
        
        if job.job_status in [JobStatus.PENDING.value, JobStatus.RUNNING.value, JobStatus.PAUSED.value]:
            job.cancel_job(reason)
            self.db.commit()
            return True
        
        return False
    
    def retry_job(self, job_id: int) -> bool:
        """Retry a failed job"""
        job = self.get(job_id)
        if not job or not job.can_retry:
            return False
        
        job.retry_count += 1
        job.job_status = JobStatus.PENDING.value
        job.error_message = None
        job.failure_details = None
        self.db.commit()
        return True
    
    def get_system_resource_usage(self) -> Dict[str, Any]:
        """Get current system resource usage by jobs"""
        running_jobs = self.get_by_status(JobStatus.RUNNING.value)
        
        total_cpu_cores = sum(job.resources_allocated.get('cpu_cores', 0) for job in running_jobs if job.resources_allocated)
        total_memory_gb = sum(job.resources_allocated.get('memory_gb', 0) for job in running_jobs if job.resources_allocated)
        total_gpu_memory = sum(job.resources_allocated.get('gpu_memory_mb', 0) for job in running_jobs if job.resources_allocated)
        
        return {
            'running_jobs_count': len(running_jobs),
            'total_cpu_cores_used': total_cpu_cores,
            'total_memory_gb_used': round(total_memory_gb, 2),
            'total_gpu_memory_mb_used': total_gpu_memory,
            'resource_analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    def optimize_job_queue(self, queue_name: str) -> Dict[str, Any]:
        """Optimize job queue based on priorities and resources"""
        queue_jobs = self.get_queue_jobs(queue_name)
        
        if not queue_jobs:
            return {'message': 'Queue is empty', 'optimizations': []}
        
        optimizations = []
        
        # Sort by priority and estimated duration
        high_priority_quick = []
        high_priority_long = []
        normal_priority = []
        
        for job in queue_jobs:
            duration_estimate = job.estimated_duration_sec or 3600  # Default 1 hour
            
            if job.priority >= 8:  # High priority
                if duration_estimate <= 1800:  # 30 minutes or less
                    high_priority_quick.append(job)
                else:
                    high_priority_long.append(job)
            else:
                normal_priority.append(job)
        
        # Reorder queue for optimization
        optimized_order = (
            sorted(high_priority_quick, key=lambda j: j.estimated_duration_sec or 0) +
            sorted(high_priority_long, key=lambda j: j.priority, reverse=True) +
            sorted(normal_priority, key=lambda j: (j.priority, j.estimated_duration_sec or 0), reverse=True)
        )
        
        # Update queue positions
        for i, job in enumerate(optimized_order):
            if job.queue_position != i + 1:
                job.queue_position = i + 1
                optimizations.append({
                    'job_id': job.id,
                    'action': 'reordered',
                    'new_position': i + 1,
                    'reason': 'priority_duration_optimization'
                })
        
        if optimizations:
            self.db.commit()
        
        return {
            'queue_name': queue_name,
            'total_jobs_reordered': len(optimizations),
            'optimizations': optimizations,
            'optimization_timestamp': datetime.utcnow().isoformat()
        }
    
    def get_job_health_check(self) -> Dict[str, Any]:
        """Comprehensive job system health check"""
        now = datetime.utcnow()
        
        # Check for stuck jobs
        stuck_jobs = self.db.query(ModelJob).filter(
            ModelJob.job_status == JobStatus.RUNNING.value,
            ModelJob.started_at < now - timedelta(hours=4),  # Running for more than 4 hours
            or_(
                ModelJob.last_heartbeat.is_(None),
                ModelJob.last_heartbeat < now - timedelta(minutes=30)  # No heartbeat in 30 minutes
            )
        ).all()
        
        # Check for high failure rates
        recent_jobs = self.db.query(ModelJob).filter(
            ModelJob.created_at >= now - timedelta(hours=24)
        ).all()
        
        failed_jobs_24h = [j for j in recent_jobs if j.job_status == JobStatus.FAILED.value]
        failure_rate_24h = (len(failed_jobs_24h) / len(recent_jobs) * 100) if recent_jobs else 0
        
        # Check queue backlogs
        pending_by_queue = self.db.query(
            ModelJob.queue_name,
            func.count(ModelJob.id).label('pending_count')
        ).filter(
            ModelJob.job_status == JobStatus.PENDING.value
        ).group_by(ModelJob.queue_name).all()
        
        backlogged_queues = [
            {'queue': q.queue_name, 'pending_jobs': q.pending_count}
            for q in pending_by_queue if q.pending_count > 10
        ]
        
        # Check resource contention
        resource_usage = self.get_system_resource_usage()
        high_resource_usage = (
            resource_usage['total_cpu_cores_used'] > 80 or
            resource_usage['total_memory_gb_used'] > 120 or  # Assuming 128GB system
            resource_usage['total_gpu_memory_mb_used'] > 22000  # Assuming 24GB GPU
        )
        
        # Generate health status
        issues = []
        
        if stuck_jobs:
            issues.append({
                'type': 'stuck_jobs',
                'severity': 'high',
                'count': len(stuck_jobs),
                'message': f'{len(stuck_jobs)} jobs appear to be stuck without heartbeat'
            })
        
        if failure_rate_24h > 20:
            issues.append({
                'type': 'high_failure_rate',
                'severity': 'medium',
                'rate': round(failure_rate_24h, 2),
                'message': f'Failure rate is {failure_rate_24h:.1f}% in last 24 hours'
            })
        
        if backlogged_queues:
            issues.append({
                'type': 'queue_backlog',
                'severity': 'medium',
                'queues': backlogged_queues,
                'message': f'{len(backlogged_queues)} queues have significant backlogs'
            })
        
        if high_resource_usage:
            issues.append({
                'type': 'resource_contention',
                'severity': 'low',
                'usage': resource_usage,
                'message': 'System resources are highly utilized'
            })
        
        health_score = max(0, 100 - (len(issues) * 15) - (failure_rate_24h / 2))
        
        return {
            'health_score': round(health_score, 1),
            'status': 'healthy' if health_score > 80 else 'degraded' if health_score > 60 else 'unhealthy',
            'issues_found': len(issues),
            'issues': issues,
            'system_metrics': {
                'total_jobs_24h': len(recent_jobs),
                'failure_rate_24h': round(failure_rate_24h, 2),
                'stuck_jobs_count': len(stuck_jobs),
                'backlogged_queues_count': len(backlogged_queues)
            },
            'resource_usage': resource_usage,
            'health_check_timestamp': now.isoformat()
        }
    
    def auto_scale_recommendations(self) -> Dict[str, Any]:
        """Generate auto-scaling recommendations"""
        now = datetime.utcnow()
        
        # Analyze queue pressure
        queue_analysis = self.db.query(
            ModelJob.queue_name,
            func.count(func.case((ModelJob.job_status == JobStatus.PENDING.value, 1))).label('pending'),
            func.count(func.case((ModelJob.job_status == JobStatus.RUNNING.value, 1))).label('running'),
            func.avg(ModelJob.execution_duration_sec).label('avg_duration')
        ).filter(
            ModelJob.created_at >= now - timedelta(hours=2)
        ).group_by(ModelJob.queue_name).all()
        
        recommendations = []
        
        for queue in queue_analysis:
            queue_name = queue.queue_name
            pending_count = queue.pending
            running_count = queue.running
            avg_duration_minutes = (queue.avg_duration or 0) / 60
            
            # Calculate estimated wait time
            if running_count > 0 and avg_duration_minutes > 0:
                estimated_wait_hours = (pending_count * avg_duration_minutes) / (running_count * 60)
            else:
                estimated_wait_hours = 0
            
            if pending_count > 5 and estimated_wait_hours > 2:
                recommendations.append({
                    'queue_name': queue_name,
                    'action': 'scale_up',
                    'reason': 'high_queue_pressure',
                    'current_workers': running_count,
                    'suggested_workers': min(running_count + 2, pending_count),
                    'estimated_wait_reduction_hours': round(estimated_wait_hours * 0.4, 2),
                    'priority': 'high' if estimated_wait_hours > 4 else 'medium'
                })
            
            elif pending_count == 0 and running_count == 0:
                recommendations.append({
                    'queue_name': queue_name,
                    'action': 'scale_down',
                    'reason': 'idle_queue',
                    'current_workers': running_count,
                    'suggested_workers': 0,
                    'cost_savings_potential': 'high',
                    'priority': 'low'
                })
        
        # Resource utilization analysis
        resource_usage = self.get_system_resource_usage()
        
        if resource_usage['total_cpu_cores_used'] < 20 and resource_usage['running_jobs_count'] < 3:
            recommendations.append({
                'action': 'optimize_resources',
                'reason': 'low_utilization',
                'current_utilization': f"{resource_usage['total_cpu_cores_used']} CPU cores",
                'suggestion': 'Consider consolidating workloads or scaling down infrastructure',
                'priority': 'low'
            })
        
        return {
            'recommendations_count': len(recommendations),
            'recommendations': sorted(recommendations, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True),
            'analysis_timestamp': now.isoformat(),
            'next_analysis_suggested': (now + timedelta(minutes=30)).isoformat()
        }
    
    def cleanup_completed_jobs(self, retention_days: int = 30) -> Dict[str, Any]:
        """Clean up old completed jobs"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Find jobs to clean up
        old_completed_jobs = self.db.query(ModelJob).filter(
            ModelJob.job_status == JobStatus.COMPLETED.value,
            ModelJob.completed_at < cutoff_date
        ).all()
        
        old_failed_jobs = self.db.query(ModelJob).filter(
            ModelJob.job_status == JobStatus.FAILED.value,
            ModelJob.completed_at < cutoff_date,
            ModelJob.retry_count >= ModelJob.max_retries  # Only cleanup jobs that won't be retried
        ).all()
        
        jobs_to_cleanup = old_completed_jobs + old_failed_jobs
        
        cleanup_summary = {
            'retention_days': retention_days,
            'completed_jobs_cleaned': len(old_completed_jobs),
            'failed_jobs_cleaned': len(old_failed_jobs),
            'total_jobs_cleaned': len(jobs_to_cleanup),
            'cleanup_timestamp': datetime.utcnow().isoformat()
        }
        
        # Archive job data before deletion (optional)
        archived_jobs = []
        for job in jobs_to_cleanup:
            archived_jobs.append({
                'job_id': job.id,
                'job_type': job.job_type,
                'status': job.job_status,
                'duration_seconds': job.execution_duration_sec,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'resource_usage': job.resources_allocated
            })
        
        # Delete old jobs
        for job in jobs_to_cleanup:
            self.db.delete(job)
        
        self.db.commit()
        
        cleanup_summary['archived_job_metadata'] = archived_jobs
        
        return cleanup_summary
    
    def get_performance_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get detailed job performance analytics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        jobs = self.db.query(ModelJob).filter(
            ModelJob.created_at >= cutoff_date
        ).all()
        
        if not jobs:
            return {'message': 'No jobs found in specified period'}
        
        # Performance by job type
        job_type_stats = {}
        for job in jobs:
            job_type = job.job_type
            if job_type not in job_type_stats:
                job_type_stats[job_type] = {
                    'total': 0,
                    'completed': 0,
                    'failed': 0,
                    'durations': []
                }
            
            stats = job_type_stats[job_type]
            stats['total'] += 1
            
            if job.job_status == JobStatus.COMPLETED.value:
                stats['completed'] += 1
                if job.execution_duration_sec:
                    stats['durations'].append(job.execution_duration_sec)
            elif job.job_status == JobStatus.FAILED.value:
                stats['failed'] += 1
        
        # Calculate metrics for each job type
        for job_type, stats in job_type_stats.items():
            stats['success_rate'] = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            if stats['durations']:
                durations = stats['durations']
                stats['avg_duration_minutes'] = round(sum(durations) / len(durations) / 60, 2)
                stats['min_duration_minutes'] = round(min(durations) / 60, 2)
                stats['max_duration_minutes'] = round(max(durations) / 60, 2)
            else:
                stats['avg_duration_minutes'] = 0
                stats['min_duration_minutes'] = 0
                stats['max_duration_minutes'] = 0
            
            # Remove raw durations from output
            del stats['durations']
        
        # Queue performance analysis
        queue_stats = {}
        for job in jobs:
            queue = job.queue_name or 'default'
            if queue not in queue_stats:
                queue_stats[queue] = {'jobs': 0, 'avg_wait_time': 0, 'wait_times': []}
            
            queue_stats[queue]['jobs'] += 1
            
            if job.started_at and job.queued_at:
                wait_time = (job.started_at - job.queued_at).total_seconds()
                queue_stats[queue]['wait_times'].append(wait_time)
        
        # Calculate queue wait times
        for queue, stats in queue_stats.items():
            if stats['wait_times']:
                stats['avg_wait_time_minutes'] = round(sum(stats['wait_times']) / len(stats['wait_times']) / 60, 2)
            else:
                stats['avg_wait_time_minutes'] = 0
            del stats['wait_times']
        
        return {
            'analysis_period_days': days,
            'total_jobs_analyzed': len(jobs),
            'job_type_performance': job_type_stats,
            'queue_performance': queue_stats,
            'overall_metrics': {
                'total_jobs': len(jobs),
                'completed_jobs': len([j for j in jobs if j.job_status == JobStatus.COMPLETED.value]),
                'failed_jobs': len([j for j in jobs if j.job_status == JobStatus.FAILED.value]),
                'overall_success_rate': round(len([j for j in jobs if j.job_status == JobStatus.COMPLETED.value]) / len(jobs) * 100, 2)
            },
            'analysis_timestamp': datetime.utcnow().isoformat()
        }