
"""add organizations and faq relationship

Revision ID: 560f564d041c
Revises: 22d25c91e4c7
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '560f564d041c'
down_revision: Union[str, Sequence[str], None] = '22d25c91e4c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # 1. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        )
    )

    op.create_index(
        'ix_organizations_id',
        'organizations',
        ['id'],
        unique=False
    )

    # 2. Create a default organization
    connection = op.get_bind()

    organization_id = connection.execute(
        sa.text(
            "INSERT INTO organizations (name) "
            "VALUES (:name) RETURNING id"
        ),
        {"name": "Default Organization"}
    ).scalar_one()

    # 3. Add nullable organization_id first
    op.add_column(
        'faqs',
        sa.Column(
            'organization_id',
            sa.Integer(),
            nullable=True
        )
    )

    # 4. Assign existing FAQs to default organization
    connection.execute(
        sa.text(
            "UPDATE faqs "
            "SET organization_id = :organization_id"
        ),
        {"organization_id": organization_id}
    )

    # 5. Make organization_id required
    op.alter_column(
        'faqs',
        'organization_id',
        existing_type=sa.Integer(),
        nullable=False
    )

    # 6. Add index and foreign key
    op.create_index(
        'ix_faqs_organization_id',
        'faqs',
        ['organization_id'],
        unique=False
    )

    op.create_foreign_key(
        'fk_faqs_organization_id_organizations',
        'faqs',
        'organizations',
        ['organization_id'],
        ['id']
    )


def downgrade() -> None:

    op.drop_constraint(
        'fk_faqs_organization_id_organizations',
        'faqs',
        type_='foreignkey'
    )

    op.drop_index(
        'ix_faqs_organization_id',
        table_name='faqs'
    )

    op.drop_column(
        'faqs',
        'organization_id'
    )

    op.drop_index(
        'ix_organizations_id',
        table_name='organizations'
    )

    op.drop_table('organizations')
