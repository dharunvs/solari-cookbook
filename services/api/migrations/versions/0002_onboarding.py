"""Create the lean workspace and onboarding persistence boundary.

Revision ID: 0002_onboarding
Revises: 0001_foundation
Create Date: 2026-09-02
"""
# ruff: noqa: E501

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_onboarding"
down_revision: str | None = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column[object]]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_clerk_user_id", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "onboarding_complete",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        *_timestamps(),
    )
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("workspace_id", "slug", name="uq_projects_workspace_slug"),
    )
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("project_id", "slug", name="uq_products_project_slug"),
    )
    op.create_table(
        "onboarding_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("current_step", sa.Text(), nullable=False, server_default="project"),
        sa.Column("project_name", sa.Text(), nullable=True),
        sa.Column("project_slug", sa.Text(), nullable=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_timestamps(),
    )
    op.create_table(
        "product_configurations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), nullable=False),
        sa.Column("packages", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "product_id", "version", name="uq_product_configuration_version"
        ),
    )
    op.execute(
        """
        CREATE FUNCTION prevent_product_configuration_mutation() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'product configurations are immutable';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER product_configuration_immutable
        BEFORE UPDATE OR DELETE ON product_configurations
        FOR EACH ROW EXECUTE FUNCTION prevent_product_configuration_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP FUNCTION IF EXISTS prevent_product_configuration_mutation() CASCADE"
    )
    op.drop_table("product_configurations")
    op.drop_table("onboarding_drafts")
    op.drop_table("products")
    op.drop_table("projects")
    op.drop_table("workspaces")
