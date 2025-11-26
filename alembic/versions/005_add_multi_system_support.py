"""Add multi-system support for Moodle, SAP, etc.

Revision ID: 005_multi_system
Revises: 004_unique_odoo_user
Create Date: 2025-11-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '005_multi_system'
down_revision = '004_unique_odoo_user'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add multi-system architecture support.

    This migration:
    1. Creates external_systems table (catalog of system types)
    2. Creates tenant_systems table (many-to-many tenant-system connections)
    3. Makes Odoo fields nullable in tenants table (backward compatibility)
    4. Seeds initial system types (Odoo, Moodle, SAP, etc.)
    """

    # Create external_systems table
    op.create_table(
        'external_systems',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('system_type', sa.Enum('odoo', 'moodle', 'sap', 'salesforce', 'dynamics', 'custom',
                                         name='systemtype'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', 'error', 'testing',
                                   name='systemstatus'), nullable=False, server_default='active'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('default_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('capabilities', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_external_systems_id', 'external_systems', ['id'])
    op.create_index('ix_external_systems_system_type', 'external_systems', ['system_type'])

    # Create tenant_systems table (many-to-many)
    op.create_table(
        'tenant_systems',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('system_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('connection_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_connection_test', sa.DateTime(), nullable=True),
        sa.Column('last_successful_connection', sa.DateTime(), nullable=True),
        sa.Column('connection_error', sa.Text(), nullable=True),
        sa.Column('custom_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_tenant_systems_id', 'tenant_systems', ['id'])
    op.create_index('ix_tenant_systems_tenant_id', 'tenant_systems', ['tenant_id'])
    op.create_index('ix_tenant_systems_system_id', 'tenant_systems', ['system_id'])
    op.create_index('ix_tenant_systems_is_active', 'tenant_systems', ['is_active'])

    # Add foreign keys
    op.create_foreign_key(
        'fk_tenant_systems_tenant_id',
        'tenant_systems', 'tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_tenant_systems_system_id',
        'tenant_systems', 'external_systems',
        ['system_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_tenant_systems_created_by',
        'tenant_systems', 'admins',
        ['created_by'], ['id']
    )

    # Make Odoo fields nullable in tenants table (for backward compatibility)
    op.alter_column('tenants', 'odoo_url', nullable=True)
    op.alter_column('tenants', 'odoo_database', nullable=True)
    op.alter_column('tenants', 'odoo_username', nullable=True)
    op.alter_column('tenants', 'odoo_password', nullable=True)

    # Seed initial system types
    op.execute("""
        INSERT INTO external_systems (id, system_type, name, description, status, is_enabled, capabilities)
        VALUES
        (gen_random_uuid(), 'odoo', 'Odoo ERP', 'Open source ERP and CRM system', 'active', true,
         '{"crud": true, "search": true, "webhooks": true, "batch": true, "realtime_sync": true}'),
        (gen_random_uuid(), 'moodle', 'Moodle LMS', 'Open source learning management system', 'active', true,
         '{"crud": true, "search": true, "webhooks": false, "courses": true, "users": true, "grades": true}'),
        (gen_random_uuid(), 'sap', 'SAP ERP', 'Enterprise resource planning software', 'inactive', false,
         '{"crud": true, "search": true, "webhooks": false}'),
        (gen_random_uuid(), 'salesforce', 'Salesforce CRM', 'Cloud-based CRM platform', 'inactive', false,
         '{"crud": true, "search": true, "webhooks": true}'),
        (gen_random_uuid(), 'dynamics', 'Microsoft Dynamics', 'Business applications platform', 'inactive', false,
         '{"crud": true, "search": true, "webhooks": true}')
    """)


def downgrade() -> None:
    """Remove multi-system support"""

    # Drop foreign keys first
    op.drop_constraint('fk_tenant_systems_created_by', 'tenant_systems', type_='foreignkey')
    op.drop_constraint('fk_tenant_systems_system_id', 'tenant_systems', type_='foreignkey')
    op.drop_constraint('fk_tenant_systems_tenant_id', 'tenant_systems', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_tenant_systems_is_active', 'tenant_systems')
    op.drop_index('ix_tenant_systems_system_id', 'tenant_systems')
    op.drop_index('ix_tenant_systems_tenant_id', 'tenant_systems')
    op.drop_index('ix_tenant_systems_id', 'tenant_systems')

    op.drop_index('ix_external_systems_system_type', 'external_systems')
    op.drop_index('ix_external_systems_id', 'external_systems')

    # Drop tables
    op.drop_table('tenant_systems')
    op.drop_table('external_systems')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS systemstatus')
    op.execute('DROP TYPE IF EXISTS systemtype')

    # Revert Odoo fields to NOT NULL
    op.alter_column('tenants', 'odoo_url', nullable=False)
    op.alter_column('tenants', 'odoo_database', nullable=False)
    op.alter_column('tenants', 'odoo_username', nullable=False)
    op.alter_column('tenants', 'odoo_password', nullable=False)
