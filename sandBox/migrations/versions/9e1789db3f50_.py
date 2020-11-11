"""empty message

Revision ID: 9e1789db3f50
Revises: 0d8b19ea0564
Create Date: 2020-11-10 11:53:59.983868

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e1789db3f50'
down_revision = '0d8b19ea0564'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_traders_cryptoAddress'), 'traders', ['cryptoAddress'], unique=True)
    op.create_index(op.f('ix_traders_traderID'), 'traders', ['traderID'], unique=True)
    op.drop_index('ix_traders_crypto_address', table_name='traders')
    op.drop_index('ix_traders_trader_id', table_name='traders')
    op.drop_column('traders', 'trader_id')
    op.drop_column('traders', 'crypto_address')
    op.drop_column('traders', 'user_regtime')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('traders', sa.Column('user_regtime', sa.FLOAT(), nullable=True))
    op.add_column('traders', sa.Column('crypto_address', sa.VARCHAR(length=128), nullable=True))
    op.add_column('traders', sa.Column('trader_id', sa.VARCHAR(length=128), nullable=True))
    op.create_index('ix_traders_trader_id', 'traders', ['trader_id'], unique=1)
    op.create_index('ix_traders_crypto_address', 'traders', ['crypto_address'], unique=1)
    op.drop_index(op.f('ix_traders_traderID'), table_name='traders')
    op.drop_index(op.f('ix_traders_cryptoAddress'), table_name='traders')
    # ### end Alembic commands ###