"""Add model_version column to predictions table

Revision ID: add_model_version_001
Revises: 
Create Date: 2025-07-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_model_version_001'
down_revision = None
depends_on = None

def upgrade():
    """Add model_version column if it doesn't exist"""
    
    # Check if column exists first
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [column['name'] for column in inspector.get_columns('predictions')]
    
    if 'model_version' not in columns:
        print("Adding model_version column...")
        op.add_column('predictions', 
                     sa.Column('model_version', sa.String(20), 
                              nullable=False, 
                              server_default='1.0'))
        print("✅ model_version column added successfully")
    else:
        print("✅ model_version column already exists")

def downgrade():
    """Remove model_version column"""
    op.drop_column('predictions', 'model_version')
