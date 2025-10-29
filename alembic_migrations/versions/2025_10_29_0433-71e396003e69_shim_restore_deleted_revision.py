"""shim: restore deleted revision

Revision ID: 71e396003e69
Revises: 87dcdcadab5b
Create Date: 2025-10-29 04:33:22.083076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71e396003e69'
down_revision: Union[str, None] = '87dcdcadab5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
