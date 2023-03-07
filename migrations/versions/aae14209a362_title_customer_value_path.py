"""title_customer_value_path

Revision ID: aae14209a362
Revises: f808275e92ac
Create Date: 2023-03-07 09:01:53.373274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aae14209a362'
down_revision = 'f808275e92ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('uploaded_files', sa.Column('contract_title', sa.String(length=256), nullable=True))
    op.add_column('uploaded_files', sa.Column('customer_name', sa.String(length=256), nullable=True))
    op.add_column('uploaded_files', sa.Column('contract_value', sa.Integer(), nullable=True))
    op.add_column('uploaded_files', sa.Column('currency_type', sa.String(length=32), nullable=False))
    op.add_column('uploaded_files', sa.Column('s3_relative_path', sa.String(length=256), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('uploaded_files', 's3_relative_path')
    op.drop_column('uploaded_files', 'currency_type')
    op.drop_column('uploaded_files', 'contract_value')
    op.drop_column('uploaded_files', 'customer_name')
    op.drop_column('uploaded_files', 'contract_title')
    # ### end Alembic commands ###
