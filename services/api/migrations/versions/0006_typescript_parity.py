"""Generalize immutable executions for TypeScript parity.

Revision ID: 0006_typescript_parity
Revises: 0005_python_verification
Create Date: 2026-09-03
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006_typescript_parity"
down_revision: str | None = "0005_python_verification"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_execution_language", "execution_attempts", type_="check")
    op.create_check_constraint(
        "ck_execution_language",
        "execution_attempts",
        "language IN ('python', 'typescript')",
    )
    op.drop_constraint(
        "fk_execution_finding_workspace", "execution_attempts", type_="foreignkey"
    )
    op.alter_column("execution_attempts", "finding_id", nullable=True)
    op.create_foreign_key(
        "fk_execution_finding_workspace",
        "execution_attempts",
        "findings",
        ["finding_id", "workspace_id"],
        ["id", "workspace_id"],
    )
    op.drop_constraint("uq_execution_attempt", "execution_attempts", type_="unique")
    op.create_unique_constraint(
        "uq_execution_attempt",
        "execution_attempts",
        ["run_id", "language", "phase", "attempt_number"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_execution_attempt", "execution_attempts", type_="unique")
    op.create_unique_constraint(
        "uq_execution_attempt",
        "execution_attempts",
        ["run_id", "finding_id", "phase", "attempt_number"],
    )
    op.drop_constraint(
        "fk_execution_finding_workspace", "execution_attempts", type_="foreignkey"
    )
    op.alter_column("execution_attempts", "finding_id", nullable=False)
    op.create_foreign_key(
        "fk_execution_finding_workspace",
        "execution_attempts",
        "findings",
        ["finding_id", "workspace_id"],
        ["id", "workspace_id"],
    )
    op.drop_constraint("ck_execution_language", "execution_attempts", type_="check")
    op.create_check_constraint(
        "ck_execution_language", "execution_attempts", "language IN ('python')"
    )
