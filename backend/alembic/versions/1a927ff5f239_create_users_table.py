"""create users table

Revision ID: 1a927ff5f239
Revises: be8ac424bd21
Create Date: 2026-09-26 10:52:34.080210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a927ff5f239'
down_revision: Union[str, Sequence[str], None] = 'be8ac424bd21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
