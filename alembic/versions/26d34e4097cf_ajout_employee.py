"""ajout employee

Revision ID: 26d34e4097cf
Revises: ebfc7adf54fe
Create Date: 2026-10-22 14:02:18.499437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26d34e4097cf'
down_revision: Union[str, None] = 'ebfc7adf54fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
