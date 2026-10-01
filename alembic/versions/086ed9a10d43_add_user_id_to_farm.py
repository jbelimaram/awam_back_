"""add user_id to farm

Revision ID: 086ed9a10d43
Revises: eb9745be9626
Create Date: 2026-09-21 11:14:39.297981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '086ed9a10d43'
down_revision: Union[str, None] = 'eb9745be9626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
