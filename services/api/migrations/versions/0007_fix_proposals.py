"""Add source-bound proposals and independent fix verification jobs.

Revision ID: 0007_fix_proposals
Revises: 0006_typescript_parity
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_fix_proposals"
down_revision: str | None = "0006_typescript_parity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="FIX_PROPOSED"),
        sa.Column("source_sha256", sa.Text(), nullable=False),
        sa.Column("proposed_sha256", sa.Text(), nullable=False),
        sa.Column("source_artifact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "proposed_artifact_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("patch_artifact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changed_lines", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id", "workspace_id"],
            ["verification_runs.id", "verification_runs.workspace_id"],
            name="fk_proposal_run_workspace",
        ),
        sa.ForeignKeyConstraint(
            ["finding_id", "workspace_id"],
            ["findings.id", "findings.workspace_id"],
            name="fk_proposal_finding_workspace",
        ),
        sa.ForeignKeyConstraint(
            ["source_artifact_id", "workspace_id"],
            ["artifacts.id", "artifacts.workspace_id"],
            name="fk_proposal_source_workspace",
        ),
        sa.ForeignKeyConstraint(
            ["proposed_artifact_id", "workspace_id"],
            ["artifacts.id", "artifacts.workspace_id"],
            name="fk_proposal_proposed_workspace",
        ),
        sa.ForeignKeyConstraint(
            ["patch_artifact_id", "workspace_id"],
            ["artifacts.id", "artifacts.workspace_id"],
            name="fk_proposal_patch_workspace",
        ),
        sa.UniqueConstraint("id", "workspace_id", name="uq_proposals_id_workspace"),
        sa.UniqueConstraint(
            "finding_id", "source_sha256", name="uq_proposal_finding_source"
        ),
        sa.CheckConstraint(
            "state IN ('FIX_PROPOSED', 'FIX_VERIFIED', 'DISMISSED')",
            name="ck_proposal_state",
        ),
        sa.CheckConstraint(
            "source_sha256 ~ '^[0-9a-f]{64}$'", name="ck_proposal_source_sha256"
        ),
        sa.CheckConstraint(
            "proposed_sha256 ~ '^[0-9a-f]{64}$'", name="ck_proposal_proposed_sha256"
        ),
        sa.CheckConstraint("changed_lines > 0", name="ck_proposal_changed_lines"),
        sa.CheckConstraint(
            "(state = 'FIX_VERIFIED') = (verified_at IS NOT NULL)",
            name="ck_proposal_verified_at",
        ),
    )
    op.add_column(
        "verification_jobs",
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_job_proposal_workspace",
        "verification_jobs",
        "proposals",
        ["proposal_id", "workspace_id"],
        ["id", "workspace_id"],
    )
    op.add_column(
        "execution_attempts",
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "execution_attempts",
        sa.Column("source_surface", sa.Text(), nullable=False, server_default="python"),
    )
    op.execute(
        "ALTER TABLE execution_attempts DISABLE TRIGGER execution_attempts_immutable"
    )
    op.execute("UPDATE execution_attempts SET source_surface = language")
    op.execute(
        "ALTER TABLE execution_attempts ENABLE TRIGGER execution_attempts_immutable"
    )
    op.alter_column("execution_attempts", "source_surface", server_default=None)
    op.create_foreign_key(
        "fk_execution_proposal_workspace",
        "execution_attempts",
        "proposals",
        ["proposal_id", "workspace_id"],
        ["id", "workspace_id"],
    )
    op.drop_constraint("ck_execution_phase", "execution_attempts", type_="check")
    op.create_check_constraint(
        "ck_execution_phase", "execution_attempts", "phase IN ('VERIFY', 'FIX_VERIFY')"
    )
    op.drop_constraint("uq_execution_attempt", "execution_attempts", type_="unique")
    op.create_index(
        "uq_execution_initial_attempt",
        "execution_attempts",
        ["run_id", "source_surface", "attempt_number"],
        unique=True,
        postgresql_where=sa.text("phase = 'VERIFY'"),
    )
    op.create_index(
        "uq_execution_fix_attempt",
        "execution_attempts",
        ["proposal_id", "attempt_number"],
        unique=True,
        postgresql_where=sa.text("phase = 'FIX_VERIFY'"),
    )
    op.create_check_constraint(
        "ck_execution_proposal_phase",
        "execution_attempts",
        "(phase = 'VERIFY' AND proposal_id IS NULL) OR "
        "(phase = 'FIX_VERIFY' AND proposal_id IS NOT NULL)",
    )
    op.execute(
        """
        CREATE FUNCTION prevent_proposal_binding_mutation() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' OR
             OLD.workspace_id IS DISTINCT FROM NEW.workspace_id OR
             OLD.run_id IS DISTINCT FROM NEW.run_id OR
             OLD.finding_id IS DISTINCT FROM NEW.finding_id OR
             OLD.source_sha256 IS DISTINCT FROM NEW.source_sha256 OR
             OLD.proposed_sha256 IS DISTINCT FROM NEW.proposed_sha256 OR
             OLD.source_artifact_id IS DISTINCT FROM NEW.source_artifact_id OR
             OLD.proposed_artifact_id IS DISTINCT FROM NEW.proposed_artifact_id OR
             OLD.patch_artifact_id IS DISTINCT FROM NEW.patch_artifact_id OR
             OLD.changed_lines IS DISTINCT FROM NEW.changed_lines OR
             OLD.created_at IS DISTINCT FROM NEW.created_at THEN
            RAISE EXCEPTION 'proposal source binding is immutable';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER proposal_bindings_immutable
        BEFORE UPDATE OR DELETE ON proposals
        FOR EACH ROW EXECUTE FUNCTION prevent_proposal_binding_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS prevent_proposal_binding_mutation() CASCADE")
    op.drop_constraint(
        "ck_execution_proposal_phase", "execution_attempts", type_="check"
    )
    op.drop_index("uq_execution_fix_attempt", table_name="execution_attempts")
    op.drop_index("uq_execution_initial_attempt", table_name="execution_attempts")
    op.create_unique_constraint(
        "uq_execution_attempt",
        "execution_attempts",
        ["run_id", "language", "phase", "attempt_number"],
    )
    op.drop_constraint("ck_execution_phase", "execution_attempts", type_="check")
    op.create_check_constraint(
        "ck_execution_phase", "execution_attempts", "phase IN ('VERIFY')"
    )
    op.drop_constraint(
        "fk_execution_proposal_workspace", "execution_attempts", type_="foreignkey"
    )
    op.drop_column("execution_attempts", "source_surface")
    op.drop_column("execution_attempts", "proposal_id")
    op.drop_constraint(
        "fk_job_proposal_workspace", "verification_jobs", type_="foreignkey"
    )
    op.drop_column("verification_jobs", "proposal_id")
    op.drop_table("proposals")
