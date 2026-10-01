"""align agenda_event with model

Revision ID: c434e3c1fc7b
Revises: bd3dd1ca8023
Create Date: 2026-09-22 16:16:48.374097

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c434e3c1fc7b'
down_revision: Union[str, None] = 'bd3dd1ca8023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Renommer start_datetime -> start_at (préserve les données)
    op.alter_column(
        'agenda_event', 'start_datetime',
        new_column_name='start_at',
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )

    # 2) Renommer end_datetime -> end_at
    op.alter_column(
        'agenda_event', 'end_datetime',
        new_column_name='end_at',
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    # 3) title : VARCHAR(150) -> VARCHAR(255)
    op.alter_column(
        'agenda_event', 'title',
        existing_type=sa.VARCHAR(150),
        type_=sa.String(255),
        existing_nullable=False,
    )

    # 4) description : TEXT -> VARCHAR(1000)
    op.alter_column(
        'agenda_event', 'description',
        existing_type=sa.TEXT(),
        type_=sa.String(1000),
        existing_nullable=True,
    )

    # 5) Supprimer les anciennes colonnes de rappel
    op.drop_column('agenda_event', 'reminder')
    op.drop_column('agenda_event', 'reminder_custom_minutes')

    # 6) Ajouter les nouvelles colonnes
    op.add_column('agenda_event', sa.Column('reminder_unit', sa.String(20), nullable=True))
    op.add_column('agenda_event', sa.Column('reminder_custom_value', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('agenda_event', 'reminder_custom_value')
    op.drop_column('agenda_event', 'reminder_unit')

    op.add_column('agenda_event', sa.Column('reminder_custom_minutes', sa.Integer(), nullable=True))
    op.add_column('agenda_event', sa.Column('reminder', sa.VARCHAR(20), nullable=True))

    op.alter_column(
        'agenda_event', 'description',
        existing_type=sa.String(1000),
        type_=sa.TEXT(),
        existing_nullable=True,
    )

    op.alter_column(
        'agenda_event', 'title',
        existing_type=sa.String(255),
        type_=sa.VARCHAR(150),
        existing_nullable=False,
    )

    op.alter_column(
        'agenda_event', 'end_at',
        new_column_name='end_datetime',
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    op.alter_column(
        'agenda_event', 'start_at',
        new_column_name='start_datetime',
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )