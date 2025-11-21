"""
Logging service for usage and error logs
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.repositories.log_repository import (
    UsageLogRepository,
    ErrorLogRepository,
    UsageStatsRepository
)
from app.models.usage_log import UsageLog
from app.models.error_log import ErrorLog, ErrorSeverity
from app.models.usage_stats import UsageStats


class LoggingService:
    """Service for managing usage and error logs"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.usage_repo = UsageLogRepository(session)
        self.error_repo = ErrorLogRepository(session)
        self.stats_repo = UsageStatsRepository(session)

    # ========================================================================
    # Usage Logs
    # ========================================================================

    async def get_usage_logs(
        self,
        tenant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> List[UsageLog]:
        """
        Get usage logs with filters

        Args:
            tenant_id: Filter by tenant (required for tenant-specific logs)
            skip: Number of records to skip
            limit: Maximum records to return
            start_date: Filter from this date
            end_date: Filter until this date
            method: Filter by HTTP method
            status_code: Filter by status code

        Returns:
            List of usage logs
        """
        if tenant_id:
            return await self.usage_repo.get_tenant_logs(
                tenant_id=tenant_id,
                skip=skip,
                limit=limit,
                start_date=start_date,
                end_date=end_date
            )
        else:
            # Admin: get all logs
            return await self.usage_repo.get_multi(
                skip=skip,
                limit=limit,
                order_by="-timestamp"
            )

    async def get_usage_stats_summary(
        self,
        tenant_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage statistics summary for a tenant

        Args:
            tenant_id: Tenant UUID
            days: Number of days to analyze (default: 30)

        Returns:
            Dictionary with usage statistics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get total requests
        total_requests = await self.usage_repo.count_tenant_requests(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )

        # Get logs for analysis
        logs = await self.usage_repo.get_tenant_logs(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Analyze last 10k requests
        )

        if not logs:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time_ms": 0,
                "total_data_transferred_mb": 0,
                "most_used_endpoint": None,
                "period_days": days
            }

        # Calculate metrics
        successful = sum(1 for log in logs if 200 <= log.status_code < 300)
        failed = sum(1 for log in logs if log.status_code >= 400)

        avg_response_time = sum(log.response_time_ms or 0 for log in logs) / len(logs) if logs else 0

        total_data = sum(
            (log.request_size_bytes or 0) + (log.response_size_bytes or 0)
            for log in logs
        )
        total_data_mb = total_data / (1024 * 1024)

        # Most used endpoint
        endpoint_counts = {}
        for log in logs:
            endpoint_counts[log.endpoint] = endpoint_counts.get(log.endpoint, 0) + 1

        most_used_endpoint = max(endpoint_counts.items(), key=lambda x: x[1])[0] if endpoint_counts else None

        return {
            "total_requests": total_requests,
            "successful_requests": successful,
            "failed_requests": failed,
            "avg_response_time_ms": round(avg_response_time, 2),
            "total_data_transferred_mb": round(total_data_mb, 2),
            "most_used_endpoint": most_used_endpoint,
            "period_days": days
        }

    # ========================================================================
    # Error Logs
    # ========================================================================

    async def log_error(
        self,
        tenant_id: UUID,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> ErrorLog:
        """
        Log an error

        Args:
            tenant_id: Tenant UUID
            error_type: Type of error
            error_message: Error message
            stack_trace: Optional stack trace
            endpoint: Endpoint where error occurred
            method: HTTP method
            request_data: Request data that caused error
            severity: Error severity level

        Returns:
            Created error log
        """
        error_log = ErrorLog(
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            endpoint=endpoint,
            method=method,
            request_data=request_data,
            severity=severity,
            is_resolved=False
        )

        return await self.error_repo.create(error_log)

    async def get_error_logs(
        self,
        tenant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        severity: Optional[ErrorSeverity] = None,
        unresolved_only: bool = False
    ) -> List[ErrorLog]:
        """
        Get error logs with filters

        Args:
            tenant_id: Filter by tenant
            skip: Number of records to skip
            limit: Maximum records to return
            severity: Filter by severity
            unresolved_only: Only show unresolved errors

        Returns:
            List of error logs
        """
        if tenant_id:
            return await self.error_repo.get_tenant_errors(
                tenant_id=tenant_id,
                skip=skip,
                limit=limit,
                severity=severity,
                unresolved_only=unresolved_only
            )
        else:
            # Admin: get all errors
            filters = {}
            if severity:
                filters["severity"] = severity
            if unresolved_only:
                filters["is_resolved"] = False

            return await self.error_repo.get_multi(
                skip=skip,
                limit=limit,
                filters=filters,
                order_by="-timestamp"
            )

    async def resolve_error(
        self,
        error_id: int,
        resolved_by: UUID,
        resolution_notes: Optional[str] = None
    ) -> Optional[ErrorLog]:
        """
        Mark an error as resolved

        Args:
            error_id: Error log ID
            resolved_by: Admin UUID who resolved the error
            resolution_notes: Notes about the resolution

        Returns:
            Updated error log or None
        """
        error = await self.error_repo.get_by_id(error_id)
        if not error:
            return None

        error.is_resolved = True
        error.resolved_at = datetime.utcnow()
        error.resolved_by = resolved_by
        error.resolution_notes = resolution_notes

        await self.session.commit()
        await self.session.refresh(error)
        return error

    async def get_error_summary(
        self,
        tenant_id: UUID,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get error summary for a tenant

        Args:
            tenant_id: Tenant UUID
            days: Number of days to analyze

        Returns:
            Error statistics
        """
        unresolved_count = await self.error_repo.count_unresolved_errors(tenant_id)

        # Get recent errors
        errors = await self.error_repo.get_tenant_errors(
            tenant_id=tenant_id,
            limit=1000
        )

        # Count by severity
        severity_counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0
        }

        for error in errors:
            severity_counts[error.severity.value] += 1

        # Most common error type
        error_type_counts = {}
        for error in errors:
            error_type_counts[error.error_type] = error_type_counts.get(error.error_type, 0) + 1

        most_common_error = max(error_type_counts.items(), key=lambda x: x[1])[0] if error_type_counts else None

        return {
            "total_errors": len(errors),
            "unresolved_errors": unresolved_count,
            "severity_breakdown": severity_counts,
            "most_common_error_type": most_common_error,
            "period_days": days
        }
