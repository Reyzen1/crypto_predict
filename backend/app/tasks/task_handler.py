# backend/app/tasks/task_handler.py
"""
Async Task Handler Utility for Celery - WINDOWS-SAFE VERSION
Provides proper event loop management for async operations in Celery tasks
"""

import asyncio
import nest_asyncio
import logging
import functools
from typing import Any, Callable, Dict, Awaitable
from datetime import datetime

# Enable nested asyncio for Celery compatibility
nest_asyncio.apply()

# Setup logging
logger = logging.getLogger(__name__)


class AsyncTaskHandler:
    """
    Handler for managing async operations within Celery tasks
    
    Provides proper event loop management to avoid "Event loop is closed" errors
    when running async code in Celery workers.
    """
    
    @staticmethod
    def run_async_task(async_func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        Execute async function in Celery task context
        
        Args:
            async_func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Any: Result of the async function
            
        Raises:
            Exception: If the async function fails
        """
        try:
            logger.info(f"Starting async task execution: {async_func.__name__}")
            
            # Try to get current event loop, create new one if needed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    logger.info("Event loop is closed, creating new one")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                logger.info("No event loop found, creating new one")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Execute the async function
            try:
                if loop.is_running():
                    # If loop is already running, use nest_asyncio
                    logger.info("Event loop is running, using nested execution")
                    result = loop.run_until_complete(async_func(*args, **kwargs))
                else:
                    # If loop is not running, run normally
                    logger.info("Event loop is not running, using normal execution")
                    result = loop.run_until_complete(async_func(*args, **kwargs))
                
                logger.info(f"Async task completed successfully: {async_func.__name__}")
                return result
                
            except Exception as e:
                logger.error(f"Async task failed: {async_func.__name__} - {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to execute async task {async_func.__name__}: {str(e)}")
            raise
    
    @staticmethod
    def async_task_wrapper(async_func: Callable[..., Awaitable[Dict[str, Any]]]):
        """
        Decorator to wrap async functions for Celery tasks
        
        Args:
            async_func: Async function to wrap
            
        Returns:
            Callable: Wrapped sync function
        """
        @functools.wraps(async_func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            """
            Wrapper function that handles async execution
            
            Returns:
                dict: Task execution result with metadata
            """
            task_start_time = datetime.utcnow()
            
            try:
                # Execute async function
                result = AsyncTaskHandler.run_async_task(async_func, *args, **kwargs)
                
                # Add metadata to result
                if isinstance(result, dict):
                    result.update({
                        'task_duration': (datetime.utcnow() - task_start_time).total_seconds(),
                        'task_completed_at': datetime.utcnow().isoformat(),
                        'status': 'success'
                    })
                else:
                    result = {
                        'result': result,
                        'task_duration': (datetime.utcnow() - task_start_time).total_seconds(),
                        'task_completed_at': datetime.utcnow().isoformat(),
                        'status': 'success'
                    }
                
                return result
                
            except Exception as e:
                logger.error(f"Task wrapper failed: {str(e)}")
                return {
                    'status': 'failed',
                    'error': str(e),
                    'task_duration': (datetime.utcnow() - task_start_time).total_seconds(),
                    'task_completed_at': datetime.utcnow().isoformat()
                }
        
        return wrapper


# Create global instance for easy import
async_task_handler = AsyncTaskHandler()


def celery_async_task(async_func: Callable[..., Awaitable[Dict[str, Any]]]):
    """
    Decorator for converting async functions to Celery-compatible sync functions
    
    Usage:
        @celery_async_task
        async def my_async_task():
            return await some_async_operation()
    
    Args:
        async_func: Async function to convert
        
    Returns:
        Callable: Sync function compatible with Celery
    """
    return AsyncTaskHandler.async_task_wrapper(async_func)


# Utility functions for common patterns

def safe_async_run(async_func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
    """
    Safely run async function with proper error handling
    
    Args:
        async_func: Async function to run
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Any: Function result or None if failed
    """
    try:
        return AsyncTaskHandler.run_async_task(async_func, *args, **kwargs)
    except Exception as e:
        logger.error(f"Safe async run failed: {str(e)}")
        return None


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Get current event loop or create new one if needed
    
    Returns:
        asyncio.AbstractEventLoop: Event loop instance
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


# Export main utilities
__all__ = [
    'AsyncTaskHandler',
    'async_task_handler', 
    'celery_async_task',
    'safe_async_run',
    'get_or_create_event_loop'
]