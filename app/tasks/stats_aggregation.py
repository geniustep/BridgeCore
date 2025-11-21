"""
Background tasks for statistics aggregation
"""
from celery import shared_task
from sqlalchemy import select, func, and_
from datetime import datetime, date, timedelta
from loguru import logger

from app.db.session import AsyncSessionLocal
from app.models.usage_log import UsageLog
from app.models.usage_stats import UsageStats
from app.models.tenant import Tenant, TenantStatus
import asyncio


@shared_task(name="aggregate_hourly_stats")
def aggregate_hourly_stats():
    """
    Aggregate hourly usage statistics for all tenants

    Runs every hour to create hourly statistics from raw usage logs
    """
    asyncio.run(_aggregate_hourly_stats())


async def _aggregate_hourly_stats():
    """Async implementation of hourly stats aggregation"""
    try:
        async with AsyncSessionLocal() as session:
            # Get current hour
            now = datetime.utcnow()
            hour_start = now.replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)

            logger.info(f"Aggregating hourly stats for {hour_start.strftime('%Y-%m-%d %H:00')}")

            # Get all active tenants
            tenants_query = select(Tenant).where(Tenant.status == TenantStatus.ACTIVE)
            tenants_result = await session.execute(tenants_query)
            tenants = tenants_result.scalars().all()

            aggregated_count = 0

            for tenant in tenants:
                # Query usage logs for this tenant in this hour
                logs_query = select(UsageLog).where(
                    and_(
                        UsageLog.tenant_id == tenant.id,
                        UsageLog.timestamp >= hour_start,
                        UsageLog.timestamp < hour_end
                    )
                )
                logs_result = await session.execute(logs_query)
                logs = logs_result.scalars().all()

                if not logs:
                    continue

                # Calculate statistics
                total_requests = len(logs)
                successful_requests = sum(1 for log in logs if 200 <= log.status_code < 300)
                failed_requests = total_requests - successful_requests

                total_data_transferred = sum(
                    (log.request_size_bytes or 0) + (log.response_size_bytes or 0)
                    for log in logs
                )

                response_times = [log.response_time_ms for log in logs if log.response_time_ms]
                avg_response_time = sum(response_times) // len(response_times) if response_times else 0

                # Get unique users
                unique_users = len(set(log.user_id for log in logs if log.user_id))

                # Get most used model
                model_counts = {}
                for log in logs:
                    if log.model_name:
                        model_counts[log.model_name] = model_counts.get(log.model_name, 0) + 1

                most_used_model = max(model_counts.items(), key=lambda x: x[1])[0] if model_counts else None

                # Check if stats already exist for this hour
                existing_stats_query = select(UsageStats).where(
                    and_(
                        UsageStats.tenant_id == tenant.id,
                        UsageStats.date == hour_start.date(),
                        UsageStats.hour == hour_start.hour
                    )
                )
                existing_result = await session.execute(existing_stats_query)
                existing_stats = existing_result.scalar_one_or_none()

                if existing_stats:
                    # Update existing stats
                    existing_stats.total_requests = total_requests
                    existing_stats.successful_requests = successful_requests
                    existing_stats.failed_requests = failed_requests
                    existing_stats.total_data_transferred_bytes = total_data_transferred
                    existing_stats.avg_response_time_ms = avg_response_time
                    existing_stats.unique_users = unique_users
                    existing_stats.most_used_model = most_used_model
                else:
                    # Create new stats
                    stats = UsageStats(
                        tenant_id=tenant.id,
                        date=hour_start.date(),
                        hour=hour_start.hour,
                        total_requests=total_requests,
                        successful_requests=successful_requests,
                        failed_requests=failed_requests,
                        total_data_transferred_bytes=total_data_transferred,
                        avg_response_time_ms=avg_response_time,
                        unique_users=unique_users,
                        most_used_model=most_used_model
                    )
                    session.add(stats)

                aggregated_count += 1

            await session.commit()

            logger.info(f"Hourly stats aggregation completed: {aggregated_count} tenants processed")

    except Exception as e:
        logger.error(f"Error aggregating hourly stats: {str(e)}")
        raise


@shared_task(name="aggregate_daily_stats")
def aggregate_daily_stats():
    """
    Aggregate daily usage statistics for all tenants

    Runs daily at midnight to create daily statistics from hourly stats
    """
    asyncio.run(_aggregate_daily_stats())


