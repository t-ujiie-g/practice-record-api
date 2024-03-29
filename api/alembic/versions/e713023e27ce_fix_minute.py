"""fix minute

Revision ID: e713023e27ce
Revises: b3c7d87fdae3
Create Date: 2024-03-03 10:08:38.762749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e713023e27ce'
down_revision: Union[str, None] = 'b3c7d87fdae3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_table('RECORD_BK')
    # op.drop_table('Tag_BK')
    # op.drop_table('PracticeTag_BK')
    # op.drop_table('PracticeDetail_BK')
    op.alter_column('records', 'startMinute',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=True)
    op.alter_column('records', 'endMinute',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('records', 'endMinute',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.alter_column('records', 'startMinute',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.create_table('PracticeDetail_BK',
    sa.Column('id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('recordId', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=True)
    )
    op.create_table('PracticeTag_BK',
    sa.Column('practiceDetailId', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('tagId', sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.create_table('Tag_BK',
    sa.Column('id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=True)
    )
    op.create_table('RECORD_BK',
    sa.Column('id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('date', postgresql.TIMESTAMP(precision=3), autoincrement=False, nullable=True),
    sa.Column('startTime', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('startMinute', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('endTime', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('endMinute', sa.TEXT(), autoincrement=False, nullable=True)
    )
    # ### end Alembic commands ###
