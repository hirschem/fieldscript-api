"""
add key_fingerprint column to project_api_keys
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_add_key_fingerprint'
down_revision = '0001_create_project_api_keys'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('project_api_keys', sa.Column('key_fingerprint', sa.String(8), nullable=True))
    # Backfill existing rows
    op.execute("UPDATE project_api_keys SET key_fingerprint = substr(key_hash, -8, 8)")
    op.alter_column('project_api_keys', 'key_fingerprint', nullable=False)
    op.create_index('ix_project_api_keys_key_fingerprint', 'project_api_keys', ['key_fingerprint'])

def downgrade():
    op.drop_index('ix_project_api_keys_key_fingerprint', table_name='project_api_keys')
    op.drop_column('project_api_keys', 'key_fingerprint')
