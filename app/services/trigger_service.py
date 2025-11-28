"""
Trigger service for automation management
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from loguru import logger

from app.models.trigger import Trigger, TriggerExecution, TriggerStatus, TriggerEvent, TriggerActionType
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.schemas.trigger_schemas import TriggerCreate, TriggerUpdate


class TriggerService:
    """Service for managing triggers"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # CRUD Operations
    # ========================================================================

    async def create_trigger(
        self,
        tenant_id: UUID,
        trigger_data: TriggerCreate
    ) -> Trigger:
        """Create a new trigger"""
        trigger = Trigger(
            tenant_id=tenant_id,
            name=trigger_data.name,
            description=trigger_data.description,
            model=trigger_data.model,
            event=trigger_data.event,
            condition=trigger_data.condition or [],
            action_type=trigger_data.action_type,
            action_config=trigger_data.action_config,
            schedule_cron=trigger_data.schedule_cron,
            schedule_timezone=trigger_data.schedule_timezone or "UTC",
            is_enabled=trigger_data.is_enabled,
            priority=trigger_data.priority,
            max_executions_per_hour=trigger_data.max_executions_per_hour,
            status=TriggerStatus.ACTIVE
        )

        # Calculate next run time for scheduled triggers
        if trigger.event == TriggerEvent.SCHEDULED and trigger.schedule_cron:
            trigger.next_run_at = self._calculate_next_run(trigger.schedule_cron)

        self.db.add(trigger)
        await self.db.commit()
        await self.db.refresh(trigger)

        logger.info(f"Created trigger: {trigger.name} for tenant {tenant_id}")
        return trigger

    async def get_trigger(self, trigger_id: UUID, tenant_id: UUID) -> Optional[Trigger]:
        """Get a trigger by ID"""
        query = select(Trigger).where(
            and_(
                Trigger.id == trigger_id,
                Trigger.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_triggers(
        self,
        tenant_id: UUID,
        model: Optional[str] = None,
        event: Optional[TriggerEvent] = None,
        status: Optional[TriggerStatus] = None,
        is_enabled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Trigger], int]:
        """List triggers with filters"""
        query = select(Trigger).where(Trigger.tenant_id == tenant_id)

        if model:
            query = query.where(Trigger.model == model)
        if event:
            query = query.where(Trigger.event == event)
        if status:
            query = query.where(Trigger.status == status)
        if is_enabled is not None:
            query = query.where(Trigger.is_enabled == is_enabled)

        # Count total
        count_query = select(func.count(Trigger.id)).where(Trigger.tenant_id == tenant_id)
        if model:
            count_query = count_query.where(Trigger.model == model)
        if event:
            count_query = count_query.where(Trigger.event == event)
        if status:
            count_query = count_query.where(Trigger.status == status)
        if is_enabled is not None:
            count_query = count_query.where(Trigger.is_enabled == is_enabled)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(Trigger.priority, Trigger.created_at.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        triggers = list(result.scalars().all())

        return triggers, total

    async def update_trigger(
        self,
        trigger_id: UUID,
        tenant_id: UUID,
        trigger_data: TriggerUpdate
    ) -> Optional[Trigger]:
        """Update a trigger"""
        trigger = await self.get_trigger(trigger_id, tenant_id)
        if not trigger:
            return None

        update_data = trigger_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(trigger, field, value)

        # Recalculate next run time if schedule changed
        if trigger.event == TriggerEvent.SCHEDULED and trigger.schedule_cron:
            trigger.next_run_at = self._calculate_next_run(trigger.schedule_cron)

        await self.db.commit()
        await self.db.refresh(trigger)

        logger.info(f"Updated trigger: {trigger.name}")
        return trigger

    async def delete_trigger(self, trigger_id: UUID, tenant_id: UUID) -> bool:
        """Delete a trigger"""
        trigger = await self.get_trigger(trigger_id, tenant_id)
        if not trigger:
            return False

        await self.db.delete(trigger)
        await self.db.commit()

        logger.info(f"Deleted trigger: {trigger.name}")
        return True

    async def toggle_trigger(
        self,
        trigger_id: UUID,
        tenant_id: UUID,
        is_enabled: bool
    ) -> Optional[Trigger]:
        """Toggle trigger enabled status"""
        trigger = await self.get_trigger(trigger_id, tenant_id)
        if not trigger:
            return None

        trigger.is_enabled = is_enabled
        if is_enabled:
            trigger.status = TriggerStatus.ACTIVE
        else:
            trigger.status = TriggerStatus.INACTIVE

        await self.db.commit()
        await self.db.refresh(trigger)

        logger.info(f"Toggled trigger {trigger.name} to {'enabled' if is_enabled else 'disabled'}")
        return trigger

    # ========================================================================
    # Execution Operations
    # ========================================================================

    async def execute_trigger(
        self,
        trigger: Trigger,
        record_id: Optional[int] = None,
        record_data: Optional[Dict[str, Any]] = None,
        test_mode: bool = False
    ) -> TriggerExecution:
        """Execute a trigger and record the result"""
        started_at = datetime.utcnow()

        execution = TriggerExecution(
            trigger_id=trigger.id,
            tenant_id=trigger.tenant_id,
            record_id=record_id,
            record_data=record_data,
            started_at=started_at,
            success=False
        )

        try:
            # Check rate limit
            if not await self._check_rate_limit(trigger):
                execution.success = False
                execution.error_message = "Rate limit exceeded"
                return execution

            # Execute based on action type
            if not test_mode:
                result = await self._perform_action(trigger, record_id, record_data)
                execution.result = result
                execution.success = True

                # Update trigger metrics
                trigger.execution_count += 1
                trigger.success_count += 1
                trigger.last_run_at = datetime.utcnow()
                trigger.current_hour_executions += 1
            else:
                execution.result = {"test_mode": True, "would_execute": trigger.action_config}
                execution.success = True

        except Exception as e:
            execution.success = False
            execution.error_message = str(e)

            # Update trigger error info
            trigger.failure_count += 1
            trigger.last_error = str(e)
            trigger.last_error_at = datetime.utcnow()

            if trigger.failure_count >= 10:
                trigger.status = TriggerStatus.ERROR

            logger.error(f"Trigger execution failed: {trigger.name} - {str(e)}")

        finally:
            execution.completed_at = datetime.utcnow()
            execution.duration_ms = int((execution.completed_at - started_at).total_seconds() * 1000)

            self.db.add(execution)
            await self.db.commit()
            await self.db.refresh(execution)

        return execution

    async def execute_manual(
        self,
        trigger_id: UUID,
        tenant_id: UUID,
        record_ids: Optional[List[int]] = None,
        test_mode: bool = False
    ) -> List[TriggerExecution]:
        """Manually execute a trigger"""
        trigger = await self.get_trigger(trigger_id, tenant_id)
        if not trigger:
            raise ValueError("Trigger not found")

        if not trigger.is_enabled:
            raise ValueError("Trigger is disabled")

        executions = []
        if record_ids:
            for record_id in record_ids:
                execution = await self.execute_trigger(
                    trigger=trigger,
                    record_id=record_id,
                    test_mode=test_mode
                )
                executions.append(execution)
        else:
            execution = await self.execute_trigger(
                trigger=trigger,
                test_mode=test_mode
            )
            executions.append(execution)

        return executions

    async def get_execution_history(
        self,
        trigger_id: UUID,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[TriggerExecution], int]:
        """Get trigger execution history"""
        query = select(TriggerExecution).where(
            and_(
                TriggerExecution.trigger_id == trigger_id,
                TriggerExecution.tenant_id == tenant_id
            )
        )

        # Count total
        count_query = select(func.count(TriggerExecution.id)).where(
            and_(
                TriggerExecution.trigger_id == trigger_id,
                TriggerExecution.tenant_id == tenant_id
            )
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(TriggerExecution.created_at.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        executions = list(result.scalars().all())

        return executions, total

    async def get_trigger_stats(self, trigger_id: UUID, tenant_id: UUID) -> Dict[str, Any]:
        """Get trigger statistics"""
        trigger = await self.get_trigger(trigger_id, tenant_id)
        if not trigger:
            return {}

        # Get today's and this week's executions
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)

        today_count_query = select(func.count(TriggerExecution.id)).where(
            and_(
                TriggerExecution.trigger_id == trigger_id,
                TriggerExecution.created_at >= today
            )
        )
        week_count_query = select(func.count(TriggerExecution.id)).where(
            and_(
                TriggerExecution.trigger_id == trigger_id,
                TriggerExecution.created_at >= week_ago
            )
        )

        # Average duration
        avg_duration_query = select(func.avg(TriggerExecution.duration_ms)).where(
            and_(
                TriggerExecution.trigger_id == trigger_id,
                TriggerExecution.duration_ms.isnot(None)
            )
        )

        today_result = await self.db.execute(today_count_query)
        week_result = await self.db.execute(week_count_query)
        avg_result = await self.db.execute(avg_duration_query)

        success_rate = 0
        if trigger.execution_count > 0:
            success_rate = (trigger.success_count / trigger.execution_count) * 100

        return {
            "trigger_id": trigger.id,
            "name": trigger.name,
            "total_executions": trigger.execution_count,
            "successful_executions": trigger.success_count,
            "failed_executions": trigger.failure_count,
            "success_rate": round(success_rate, 2),
            "avg_duration_ms": avg_result.scalar(),
            "last_execution": trigger.last_run_at,
            "executions_today": today_result.scalar() or 0,
            "executions_this_week": week_result.scalar() or 0
        }

    # ========================================================================
    # Event Processing
    # ========================================================================

    async def process_event(
        self,
        tenant_id: UUID,
        model: str,
        event: TriggerEvent,
        record_id: int,
        record_data: Optional[Dict[str, Any]] = None
    ) -> List[TriggerExecution]:
        """Process an Odoo event and execute matching triggers"""
        # Find matching triggers
        query = select(Trigger).where(
            and_(
                Trigger.tenant_id == tenant_id,
                Trigger.model == model,
                Trigger.event == event,
                Trigger.is_enabled == True,
                Trigger.status != TriggerStatus.ERROR
            )
        ).order_by(Trigger.priority)

        result = await self.db.execute(query)
        triggers = list(result.scalars().all())

        executions = []
        for trigger in triggers:
            # Check condition (domain filter)
            if trigger.condition and record_data:
                if not self._evaluate_condition(trigger.condition, record_data):
                    continue

            execution = await self.execute_trigger(
                trigger=trigger,
                record_id=record_id,
                record_data=record_data
            )
            executions.append(execution)

        return executions

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _check_rate_limit(self, trigger: Trigger) -> bool:
        """Check if trigger is within rate limit"""
        if trigger.current_hour_executions >= trigger.max_executions_per_hour:
            return False
        return True

    async def _perform_action(
        self,
        trigger: Trigger,
        record_id: Optional[int],
        record_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform the trigger action"""
        config = trigger.action_config

        if trigger.action_type == TriggerActionType.NOTIFICATION:
            return await self._action_notification(trigger, record_id, record_data, config)
        elif trigger.action_type == TriggerActionType.WEBHOOK:
            return await self._action_webhook(trigger, record_id, record_data, config)
        elif trigger.action_type == TriggerActionType.EMAIL:
            return await self._action_email(trigger, record_id, record_data, config)
        elif trigger.action_type == TriggerActionType.ODOO_METHOD:
            return await self._action_odoo_method(trigger, record_id, record_data, config)
        else:
            return {"status": "unsupported_action_type"}

    async def _action_notification(
        self,
        trigger: Trigger,
        record_id: Optional[int],
        record_data: Optional[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create notification action"""
        from app.services.notification_service import NotificationService

        title = self._render_template(config.get("title", ""), record_data)
        message = self._render_template(config.get("message", ""), record_data)
        user_ids = config.get("user_ids", [])

        notification_service = NotificationService(self.db)
        notifications = []

        for user_id in user_ids:
            notification = Notification(
                tenant_id=trigger.tenant_id,
                user_id=user_id,
                title=title,
                message=message,
                type=NotificationType.INFO,
                priority=NotificationPriority.NORMAL,
                related_model=trigger.model,
                related_id=record_id,
                source="trigger",
                source_id=trigger.id
            )
            self.db.add(notification)
            notifications.append(str(notification.id))

        await self.db.commit()
        return {"notifications_created": len(notifications), "notification_ids": notifications}

    async def _action_webhook(
        self,
        trigger: Trigger,
        record_id: Optional[int],
        record_data: Optional[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute webhook action"""
        import httpx

        url = config.get("url")
        method = config.get("method", "POST")
        headers = config.get("headers", {})

        # Prepare payload
        payload = {
            "trigger_id": str(trigger.id),
            "trigger_name": trigger.name,
            "model": trigger.model,
            "event": trigger.event.value,
            "record_id": record_id,
            "record_data": record_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            return {
                "status_code": response.status_code,
                "response": response.text[:500]  # Limit response size
            }

    async def _action_email(
        self,
        trigger: Trigger,
        record_id: Optional[int],
        record_data: Optional[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send email action"""
        # TODO: Implement email sending
        to = config.get("to", [])
        subject = self._render_template(config.get("subject", ""), record_data)
        body = self._render_template(config.get("body_template", ""), record_data)

        return {
            "status": "email_queued",
            "to": to,
            "subject": subject
        }

    async def _action_odoo_method(
        self,
        trigger: Trigger,
        record_id: Optional[int],
        record_data: Optional[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Odoo method action"""
        # TODO: Implement Odoo method call via adapter
        method = config.get("method")
        args = config.get("args", [])
        kwargs = config.get("kwargs", {})

        return {
            "status": "odoo_method_queued",
            "method": method,
            "record_id": record_id
        }

    def _render_template(self, template: str, data: Optional[Dict[str, Any]]) -> str:
        """Simple template rendering for {{field}} placeholders"""
        if not data or not template:
            return template

        result = template
        for key, value in data.items():
            placeholder = "{{" + f"record.{key}" + "}}"
            result = result.replace(placeholder, str(value) if value else "")
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value) if value else "")

        return result

    def _evaluate_condition(self, condition: List[Any], record_data: Dict[str, Any]) -> bool:
        """Evaluate Odoo domain condition against record data"""
        # Simple domain evaluation - can be extended
        for clause in condition:
            if isinstance(clause, list) and len(clause) == 3:
                field, operator, value = clause
                record_value = record_data.get(field)

                if operator == "=":
                    if record_value != value:
                        return False
                elif operator == "!=":
                    if record_value == value:
                        return False
                elif operator == ">":
                    if not (record_value and record_value > value):
                        return False
                elif operator == "<":
                    if not (record_value and record_value < value):
                        return False
                elif operator == "in":
                    if record_value not in value:
                        return False
                elif operator == "not in":
                    if record_value in value:
                        return False

        return True

    def _calculate_next_run(self, cron_expression: str) -> Optional[datetime]:
        """Calculate next run time from cron expression"""
        try:
            from croniter import croniter
            cron = croniter(cron_expression, datetime.utcnow())
            return cron.get_next(datetime)
        except Exception:
            return None

