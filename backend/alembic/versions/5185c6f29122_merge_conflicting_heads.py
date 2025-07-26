"""merge conflicting heads

Revision ID: 5185c6f29122
Revises: add_model_version_001, safe_ml_models_20250724_145712
Create Date: 2025-07-26 15:56:31.808114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5185c6f29122'
down_revision: Union[str, None] = ('add_model_version_001', 'safe_ml_models_20250724_145712')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
