"""Add durable verification runs, leased jobs, and immutable artifacts.

Revision ID: 0003_durable_runs
Revises: 0002_onboarding
Create Date: 2026-09-02
"""
# ruff: noqa: E501

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_durable_runs"
down_revision: str | None = "0002_onboarding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


RUN_STATES = (
    "QUEUED",
    "SNAPSHOTTING",
    "ANALYZING",
    "VERIFYING",
    "PROPOSING",
    "REVERIFYING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
)
JOB_STATES = ("QUEUED", "LEASED", "COMPLETED", "FAILED", "CANCELLED")


def _state_check(column: str, values: tuple[str, ...]) -> str:
    allowed = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({allowed})"


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_product_configurations_id_product",
        "product_configurations",
        ["id", "product_id"],
    )
    op.create_table(
        "verification_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("configuration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scenario", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="QUEUED"),
        sa.Column("manifest_sha256", sa.Text(), nullable=True),
        sa.Column("result_artifact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["configuration_id", "product_id"],
            ["product_configurations.id", "product_configurations.product_id"],
            name="fk_run_configuration_product",
        ),
        sa.UniqueConstraint("id", "workspace_id", name="uq_runs_id_workspace"),
        sa.CheckConstraint(_state_check("state", RUN_STATES), name="ck_run_state"),
        sa.CheckConstraint(
            "manifest_sha256 IS NULL OR manifest_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_run_manifest_sha256",
        ),
        sa.CheckConstraint(
            "(state IN ('COMPLETED', 'FAILED', 'CANCELLED')) = (completed_at IS NOT NULL)",
            name="ck_run_terminal_completed_at",
        ),
    )
    op.create_table(
        "verification_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False, server_default="READINESS_PROBE"),
        sa.Column("state", sa.Text(), nullable=False, server_default="QUEUED"),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("lease_owner", sa.Text(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_sha256", sa.Text(), nullable=False),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["run_id", "workspace_id"],
            ["verification_runs.id", "verification_runs.workspace_id"],
            ondelete="CASCADE",
            name="fk_job_run_workspace",
        ),
        sa.UniqueConstraint(
            "workspace_id", "idempotency_key", name="uq_jobs_workspace_idempotency"
        ),
        sa.CheckConstraint(_state_check("state", JOB_STATES), name="ck_job_state"),
        sa.CheckConstraint("attempt >= 0 AND max_attempts > 0", name="ck_job_attempts"),
        sa.CheckConstraint(
            "request_sha256 ~ '^[0-9a-f]{64}$'", name="ck_job_request_sha256"
        ),
        sa.CheckConstraint(
            "(state = 'LEASED') = (lease_owner IS NOT NULL AND lease_expires_at IS NOT NULL)",
            name="ck_job_lease_fields",
        ),
    )
    op.create_index(
        "ix_verification_jobs_claim",
        "verification_jobs",
        ["state", "available_at", "lease_expires_at", "created_at"],
    )
    op.create_index(
        "ix_verification_runs_product_created",
        "verification_runs",
        ["product_id", "created_at"],
    )
    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False, unique=True),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column("byte_length", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["run_id", "workspace_id"],
            ["verification_runs.id", "verification_runs.workspace_id"],
            ondelete="CASCADE",
            name="fk_artifact_run_workspace",
        ),
        sa.UniqueConstraint("id", "workspace_id", name="uq_artifacts_id_workspace"),
        sa.CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="ck_artifact_sha256"),
        sa.CheckConstraint("byte_length >= 0", name="ck_artifact_byte_length"),
    )
    op.create_foreign_key(
        "fk_run_result_artifact",
        "verification_runs",
        "artifacts",
        ["result_artifact_id", "workspace_id"],
        ["id", "workspace_id"],
    )
    op.execute(
        """
        CREATE FUNCTION prevent_artifact_mutation() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'artifacts are immutable';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER artifacts_immutable
        BEFORE UPDATE OR DELETE ON artifacts
        FOR EACH ROW EXECUTE FUNCTION prevent_artifact_mutation();

        CREATE FUNCTION prevent_terminal_run_mutation() RETURNS trigger AS $$
        BEGIN
          IF OLD.state IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
            RAISE EXCEPTION 'terminal verification runs are immutable';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER terminal_runs_immutable
        BEFORE UPDATE OR DELETE ON verification_runs
        FOR EACH ROW EXECUTE FUNCTION prevent_terminal_run_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS prevent_terminal_run_mutation() CASCADE")
    op.execute("DROP FUNCTION IF EXISTS prevent_artifact_mutation() CASCADE")
    op.drop_constraint("fk_run_result_artifact", "verification_runs")
    op.drop_table("artifacts")
    op.drop_index("ix_verification_jobs_claim", table_name="verification_jobs")
    op.drop_table("verification_jobs")
    op.drop_index(
        "ix_verification_runs_product_created", table_name="verification_runs"
    )
    op.drop_table("verification_runs")
    op.drop_constraint(
        "uq_product_configurations_id_product",
        "product_configurations",
        type_="unique",
    )
