"""Add unique constraint on tenant_id and odoo_user_id

Revision ID: 004_unique_odoo_user
Revises: 003_max_users
Create Date: 2025-11-22 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_unique_odoo_user'
down_revision = '003_max_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add unique constraint to prevent multiple BridgeCore accounts 
    for the same Odoo user within the same tenant.
    
    This ensures:
    - Security: Prevents privilege escalation
    - Audit: Clear one-to-one mapping
    - Rate Limiting: Cannot bypass limits with multiple accounts
    - Data Integrity: Consistent user identity
    """
    # First, remove any duplicate entries if they exist
    # Keep the oldest record for each (tenant_id, odoo_user_id) pair
    op.execute("""
        DELETE FROM tenant_users
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM tenant_users
            WHERE odoo_user_id IS NOT NULL
            GROUP BY tenant_id, odoo_user_id
        )
        AND odoo_user_id IS NOT NULL
    """)
    
    # Add the unique constraint
    op.create_unique_constraint(
        'uq_tenant_odoo_user',
        'tenant_users',
        ['tenant_id', 'odoo_user_id']
    )


def downgrade() -> None:
    """Remove the unique constraint"""
    op.drop_constraint(
        'uq_tenant_odoo_user',
        'tenant_users',
        type_='unique'
    )

