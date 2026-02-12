"""
create project_api_keys table
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_create_project_api_keys'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'project_api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(64), nullable=False, index=True),
        sa.Column('key_prefix', sa.String(16), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_project_api_keys_project_id', 'project_api_keys', ['project_id'])
    op.create_index('ix_project_api_keys_project_id_revoked_at', 'project_api_keys', ['project_id', 'revoked_at'])
    op.create_unique_constraint('uq_project_api_keys_key_hash', 'project_api_keys', ['key_hash'])

def downgrade():
    op.drop_constraint('uq_project_api_keys_key_hash', 'project_api_keys', type_='unique')
    op.drop_index('ix_project_api_keys_project_id_revoked_at', table_name='project_api_keys')
    op.drop_index('ix_project_api_keys_project_id', table_name='project_api_keys')
    op.drop_table('project_api_keys')
