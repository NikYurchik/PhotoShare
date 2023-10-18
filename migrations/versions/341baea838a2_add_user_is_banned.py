"""add User.is_banned

Revision ID: 341baea838a2
Revises: 850aa22b160f
Create Date: 2023-10-11 21:53:59.949406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '341baea838a2'
down_revision: Union[str, None] = '850aa22b160f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_banned', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_banned')
    # ### end Alembic commands ###