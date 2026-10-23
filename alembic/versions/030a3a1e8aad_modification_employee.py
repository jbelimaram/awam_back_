"""modification employee

Revision ID: 030a3a1e8aad
Revises: 837b1902cb83
Create Date: 2026-10-23 11:03:51.053703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '030a3a1e8aad'
down_revision: Union[str, None] = '837b1902cb83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
