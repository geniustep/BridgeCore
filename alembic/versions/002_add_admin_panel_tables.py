"""Add admin panel and multi-tenant tables

Revision ID: 002_admin_panel
Revises: 001_initial
Create Date: 2025-11-21 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_admin_panel'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create admins table
    op.create_table(
        'admins',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('SUPER_ADMIN', 'ADMIN', 'SUPPORT', name='adminrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_admins_id', 'admins', ['id'])
    op.create_index('ix_admins_email', 'admins', ['email'])

    # Create plans table
    op.create_table(
        'plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('max_requests_per_day', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('max_requests_per_hour', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('max_users', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_storage_gb', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('price_monthly', sa.DECIMAL(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('price_yearly', sa.DECIMAL(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_plans_id', 'plans', ['id'])

    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=False),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('odoo_url', sa.String(length=500), nullable=False),
        sa.Column('odoo_database', sa.String(length=255), nullable=False),
        sa.Column('odoo_version', sa.String(length=50), nullable=True),
        sa.Column('odoo_username', sa.String(length=255), nullable=False),
        sa.Column('odoo_password', sa.String(length=500), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'SUSPENDED', 'TRIAL', 'DELETED', name='tenantstatus'), nullable=False, server_default='TRIAL'),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_ends_at', sa.DateTime(), nullable=True),
        sa.Column('max_requests_per_day', sa.Integer(), nullable=True),
        sa.Column('max_requests_per_hour', sa.Integer(), nullable=True),
        sa.Column('allowed_models', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('allowed_features', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_active_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['admins.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index('ix_tenants_id', 'tenants', ['id'])
    op.create_index('ix_tenants_slug', 'tenants', ['slug'])
    op.create_index('ix_tenants_status', 'tenants', ['status'])

    # Create tenant_users table
    op.create_table(
        'tenant_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'USER', name='tenantuserrole'), nullable=False, server_default='USER'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('odoo_user_id', sa.Integer(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tenant_users_id', 'tenant_users', ['id'])
    op.create_index('ix_tenant_users_tenant_id', 'tenant_users', ['tenant_id'])
    op.create_index('ix_tenant_users_email', 'tenant_users', ['email'])

    # Create usage_logs table
    op.create_table(
        'usage_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('request_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('response_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['tenant_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_usage_logs_id', 'usage_logs', ['id'])
    op.create_index('ix_usage_logs_tenant_id', 'usage_logs', ['tenant_id'])
    op.create_index('ix_usage_logs_user_id', 'usage_logs', ['user_id'])
    op.create_index('ix_usage_logs_timestamp', 'usage_logs', ['timestamp'])
    op.create_index('ix_usage_logs_status_code', 'usage_logs', ['status_code'])
    op.create_index('ix_usage_logs_model_name', 'usage_logs', ['model_name'])
    op.create_index('ix_usage_logs_tenant_timestamp', 'usage_logs', ['tenant_id', 'timestamp'])
    op.create_index('ix_usage_logs_tenant_status', 'usage_logs', ['tenant_id', 'status_code'])
    op.create_index('ix_usage_logs_tenant_model', 'usage_logs', ['tenant_id', 'model_name'])

    # Create error_logs table
    op.create_table(
        'error_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('error_type', sa.String(length=255), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('endpoint', sa.String(length=500), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('request_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='errorseverity'), nullable=False, server_default='MEDIUM'),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['admins.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_error_logs_id', 'error_logs', ['id'])
    op.create_index('ix_error_logs_tenant_id', 'error_logs', ['tenant_id'])
    op.create_index('ix_error_logs_timestamp', 'error_logs', ['timestamp'])
    op.create_index('ix_error_logs_error_type', 'error_logs', ['error_type'])
    op.create_index('ix_error_logs_severity', 'error_logs', ['severity'])
    op.create_index('ix_error_logs_is_resolved', 'error_logs', ['is_resolved'])
    op.create_index('ix_error_logs_tenant_timestamp', 'error_logs', ['tenant_id', 'timestamp'])
    op.create_index('ix_error_logs_tenant_severity', 'error_logs', ['tenant_id', 'severity'])
    op.create_index('ix_error_logs_unresolved', 'error_logs', ['tenant_id', 'is_resolved'])

    # Create usage_stats table
    op.create_table(
        'usage_stats',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=True),
        sa.Column('total_requests', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('successful_requests', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('failed_requests', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_data_transferred_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('avg_response_time_ms', sa.Integer(), nullable=True),
        sa.Column('unique_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('most_used_model', sa.String(length=100), nullable=True),
        sa.Column('peak_hour', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('hour IS NULL OR (hour >= 0 AND hour <= 23)', name='check_hour_range')
    )
    op.create_index('ix_usage_stats_id', 'usage_stats', ['id'])
    op.create_index('ix_usage_stats_tenant_id', 'usage_stats', ['tenant_id'])
    op.create_index('ix_usage_stats_date', 'usage_stats', ['date'])
    op.create_index('ix_usage_stats_tenant_date', 'usage_stats', ['tenant_id', 'date'])
    op.create_index('ix_usage_stats_tenant_date_hour', 'usage_stats', ['tenant_id', 'date', 'hour'])
    op.create_index('uq_usage_stats_tenant_date_hour', 'usage_stats', ['tenant_id', 'date', 'hour'], unique=True)

    # Create admin_audit_logs table
    op.create_table(
        'admin_audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ),
        sa.ForeignKeyConstraint(['target_tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_admin_audit_logs_id', 'admin_audit_logs', ['id'])
    op.create_index('ix_admin_audit_logs_admin_id', 'admin_audit_logs', ['admin_id'])
    op.create_index('ix_admin_audit_logs_target_tenant_id', 'admin_audit_logs', ['target_tenant_id'])
    op.create_index('ix_admin_audit_logs_action', 'admin_audit_logs', ['action'])
    op.create_index('ix_admin_audit_logs_timestamp', 'admin_audit_logs', ['timestamp'])
    op.create_index('ix_admin_audit_logs_admin_timestamp', 'admin_audit_logs', ['admin_id', 'timestamp'])
    op.create_index('ix_admin_audit_logs_tenant_timestamp', 'admin_audit_logs', ['target_tenant_id', 'timestamp'])
    op.create_index('ix_admin_audit_logs_action_timestamp', 'admin_audit_logs', ['action', 'timestamp'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('admin_audit_logs')
    op.drop_table('usage_stats')
    op.drop_table('error_logs')
    op.drop_table('usage_logs')
    op.drop_table('tenant_users')
    op.drop_table('tenants')
    op.drop_table('plans')
    op.drop_table('admins')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS errorseverity')
    op.execute('DROP TYPE IF EXISTS tenantuserrole')
    op.execute('DROP TYPE IF EXISTS tenantstatus')
    op.execute('DROP TYPE IF EXISTS adminrole')
