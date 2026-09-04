"""Allow immutable Go runtime execution evidence.

Revision ID: 0008_go_runtime_execution
Revises: 0007_fix_proposals
Create Date: 2026-09-03
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008_go_runtime_execution"
down_revision: str | None = "0007_fix_proposals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_execution_language", "execution_attempts", type_="check")
    op.create_check_constraint(
        "ck_execution_language",
        "execution_attempts",
        "language IN ('python', 'typescript', 'go')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_execution_language", "execution_attempts", type_="check")
    op.create_check_constraint(
        "ck_execution_language",
        "execution_attempts",
        "language IN ('python', 'typescript')",
    )
