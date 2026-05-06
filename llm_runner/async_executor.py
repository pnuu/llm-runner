"""Asyncio-based task execution with timeout enforcement"""
import asyncio
from typing import Any, Callable, Optional, Coroutine


class TimeoutError(Exception):
    """Raised when an async operation exceeds its timeout"""
    pass


async def async_with_timeout(
    coro: Coroutine,
    timeout_sec: float
) -> Any:
    """
    Execute an async coroutine with timeout enforcement.
    
    Args:
        coro: Coroutine to execute
        timeout_sec: Timeout in seconds
        
    Returns:
        Result from coroutine
        
    Raises:
        TimeoutError: If coroutine exceeds timeout
        Any exception raised by the coroutine
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_sec)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation exceeded timeout of {timeout_sec}s")


class AsyncTaskRunner:
    """
    Manages concurrent async task execution with timeout enforcement.
    
    Provides a clean interface for running tasks with individual or default timeouts.
    """
    
    def __init__(self, default_timeout: float = 30.0):
        """
        Initialize task runner.
        
        Args:
            default_timeout: Default timeout in seconds for tasks
        """
        self.default_timeout = default_timeout
        self.active_tasks = {}
        self.completed_tasks = {}
    
    async def run_task(
        self,
        task_id: str,
        coro: Coroutine,
        timeout_sec: Optional[float] = None
    ) -> Any:
        """
        Run a task with timeout enforcement.
        
        Args:
            task_id: Unique identifier for this task
            coro: Coroutine to execute
            timeout_sec: Timeout override (uses default_timeout if None)
            
        Returns:
            Result from coroutine
            
        Raises:
            TimeoutError: If task exceeds timeout
            Any exception raised by the coroutine
        """
        timeout = timeout_sec if timeout_sec is not None else self.default_timeout
        
        try:
            self.active_tasks[task_id] = coro
            result = await async_with_timeout(coro, timeout)
            self.completed_tasks[task_id] = ("success", result)
            return result
        except TimeoutError as e:
            self.completed_tasks[task_id] = ("timeout", None)
            raise
        except Exception as e:
            self.completed_tasks[task_id] = ("error", str(e))
            raise
        finally:
            self.active_tasks.pop(task_id, None)
    
    def get_active_tasks(self) -> dict:
        """Get currently active tasks"""
        return self.active_tasks.copy()
    
    def get_completed_tasks(self) -> dict:
        """Get task completion history"""
        return self.completed_tasks.copy()
    
    def clear_history(self) -> None:
        """Clear task history"""
        self.completed_tasks.clear()
