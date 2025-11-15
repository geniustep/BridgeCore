"""
Audit Logging Service
"""
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository


class AuditService:
    """
    Service for logging all operations (Audit Trail)

    Features:
    - Log all CRUD operations
    - Track user activity
    - Monitor system operations
    - Identify failed operations
    """

    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo

    async def log_operation(
        self,
        user_id: int,
        system_id: Optional[int],
        action: str,
        model: Optional[str] = None,
        record_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        duration_ms: Optional[int] = None
    ):
        """
        Log an operation to audit trail

        Args:
            user_id: User who performed the operation
            system_id: System where operation was performed
            action: Action type (create, read, update, delete)
            model: Model/entity name
            record_id: Record ID in external system
            request_data: Request payload
            response_data: Response data
            status: Operation status (success, error)
            error_message: Error message if failed
            ip_address: Client IP address
            user_agent: Client user agent
            duration_ms: Operation duration in milliseconds

        Example:
            await audit_service.log_operation(
                user_id=1,
                system_id=1,
                action="create",
                model="res.partner",
                record_id="42",
                request_data={"name": "Ahmed"},
                status="success"
            )
        """
        log_entry = AuditLog(
            user_id=user_id,
            system_id=system_id,
            action=action,
            model=model,
            record_id=record_id,
            request_data=request_data,
            response_data=response_data,
            status=status,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms
        )

        await self.audit_repo.create(log_entry)

        logger.info(
            f"Audit: User {user_id} performed {action} on system {system_id}/{model}/{record_id} - {status}"
        )

    async def get_user_activity(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ):
        """
        Get user activity log

        Args:
            user_id: User ID
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of audit log entries
        """
        return await self.audit_repo.get_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset
        )

    async def get_system_activity(
        self,
        system_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ):
        """
        Get system activity log

        Args:
            system_id: System ID
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of records

        Returns:
            List of audit log entries
        """
        return await self.audit_repo.get_by_system(
            system_id=system_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

    async def get_failed_operations(
        self,
        system_id: Optional[int] = None,
        hours: int = 24
    ):
        """
        Get failed operations within the last N hours

        Args:
            system_id: Optional system ID to filter by
            hours: Number of hours to look back

        Returns:
            List of failed audit log entries
        """
        return await self.audit_repo.get_failed_operations(
            system_id=system_id,
            hours=hours
        )
