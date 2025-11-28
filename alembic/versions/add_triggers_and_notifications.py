"""Add triggers and notifications tables

Revision ID: add_triggers_notifications
Revises: 
Create Date: 2025-11-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_triggers_notifications'
down_revision = None  # Update this with the previous migration ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================================================
    # Triggers Table
    # ========================================================================
    op.create_table(
        'triggers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('model', sa.String(255), nullable=False, index=True),
        sa.Column('event', sa.String(50), nullable=False, index=True),
        sa.Column('condition', postgresql.JSON, nullable=True, default=[]),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_config', postgresql.JSON, nullable=False, default={}),
        sa.Column('schedule_cron', sa.String(100), nullable=True),
        sa.Column('schedule_timezone', sa.String(50), default='UTC'),
        sa.Column('next_run_at', sa.DateTime, nullable=True),
        sa.Column('last_run_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(20), default='active', nullable=False, index=True),
        sa.Column('is_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('priority', sa.Integer, default=10, nullable=False),
        sa.Column('execution_count', sa.Integer, default=0, nullable=False),
        sa.Column('success_count', sa.Integer, default=0, nullable=False),
        sa.Column('failure_count', sa.Integer, default=0, nullable=False),
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('last_error_at', sa.DateTime, nullable=True),
        sa.Column('max_executions_per_hour', sa.Integer, default=100),
        sa.Column('current_hour_executions', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now(), nullable=True),
    )

    # ========================================================================
    # Trigger Executions Table
    # ========================================================================
    op.create_table(
        'trigger_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trigger_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('triggers.id'), nullable=False, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('record_id', sa.Integer, nullable=True),
        sa.Column('record_data', postgresql.JSON, nullable=True),
        sa.Column('success', sa.Boolean, nullable=False),
        sa.Column('result', postgresql.JSON, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now(), nullable=True),
    )

    # ========================================================================
    # Notifications Table
    # ========================================================================
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenant_users.id'), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('type', sa.String(20), default='info', nullable=False),
        sa.Column('priority', sa.String(20), default='normal', nullable=False),
        sa.Column('channels', postgresql.JSON, default=['in_app']),
        sa.Column('is_read', sa.Boolean, default=False, nullable=False, index=True),
        sa.Column('read_at', sa.DateTime, nullable=True),
        sa.Column('action_type', sa.String(50), nullable=True),
        sa.Column('action_data', postgresql.JSON, nullable=True),
        sa.Column('related_model', sa.String(255), nullable=True),
        sa.Column('related_id', sa.Integer, nullable=True),
        sa.Column('metadata', postgresql.JSON, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now(), nullable=True),
    )

    # ========================================================================
    # Notification Preferences Table
    # ========================================================================
    op.create_table(
        'notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenant_users.id'), nullable=False, unique=True, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('enable_in_app', sa.Boolean, default=True, nullable=False),
        sa.Column('enable_push', sa.Boolean, default=True, nullable=False),
        sa.Column('enable_email', sa.Boolean, default=True, nullable=False),
        sa.Column('enable_sms', sa.Boolean, default=False, nullable=False),
        sa.Column('receive_info', sa.Boolean, default=True, nullable=False),
        sa.Column('receive_success', sa.Boolean, default=True, nullable=False),
        sa.Column('receive_warning', sa.Boolean, default=True, nullable=False),
        sa.Column('receive_error', sa.Boolean, default=True, nullable=False),
        sa.Column('receive_system', sa.Boolean, default=True, nullable=False),
        sa.Column('quiet_hours_enabled', sa.Boolean, default=False, nullable=False),
        sa.Column('quiet_hours_start', sa.String(5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(5), nullable=True),
        sa.Column('quiet_hours_timezone', sa.String(50), default='UTC'),
        sa.Column('email_digest_enabled', sa.Boolean, default=False, nullable=False),
        sa.Column('email_digest_frequency', sa.String(20), default='daily'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now(), nullable=True),
    )

    # ========================================================================
    # Device Tokens Table
    # ========================================================================
    op.create_table(
        'device_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenant_users.id'), nullable=False, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('device_id', sa.String(255), nullable=False, index=True),
        sa.Column('device_name', sa.String(255), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=False),
        sa.Column('token', sa.Text, nullable=False),
        sa.Column('token_type', sa.String(50), default='fcm'),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        sa.Column('app_version', sa.String(50), nullable=True),
        sa.Column('os_version', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now(), nullable=True),
    )

    # Create indexes for better query performance
    op.create_index('ix_triggers_tenant_model', 'triggers', ['tenant_id', 'model'])
    op.create_index('ix_trigger_executions_trigger_created', 'trigger_executions', ['trigger_id', 'created_at'])
    op.create_index('ix_notifications_user_read', 'notifications', ['user_id', 'is_read'])
    op.create_index('ix_notifications_user_created', 'notifications', ['user_id', 'created_at'])
    op.create_index('ix_device_tokens_user_device', 'device_tokens', ['user_id', 'device_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_device_tokens_user_device', 'device_tokens')
    op.drop_index('ix_notifications_user_created', 'notifications')
    op.drop_index('ix_notifications_user_read', 'notifications')
    op.drop_index('ix_trigger_executions_trigger_created', 'trigger_executions')
    op.drop_index('ix_triggers_tenant_model', 'triggers')

    # Drop tables
    op.drop_table('device_tokens')
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
    op.drop_table('trigger_executions')
    op.drop_table('triggers')

