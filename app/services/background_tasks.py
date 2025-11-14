"""
Background Tasks Service
"""
from fastapi import BackgroundTasks
from typing import Callable, Any
from loguru import logger
import asyncio


class BackgroundTaskService:
    """
    Service for running tasks in the background

    Features:
    - Add tasks to background queue
    - Non-blocking execution
    - Task logging
    """

    @staticmethod
    def add_task(
        background_tasks: BackgroundTasks,
        func: Callable,
        *args,
        **kwargs
    ):
        """
        Add a task to background execution

        Args:
            background_tasks: FastAPI BackgroundTasks instance
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Example:
            BackgroundTaskService.add_task(
                background_tasks,
                send_notification,
                user_id=1,
                message="Hello"
            )
        """
        background_tasks.add_task(func, *args, **kwargs)
        logger.info(f"Background task added: {func.__name__}")

    @staticmethod
    async def send_notification(user_id: int, message: str):
        """
        Example: Send notification in background

        Args:
            user_id: User ID
            message: Notification message
        """
        logger.info(f"Sending notification to user {user_id}: {message}")
        # Notification logic here
        await asyncio.sleep(1)  # Simulate async operation
        logger.info(f"Notification sent to user {user_id}")

    @staticmethod
    async def sync_data_task(
        system_id: int,
        model: str,
        data: dict
    ):
        """
        Example: Sync data in background

        Args:
            system_id: System ID
            model: Model name
            data: Data to sync
        """
        logger.info(f"Syncing data for system {system_id}/{model}")
        # Sync logic here
        await asyncio.sleep(2)  # Simulate async operation
        logger.info(f"Data synced for system {system_id}/{model}")

    @staticmethod
    async def cache_warmup(cache_service, keys: list):
        """
        Example: Warm up cache in background

        Args:
            cache_service: Cache service instance
            keys: List of keys to warm up
        """
        logger.info(f"Warming up cache for {len(keys)} keys")
        for key in keys:
            # Cache warmup logic
            await asyncio.sleep(0.1)
        logger.info(f"Cache warmup completed for {len(keys)} keys")

    @staticmethod
    async def cleanup_old_logs(days: int = 30):
        """
        Example: Cleanup old audit logs

        Args:
            days: Number of days to keep
        """
        logger.info(f"Cleaning up audit logs older than {days} days")
        # Cleanup logic here
        await asyncio.sleep(1)
        logger.info("Audit log cleanup completed")
