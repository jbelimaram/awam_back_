"""ajout heure dans table activity

Revision ID: b46d14411a5b
Revises: 030a3a1e8aad
Create Date: 2026-10-29 11:05:17.061769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b46d14411a5b'
down_revision: Union[str, None] = '030a3a1e8aad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
