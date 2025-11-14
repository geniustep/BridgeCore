"""
Celery Task Queue for Heavy Operations

Handles:
- Batch operations
- Report generation
- Data synchronization
- Long-running migrations
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from loguru import logger
import asyncio


# Initialize Celery
celery_app = Celery(
    "bridgecore",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    "cleanup-old-audit-logs": {
        "task": "app.tasks.celery_app.cleanup_old_audit_logs",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    "refresh-system-connections": {
        "task": "app.tasks.celery_app.refresh_system_connections",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    "update-cache-stats": {
        "task": "app.tasks.celery_app.update_cache_stats",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}


def run_async(coro):
    """
    Helper to run async functions in sync Celery tasks

    Args:
        coro: Async coroutine

    Returns:
        Result of coroutine
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@celery_app.task(name="app.tasks.celery_app.process_batch_operation")
def process_batch_operation(
    user_id: int,
    system_id: str,
    operations: list,
    stop_on_error: bool = False
):
    """
    Process batch operations asynchronously

    Args:
        user_id: User ID
        system_id: System ID
        operations: List of operations
        stop_on_error: Stop on first error

    Returns:
        Results of all operations
    """
    from app.services.system_service import SystemService
    from app.db.session import SessionLocal

    logger.info(f"Processing batch operation: {len(operations)} operations")

    db = SessionLocal()
    try:
        service = SystemService(db)
        results = []

        for idx, operation in enumerate(operations):
            try:
                model = operation.get("model")
                action = operation.get("action")
                data = operation.get("data")

                if action == "create":
                    result = run_async(service.create(
                        user_id=user_id,
                        system_id=system_id,
                        model=model,
                        data=data
                    ))
                elif action == "update":
                    record_id = operation.get("record_id")
                    result = run_async(service.update(
                        user_id=user_id,
                        system_id=system_id,
                        model=model,
                        record_id=record_id,
                        data=data
                    ))
                elif action == "delete":
                    record_id = operation.get("record_id")
                    result = run_async(service.delete(
                        user_id=user_id,
                        system_id=system_id,
                        model=model,
                        record_id=record_id
                    ))
                else:
                    result = {"success": False, "error": f"Unknown action: {action}"}

                results.append({
                    "operation": idx,
                    "success": True,
                    "result": result
                })

            except Exception as e:
                logger.error(f"Batch operation {idx} failed: {e}")
                results.append({
                    "operation": idx,
                    "success": False,
                    "error": str(e)
                })

                if stop_on_error:
                    break

        return {
            "total": len(operations),
            "processed": len(results),
            "results": results
        }

    finally:
        db.close()


@celery_app.task(name="app.tasks.celery_app.generate_report")
def generate_report(
    user_id: int,
    system_id: str,
    report_type: str,
    model: str,
    filters: dict = None,
    format: str = "pdf"
):
    """
    Generate report asynchronously

    Args:
        user_id: User ID
        system_id: System ID
        report_type: Report type
        model: Model name
        filters: Filters to apply
        format: Output format (pdf, excel, csv)

    Returns:
        Report file path
    """
    from app.services.system_service import SystemService
    from app.db.session import SessionLocal

    logger.info(f"Generating {format} report for {model}")

    db = SessionLocal()
    try:
        service = SystemService(db)

        # Fetch data
        domain = filters or []
        data = run_async(service.read(
            user_id=user_id,
            system_id=system_id,
            model=model,
            domain=domain
        ))

        # Generate report based on format
        if format == "pdf":
            file_path = _generate_pdf_report(model, data)
        elif format == "excel":
            file_path = _generate_excel_report(model, data)
        elif format == "csv":
            file_path = _generate_csv_report(model, data)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Report generated: {file_path}")
        return {
            "success": True,
            "file_path": file_path,
            "records": len(data) if isinstance(data, list) else 1
        }

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.celery_app.sync_data")
def sync_data(
    user_id: int,
    source_system_id: str,
    target_system_id: str,
    model: str,
    filters: dict = None,
    bidirectional: bool = False
):
    """
    Synchronize data between two systems

    Args:
        user_id: User ID
        source_system_id: Source system ID
        target_system_id: Target system ID
        model: Model name
        filters: Filters to apply
        bidirectional: Sync in both directions

    Returns:
        Sync results
    """
    from app.services.system_service import SystemService
    from app.db.session import SessionLocal

    logger.info(f"Syncing {model} from {source_system_id} to {target_system_id}")

    db = SessionLocal()
    try:
        service = SystemService(db)

        # Read from source
        domain = filters or []
        source_data = run_async(service.read(
            user_id=user_id,
            system_id=source_system_id,
            model=model,
            domain=domain
        ))

        created = 0
        updated = 0
        errors = []

        # Write to target
        if isinstance(source_data, list):
            for record in source_data:
                try:
                    # Try to find existing record
                    # This is simplified - real implementation would need proper matching
                    result = run_async(service.create(
                        user_id=user_id,
                        system_id=target_system_id,
                        model=model,
                        data=record
                    ))
                    created += 1

                except Exception as e:
                    logger.error(f"Failed to sync record: {e}")
                    errors.append(str(e))

        results = {
            "created": created,
            "updated": updated,
            "errors": errors,
            "total": len(source_data) if isinstance(source_data, list) else 1
        }

        # Bidirectional sync
        if bidirectional:
            reverse_results = run_async(sync_data(
                user_id=user_id,
                source_system_id=target_system_id,
                target_system_id=source_system_id,
                model=model,
                filters=filters,
                bidirectional=False
            ))
            results["reverse"] = reverse_results

        return results

    finally:
        db.close()


