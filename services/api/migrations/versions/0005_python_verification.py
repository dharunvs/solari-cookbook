"""Add immutable Python execution evidence and cooperative cancellation.

Revision ID: 0005_python_verification
Revises: 0004_static_analysis
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_python_verification"
down_revision: str | None = "0004_static_analysis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_run_state", "verification_runs", type_="check")
    op.create_check_constraint(
        "ck_run_state",
        "verification_runs",
        "state IN ('QUEUED', 'SNAPSHOTTING', 'ANALYZING', 'VERIFYING', "
        "'PROPOSING', 'REVERIFYING', 'CANCEL_REQUESTED', 'COMPLETED', "
        "'FAILED', 'CANCELLED')",
    )
    op.create_table(
        "execution_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("language", sa.Text(), nullable=False),
        sa.Column("phase", sa.Text(), nullable=False),
        sa.Column("backend", sa.Text(), nullable=False),
        sa.Column("infrastructure_state", sa.Text(), nullable=False),
        sa.Column("infrastructure_step", sa.Text(), nullable=False),
        sa.Column("subject_state", sa.Text(), nullable=False),
        sa.Column("sandbox_id", sa.Text(), nullable=True),
        sa.Column("package_name", sa.Text(), nullable=False),
        sa.Column("package_version", sa.Text(), nullable=False),
        sa.Column("source_artifact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_sha256", sa.Text(), nullable=False),
        sa.Column("command_sha256", sa.Text(), nullable=False),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("output_truncated", sa.Boolean(), nullable=False),
        sa.Column("cleanup_state", sa.Text(), nullable=False),
        sa.Column("cancelled", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column(
            "evidence_artifact_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id", "workspace_id"],
            ["verification_runs.id", "verification_runs.workspace_id"],
            ondelete="CASCADE",
            name="fk_execution_run_workspace",
        ),
        sa.ForeignKeyConstraint(
            ["finding_id", "workspace_id"],
            ["findings.id", "findings.workspace_id"],
            name="fk_execution_finding_workspace",
        ),
        sa.ForeignKeyConstraint(
            ["source_artifact_id", "workspace_id"],
            ["artifacts.id", "artifacts.workspace_id"],
            name="fk_execution_source_workspace",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_artifact_id", "workspace_id"],
            ["artifacts.id", "artifacts.workspace_id"],
            name="fk_execution_evidence_workspace",
        ),
        sa.UniqueConstraint("id", "workspace_id", name="uq_executions_id_workspace"),
        sa.UniqueConstraint(
            "run_id",
            "finding_id",
            "phase",
            "attempt_number",
            name="uq_execution_attempt",
        ),
        sa.CheckConstraint("attempt_number > 0", name="ck_execution_attempt_number"),
        sa.CheckConstraint("language IN ('python')", name="ck_execution_language"),
        sa.CheckConstraint("phase IN ('VERIFY')", name="ck_execution_phase"),
        sa.CheckConstraint(
            "backend IN ('REPLAY', 'SOLARI')", name="ck_execution_backend"
        ),
        sa.CheckConstraint(
            "infrastructure_state IN ('PASS', 'FAIL')",
            name="ck_execution_infrastructure_state",
        ),
        sa.CheckConstraint(
            "subject_state IN ('PASS', 'FAIL', 'NOT_RUN')",
            name="ck_execution_subject_state",
        ),
        sa.CheckConstraint(
            "cleanup_state IN ('PASS', 'FAIL', 'NOT_REQUIRED')",
            name="ck_execution_cleanup_state",
        ),
        sa.CheckConstraint(
            "(infrastructure_state = 'PASS' AND subject_state IN ('PASS', 'FAIL')) "
            "OR (infrastructure_state = 'FAIL' AND subject_state = 'NOT_RUN')",
            name="ck_execution_truth_separation",
        ),
        sa.CheckConstraint(
            "source_sha256 ~ '^[0-9a-f]{64}$'", name="ck_execution_source_sha256"
        ),
        sa.CheckConstraint(
            "command_sha256 ~ '^[0-9a-f]{64}$'", name="ck_execution_command_sha256"
        ),
        sa.CheckConstraint("duration_ms >= 0", name="ck_execution_duration"),
    )
    op.create_index(
        "ix_execution_attempts_run", "execution_attempts", ["run_id", "started_at"]
    )
    op.execute(
        """
        CREATE FUNCTION prevent_execution_attempt_mutation() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'execution attempts are immutable';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER execution_attempts_immutable
        BEFORE UPDATE OR DELETE ON execution_attempts
        FOR EACH ROW EXECUTE FUNCTION prevent_execution_attempt_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS prevent_execution_attempt_mutation() CASCADE")
    op.drop_index("ix_execution_attempts_run", table_name="execution_attempts")
    op.drop_table("execution_attempts")
    op.drop_constraint("ck_run_state", "verification_runs", type_="check")
    op.create_check_constraint(
        "ck_run_state",
        "verification_runs",
        "state IN ('QUEUED', 'SNAPSHOTTING', 'ANALYZING', 'VERIFYING', "
        "'PROPOSING', 'REVERIFYING', 'COMPLETED', 'FAILED', 'CANCELLED')",
    )
