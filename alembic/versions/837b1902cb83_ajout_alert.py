"""ajout alert

Revision ID: 837b1902cb83
Revises: 26d34e4097cf
Create Date: 2026-10-22 14:04:56.004815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '837b1902cb83'
down_revision: Union[str, None] = '26d34e4097cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