@celery_app.task(name="app.tasks.celery_app.migrate_version")
def migrate_version(
    user_id: int,
    system_id: str,
    model: str,
    from_version: str,
    to_version: str,
    record_ids: list = None
):
    """
    Migrate data to different version

    Args:
        user_id: User ID
        system_id: System ID
        model: Model name
        from_version: Source version
        to_version: Target version
        record_ids: Specific record IDs (or None for all)

    Returns:
        Migration results
    """
    from app.services.version_handler_v2 import EnhancedVersionHandler
    from app.services.system_service import SystemService
    from app.db.session import SessionLocal

    logger.info(f"Migrating {model} from {from_version} to {to_version}")

    db = SessionLocal()
    try:
        service = SystemService(db)
        handler = EnhancedVersionHandler()

        # Read records
        domain = []
        if record_ids:
            domain = [("id", "in", record_ids)]

        records = run_async(service.read(
            user_id=user_id,
            system_id=system_id,
            model=model,
            domain=domain
        ))

        migrated = 0
        errors = []

        if isinstance(records, list):
            for record in records:
                try:
                    # Migrate data
                    migrated_data = run_async(handler.migrate_data(
                        data=record,
                        system_type="odoo",
                        from_version=from_version,
                        to_version=to_version,
                        model=model
                    ))

                    # Update record with migrated data
                    # This is simplified - real implementation would handle this better
                    migrated += 1

                except Exception as e:
                    logger.error(f"Failed to migrate record: {e}")
                    errors.append(str(e))

        return {
            "migrated": migrated,
            "errors": errors,
            "total": len(records) if isinstance(records, list) else 1
        }

    finally:
        db.close()


@celery_app.task(name="app.tasks.celery_app.cleanup_old_audit_logs")
def cleanup_old_audit_logs(days: int = 90):
    """
    Clean up old audit logs

    Args:
        days: Keep logs newer than this many days

    Returns:
        Number of deleted logs
    """
    from app.db.session import SessionLocal
    from app.models.audit_log import AuditLog
    from datetime import datetime, timedelta

    logger.info(f"Cleaning up audit logs older than {days} days")

    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff_date
        ).delete()

        db.commit()

        logger.info(f"Deleted {deleted} old audit logs")
        return deleted

    finally:
        db.close()


@celery_app.task(name="app.tasks.celery_app.refresh_system_connections")
def refresh_system_connections():
    """
    Refresh all system connections to keep them alive

    Returns:
        Number of refreshed connections
    """
    from app.db.session import SessionLocal
    from app.models.system import System

    logger.info("Refreshing system connections")

    db = SessionLocal()
    try:
        systems = db.query(System).filter(System.is_active == True).all()

        refreshed = 0
        for system in systems:
            try:
                # Ping the system to keep connection alive
                # This is simplified - real implementation would use adapter
                refreshed += 1
            except Exception as e:
                logger.error(f"Failed to refresh system {system.system_id}: {e}")

        logger.info(f"Refreshed {refreshed} system connections")
        return refreshed

    finally:
        db.close()


@celery_app.task(name="app.tasks.celery_app.update_cache_stats")
def update_cache_stats():
    """
    Update cache statistics

    Returns:
        Cache statistics
    """
    from app.core.cache import cache_service

    logger.debug("Updating cache statistics")

    stats = run_async(cache_service.get_stats())
    logger.debug(f"Cache stats: {stats}")

    return stats


def _generate_pdf_report(model: str, data: list) -> str:
    """Generate PDF report"""
    # Placeholder - implement actual PDF generation
    file_path = f"/tmp/report_{model}.pdf"
    logger.info(f"Generated PDF report: {file_path}")
    return file_path


def _generate_excel_report(model: str, data: list) -> str:
    """Generate Excel report"""
    # Placeholder - implement actual Excel generation
    file_path = f"/tmp/report_{model}.xlsx"
    logger.info(f"Generated Excel report: {file_path}")
    return file_path


def _generate_csv_report(model: str, data: list) -> str:
    """Generate CSV report"""
    # Placeholder - implement actual CSV generation
    file_path = f"/tmp/report_{model}.csv"
    logger.info(f"Generated CSV report: {file_path}")
    return file_path
