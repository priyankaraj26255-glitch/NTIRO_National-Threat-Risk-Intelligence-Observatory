"""add user status constraints

Revision ID: 77665f9f6a7e
Revises: f0204c25b047
"""

from typing import Sequence, Union

from alembic import op

revision: str = "77665f9f6a7e"
down_revision: Union[str, Sequence[str], None] = "f0204c25b047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_users_approval_status",
        "users",
        """
        approval_status IN (
            'pending',
            'approved',
            'rejected',
            'not_required'
        )
        """,
    )

    op.create_check_constraint(
        "ck_users_account_status",
        "users",
        """
        account_status IN (
            'active',
            'suspended',
            'disabled'
        )
        """,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_users_account_status",
        "users",
        type_="check",
    )

    op.drop_constraint(
        "ck_users_approval_status",
        "users",
        type_="check",
    )