"""add max_users field to tenants

Revision ID: 003_max_users
Revises: 002_add_admin_panel_tables
Create Date: 2025-11-22 14:42:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_max_users'
down_revision = '002_admin_panel'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column with default value for existing rows
    op.add_column('tenants', sa.Column('max_users', sa.Integer(), nullable=True))
    
    # Update existing rows to have default value of 5
    op.execute('UPDATE tenants SET max_users = 5 WHERE max_users IS NULL')
    
    # Make column NOT NULL
    op.alter_column('tenants', 'max_users', nullable=False)


def downgrade() -> None:
    op.drop_column('tenants', 'max_users')