async def _aggregate_daily_stats():
    """Async implementation of daily stats aggregation"""
    try:
        async with AsyncSessionLocal() as session:
            # Get yesterday's date
            yesterday = date.today() - timedelta(days=1)

            logger.info(f"Aggregating daily stats for {yesterday}")

            # Get all active tenants
            tenants_query = select(Tenant).where(Tenant.status == TenantStatus.ACTIVE)
            tenants_result = await session.execute(tenants_query)
            tenants = tenants_result.scalars().all()

            aggregated_count = 0

            for tenant in tenants:
                # Get hourly stats for yesterday
                hourly_stats_query = select(UsageStats).where(
                    and_(
                        UsageStats.tenant_id == tenant.id,
                        UsageStats.date == yesterday,
                        UsageStats.hour.isnot(None)
                    )
                )
                hourly_result = await session.execute(hourly_stats_query)
                hourly_stats = hourly_result.scalars().all()

                if not hourly_stats:
                    continue

                # Aggregate hourly stats into daily
                total_requests = sum(stat.total_requests for stat in hourly_stats)
                successful_requests = sum(stat.successful_requests for stat in hourly_stats)
                failed_requests = sum(stat.failed_requests for stat in hourly_stats)
                total_data_transferred = sum(stat.total_data_transferred_bytes for stat in hourly_stats)

                # Calculate average response time (weighted by request count)
                total_weighted_response_time = sum(
                    stat.avg_response_time_ms * stat.total_requests
                    for stat in hourly_stats if stat.avg_response_time_ms
                )
                avg_response_time = total_weighted_response_time // total_requests if total_requests > 0 else 0

                # Get unique users (max from all hours)
                unique_users = max(stat.unique_users for stat in hourly_stats)

                # Get most used model
                model_counts = {}
                for stat in hourly_stats:
                    if stat.most_used_model:
                        model_counts[stat.most_used_model] = model_counts.get(stat.most_used_model, 0) + stat.total_requests

                most_used_model = max(model_counts.items(), key=lambda x: x[1])[0] if model_counts else None

                # Find peak hour
                peak_stat = max(hourly_stats, key=lambda stat: stat.total_requests)
                peak_hour = peak_stat.hour if peak_stat else None

                # Check if daily stats already exist
                existing_stats_query = select(UsageStats).where(
                    and_(
                        UsageStats.tenant_id == tenant.id,
                        UsageStats.date == yesterday,
                        UsageStats.hour.is_(None)
                    )
                )
                existing_result = await session.execute(existing_stats_query)
                existing_stats = existing_result.scalar_one_or_none()

                if existing_stats:
                    # Update existing daily stats
                    existing_stats.total_requests = total_requests
                    existing_stats.successful_requests = successful_requests
                    existing_stats.failed_requests = failed_requests
                    existing_stats.total_data_transferred_bytes = total_data_transferred
                    existing_stats.avg_response_time_ms = avg_response_time
                    existing_stats.unique_users = unique_users
                    existing_stats.most_used_model = most_used_model
                    existing_stats.peak_hour = peak_hour
                else:
                    # Create new daily stats
                    stats = UsageStats(
                        tenant_id=tenant.id,
                        date=yesterday,
                        hour=None,  # NULL for daily stats
                        total_requests=total_requests,
                        successful_requests=successful_requests,
                        failed_requests=failed_requests,
                        total_data_transferred_bytes=total_data_transferred,
                        avg_response_time_ms=avg_response_time,
                        unique_users=unique_users,
                        most_used_model=most_used_model,
                        peak_hour=peak_hour
                    )
                    session.add(stats)

                aggregated_count += 1

            await session.commit()

            logger.info(f"Daily stats aggregation completed: {aggregated_count} tenants processed")

    except Exception as e:
        logger.error(f"Error aggregating daily stats: {str(e)}")
        raise


@shared_task(name="cleanup_old_logs")
def cleanup_old_logs():
    """
    Clean up old usage logs (keep last 90 days)

    Runs daily to keep the database size manageable
    """
    asyncio.run(_cleanup_old_logs())


async def _cleanup_old_logs():
    """Async implementation of log cleanup"""
    try:
        async with AsyncSessionLocal() as session:
            # Delete logs older than 90 days
            cutoff_date = datetime.utcnow() - timedelta(days=90)

            logger.info(f"Cleaning up usage logs older than {cutoff_date.date()}")

            # Delete old usage logs
            from sqlalchemy import delete
            delete_query = delete(UsageLog).where(UsageLog.timestamp < cutoff_date)
            result = await session.execute(delete_query)
            await session.commit()

            deleted_count = result.rowcount

            logger.info(f"Cleanup completed: {deleted_count} old usage logs deleted")

    except Exception as e:
        logger.error(f"Error cleaning up old logs: {str(e)}")
        raise
