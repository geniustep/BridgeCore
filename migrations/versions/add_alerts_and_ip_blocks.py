"""Add alerts and IP blocks tables

Revision ID: add_alerts_ip_blocks
Revises: 
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = 'add_alerts_ip_blocks'
down_revision = None  # Update this to chain to your latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True, index=True),
        
        # Alert details
        sa.Column('alert_type', sa.Enum(
            'rate_limit_warning', 'rate_limit_exceeded', 'high_error_rate',
            'slow_response', 'suspicious_ip', 'tenant_suspended',
            'connection_failed', 'security_threat',
            name='alerttype'
        ), nullable=False, index=True),
        sa.Column('severity', sa.Enum(
            'info', 'warning', 'error', 'critical',
            name='alertseverity'
        ), default='warning', nullable=False, index=True),
        sa.Column('status', sa.Enum(
            'active', 'acknowledged', 'resolved', 'dismissed',
            name='alertstatus'
        ), default='active', nullable=False, index=True),
        
        # Content
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', JSON, nullable=True),
        
        # Thresholds
        sa.Column('threshold_value', sa.Integer(), nullable=True),
        sa.Column('current_value', sa.Integer(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False, index=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', UUID(as_uuid=True), sa.ForeignKey('admins.id'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', UUID(as_uuid=True), sa.ForeignKey('admins.id'), nullable=True),
        
        # Auto-dismiss
        sa.Column('auto_resolve', sa.Boolean(), default=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    
    # Create indexes for alerts
    op.create_index('ix_alerts_tenant_type', 'alerts', ['tenant_id', 'alert_type'])
    op.create_index('ix_alerts_status_severity', 'alerts', ['status', 'severity'])
    op.create_index('ix_alerts_active', 'alerts', ['status', 'created_at'])

    # Create IP blocks table
    op.create_table(
        'ip_blocks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        
        # IP Information
        sa.Column('ip_address', sa.String(45), nullable=False, index=True),
        sa.Column('ip_range', sa.String(50), nullable=True),
        
        # Block details
        sa.Column('reason', sa.Enum(
            'rate_limit_abuse', 'brute_force', 'suspicious_activity',
            'security_threat', 'manual_block', 'spam',
            name='blockreason'
        ), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Associated tenant
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True, index=True),
        
        # Block settings
        sa.Column('is_permanent', sa.Boolean(), default=False),
        sa.Column('blocked_at', sa.DateTime(), default=sa.func.now(), nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True, index=True),
        
        # Violation tracking
        sa.Column('violation_count', sa.Integer(), default=1),
        sa.Column('last_violation_at', sa.DateTime(), default=sa.func.now()),
        
        # Admin info
        sa.Column('blocked_by', UUID(as_uuid=True), sa.ForeignKey('admins.id'), nullable=True),
        
        # Unblock info
        sa.Column('is_active', sa.Boolean(), default=True, index=True),
        sa.Column('unblocked_at', sa.DateTime(), nullable=True),
        sa.Column('unblocked_by', UUID(as_uuid=True), sa.ForeignKey('admins.id'), nullable=True),
        sa.Column('unblock_reason', sa.Text(), nullable=True),
        
        # Context
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('request_details', JSON, nullable=True),
    )
    
    # Create indexes for ip_blocks
    op.create_index('ix_ip_blocks_active_ip', 'ip_blocks', ['is_active', 'ip_address'])
    op.create_index('ix_ip_blocks_expires', 'ip_blocks', ['is_active', 'expires_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_ip_blocks_expires', 'ip_blocks')
    op.drop_index('ix_ip_blocks_active_ip', 'ip_blocks')
    op.drop_index('ix_alerts_active', 'alerts')
    op.drop_index('ix_alerts_status_severity', 'alerts')
    op.drop_index('ix_alerts_tenant_type', 'alerts')
    
    # Drop tables
    op.drop_table('ip_blocks')
    op.drop_table('alerts')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS blockreason')
    op.execute('DROP TYPE IF EXISTS alertstatus')
    op.execute('DROP TYPE IF EXISTS alertseverity')
    op.execute('DROP TYPE IF EXISTS alerttype')

