"""add raster table only

Revision ID: bd3dd1ca8023
Revises: 086ed9a10d43
Create Date: 2026-09-21 13:21:37.305954

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd3dd1ca8023'
down_revision: Union[str, None] = '086ed9a10d43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'raster',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(length=255), nullable=True),
        sa.Column('b2_key', sa.String(length=500), nullable=False),
        sa.Column('b2_url', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raster_id'), 'raster', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_raster_id'), table_name='raster')
    op.drop_table('raster')