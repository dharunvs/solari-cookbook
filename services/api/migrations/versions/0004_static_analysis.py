"""Persist workspace-scoped static findings.

Revision ID: 0004_static_analysis
Revises: 0003_durable_runs
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_static_analysis"
down_revision: str | None = "0003_durable_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("capability_id", sa.Text(), nullable=False),
        sa.Column("source_surface", sa.Text(), nullable=False),
        sa.Column("static_state", sa.Text(), nullable=False),
        sa.Column("lifecycle_state", sa.Text(), nullable=False),
        sa.Column("expected_value", sa.Text(), nullable=False),
        sa.Column("observed_value", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("source_locator", sa.Text(), nullable=False),
        sa.Column("source_excerpt", sa.Text(), nullable=False),
        sa.Column(
            "evidence_artifact_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
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
            name="fk_finding_run_workspace",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_artifact_id", "workspace_id"],
            ["artifacts.id", "artifacts.workspace_id"],
            name="fk_finding_artifact_workspace",
        ),
        sa.UniqueConstraint("id", "workspace_id", name="uq_findings_id_workspace"),
        sa.UniqueConstraint(
            "run_id", "capability_id", "source_surface", name="uq_finding_identity"
        ),
        sa.CheckConstraint(
            "static_state IN ('ALIGNED', 'SUSPECTED', 'NOT_EXPECTED', 'UNVERIFIED')",
            name="ck_finding_static_state",
        ),
        sa.CheckConstraint(
            "lifecycle_state IN ('SUSPECTED', 'REPRODUCED', 'FIX_PROPOSED', "
            "'FIX_VERIFIED', 'DISMISSED', 'UNVERIFIED')",
            name="ck_finding_lifecycle_state",
        ),
    )
    op.create_index("ix_findings_run", "findings", ["run_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_findings_run", table_name="findings")
    op.drop_table("findings")
