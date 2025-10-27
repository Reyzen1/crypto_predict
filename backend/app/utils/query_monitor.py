"""
Query monitoring utility for tracking database queries
"""
import logging
import time
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine
from typing import Dict, List
import threading

logger = logging.getLogger(__name__)

class QueryMonitor:
    """Monitor database queries for performance analysis"""
    
    def __init__(self):
        self.query_count = 0
        self.queries = []
        self.enabled = False
        self.start_time = None
        self.lock = threading.Lock()
        
    def enable(self):
        """Enable query monitoring"""
        with self.lock:
            self.enabled = True
            self.query_count = 0
            self.queries = []
            self.start_time = time.time()
            logger.info("🔍 Query monitoring ENABLED")
    
    def disable(self):
        """Disable query monitoring"""
        with self.lock:
            self.enabled = False
            total_time = time.time() - self.start_time if self.start_time else 0
            logger.info(f"🔍 Query monitoring DISABLED - Total queries: {self.query_count}, Total time: {total_time:.2f}s")
    
    def reset(self):
        """Reset query counters"""
        with self.lock:
            self.query_count = 0
            self.queries = []
            self.start_time = time.time()
            logger.info("🔄 Query monitor RESET")
    
    def get_stats(self) -> Dict:
        """Get current monitoring statistics"""
        with self.lock:
            total_time = time.time() - self.start_time if self.start_time else 0
            return {
                'total_queries': self.query_count,
                'total_time': total_time,
                'queries_per_second': self.query_count / total_time if total_time > 0 else 0,
                'recent_queries': self.queries[-10:] if len(self.queries) > 10 else self.queries
            }

# Global instance
query_monitor = QueryMonitor()

def setup_query_monitoring(engine):
    """Setup SQLAlchemy event listeners for query monitoring"""
    
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if query_monitor.enabled:
            context._query_start_time = time.time()
    
    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if query_monitor.enabled:
            with query_monitor.lock:
                query_monitor.query_count += 1
                
                # Calculate execution time
                execution_time = time.time() - context._query_start_time
                
                # Create compact query representation
                compact_sql = statement.replace('\n', ' ').replace('\t', ' ')
                while '  ' in compact_sql:
                    compact_sql = compact_sql.replace('  ', ' ')
                compact_sql = compact_sql.strip()
                
                # Truncate long SQL for readability
                if len(compact_sql) > 80:
                    compact_sql = compact_sql[:77] + "..."
                
                # Truncate parameters for readability
                params_str = ""
                if parameters:
                    params_str = str(parameters)
                    if len(params_str) > 50:
                        params_str = params_str[:47] + "..."
                
                # Store query info
                query_info = {
                    'query_id': query_monitor.query_count,
                    'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                    'execution_time': f"{execution_time:.3f}s",
                    'statement': compact_sql,
                    'parameters': params_str
                }
                
                query_monitor.queries.append(query_info)
                
                # Print compact colored output
                color = "\033[92m" if execution_time < 0.1 else "\033[93m" if execution_time < 0.5 else "\033[91m"
                reset_color = "\033[0m"
                
                # Single line compact output
                params_part = f" | Params: {params_str}" if params_str else ""
                print(f"{color}🔍 Query #{query_monitor.query_count:03d} ({query_info['execution_time']}) | {compact_sql}{params_part}{reset_color}")

def enable_query_monitoring():
    """Enable query monitoring globally"""
    query_monitor.enable()

def disable_query_monitoring():
    """Disable query monitoring globally"""
    query_monitor.disable()

def reset_query_monitoring():
    """Reset query monitoring counters"""
    query_monitor.reset()

def get_query_stats():
    """Get current query monitoring statistics"""
    return query_monitor.get_stats()

def toggle_query_monitoring():
    """Toggle query monitoring on/off"""
    if query_monitor.enabled:
        disable_query_monitoring()
        return False
    else:
        enable_query_monitoring() 
        return True

def is_query_monitoring_enabled():
    """Check if query monitoring is currently enabled"""
    return query_monitor.enabled

def set_query_monitoring(enabled: bool):
    """Set query monitoring state"""
    if enabled:
        enable_query_monitoring()
    else:
        disable_query_monitoring()