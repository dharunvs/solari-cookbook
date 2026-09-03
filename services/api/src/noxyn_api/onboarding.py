"""Workspace-scoped onboarding persistence and HTTP contract."""
# ruff: noqa: E501

from __future__ import annotations

import json
import re
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from noxyn_api.auth import Principal, current_principal
from noxyn_api.database import get_session_factory

router = APIRouter(prefix="/v1", tags=["onboarding"])

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
UNAVAILABLE = "resource unavailable"


class WorkspaceView(BaseModel):
    id: UUID
    name: str
    onboarding_complete: bool


class DraftView(BaseModel):
    current_step: Literal["project", "product", "configuration", "complete"]
    project_name: str | None = None
    project_slug: str | None = None
    project_id: UUID | None = None
    product_id: UUID | None = None


class MeResponse(BaseModel):
    workspace: WorkspaceView
    onboarding: DraftView
    project_id: UUID | None = None


class DraftUpdate(BaseModel):
    current_step: Literal["project", "product", "configuration"]
    project_name: str | None = Field(default=None, max_length=120)
    project_slug: str | None = Field(default=None, max_length=80)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=80)


class ProjectView(BaseModel):
    id: UUID
    name: str
    slug: str


class ProductCreate(BaseModel):
    slug: Literal["sandbox"] = "sandbox"


class ProductView(BaseModel):
    id: UUID
    project_id: UUID
    slug: Literal["sandbox"]
    name: str


class PackageSpec(BaseModel):
    ecosystem: Literal["python", "typescript", "go"]
    package: str = Field(min_length=1, max_length=160)
    version: str = Field(min_length=1, max_length=80)


class ConfigurationCreate(BaseModel):
    sources: list[str] = Field(min_length=1, max_length=8)
    packages: list[PackageSpec] = Field(min_length=1, max_length=6)


class ConfigurationView(BaseModel):
    id: UUID
    product_id: UUID
    version: Literal[1]
    sources: list[str]
    packages: list[PackageSpec]
    created_at: datetime


def _not_found() -> HTTPException:
    # Deliberately indistinguishable for missing and cross-workspace IDs.
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=UNAVAILABLE)


def _require_idempotency(key: str | None) -> str:
    if key is None or not key.strip() or len(key) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="idempotency key required",
        )
    return key


async def session_dependency() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def _workspace(session: AsyncSession, principal: Principal) -> dict[str, Any]:
    """Provision one private workspace per Clerk subject, idempotently."""
    workspace_id = uuid4()
    result = await session.execute(
        text(
            """
            INSERT INTO workspaces (id, owner_clerk_user_id, name)
            VALUES (:id, :owner, 'My workspace')
            ON CONFLICT (owner_clerk_user_id)
            DO UPDATE SET owner_clerk_user_id = EXCLUDED.owner_clerk_user_id
            RETURNING id, name, onboarding_complete
            """
        ),
        {"id": workspace_id, "owner": principal.subject},
    )
    return dict(result.mappings().one())


async def _draft(session: AsyncSession, workspace_id: UUID) -> dict[str, Any]:
    result = await session.execute(
        text(
            """
            INSERT INTO onboarding_drafts (id, workspace_id, current_step)
            VALUES (:id, :workspace_id, 'project')
            ON CONFLICT (workspace_id) DO UPDATE SET workspace_id = EXCLUDED.workspace_id
            RETURNING current_step, project_name, project_slug, project_id, product_id
            """
        ),
        {"id": uuid4(), "workspace_id": workspace_id},
    )
    return dict(result.mappings().one())


async def _workspace_and_draft(
    session: AsyncSession, principal: Principal
) -> tuple[dict[str, Any], dict[str, Any]]:
    workspace = await _workspace(session, principal)
    draft = await _draft(session, workspace["id"])
    await session.commit()
    return workspace, draft


@router.get("/me", operation_id="getCurrentWorkspace", response_model=MeResponse)
async def get_me(
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> MeResponse:
    workspace, draft = await _workspace_and_draft(session, principal)
    return MeResponse(
        workspace=WorkspaceView(**workspace),
        onboarding=DraftView(**draft),
        project_id=draft["project_id"] if workspace["onboarding_complete"] else None,
    )


@router.patch(
    "/onboarding", operation_id="updateOnboardingDraft", response_model=DraftView
)
async def update_draft(
    payload: DraftUpdate,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> DraftView:
    _require_idempotency(idempotency_key)
    workspace, _ = await _workspace_and_draft(session, principal)
    if payload.project_slug and not SLUG.fullmatch(payload.project_slug):
        raise HTTPException(status_code=422, detail="project slug is invalid")
    result = await session.execute(
        text(
            """
            UPDATE onboarding_drafts
            SET current_step = :current_step, project_name = :project_name,
                project_slug = :project_slug, updated_at = now()
            WHERE workspace_id = :workspace_id
            RETURNING current_step, project_name, project_slug, project_id, product_id
            """
        ),
        {"workspace_id": workspace["id"], **payload.model_dump()},
    )
    await session.commit()
    return DraftView(**dict(result.mappings().one()))


@router.post(
    "/projects",
    operation_id="createProject",
    response_model=ProjectView,
    status_code=201,
)
async def create_project(
    payload: ProjectCreate,
    response: Response,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> ProjectView:
    _require_idempotency(idempotency_key)
    if not SLUG.fullmatch(payload.slug):
        raise HTTPException(status_code=422, detail="project slug is invalid")
    workspace, _ = await _workspace_and_draft(session, principal)
    result = await session.execute(
        text(
            """
            INSERT INTO projects (id, workspace_id, name, slug)
            VALUES (:id, :workspace_id, :name, :slug)
            ON CONFLICT (workspace_id, slug) DO UPDATE SET slug = EXCLUDED.slug
            RETURNING id, name, slug, (xmax = 0) AS created
            """
        ),
        {"id": uuid4(), "workspace_id": workspace["id"], **payload.model_dump()},
    )
    row = dict(result.mappings().one())
    await session.execute(
        text(
            """
            UPDATE onboarding_drafts
            SET current_step = 'product', project_id = :project_id,
                project_name = :name, project_slug = :slug, updated_at = now()
            WHERE workspace_id = :workspace_id
            """
        ),
        {
            "project_id": row["id"],
            "workspace_id": workspace["id"],
            **payload.model_dump(),
        },
    )
    await session.commit()
    if not row.pop("created"):
        response.status_code = status.HTTP_200_OK
    return ProjectView(**row)


async def _project_in_workspace(
    session: AsyncSession, workspace_id: UUID, project_id: UUID
) -> dict[str, Any]:
    result = await session.execute(
        text(
            "SELECT id, name, slug FROM projects WHERE id = :id AND workspace_id = :workspace_id"
        ),
        {"id": project_id, "workspace_id": workspace_id},
    )
    row = result.mappings().one_or_none()
    if row is None:
        raise _not_found()
    return dict(row)


@router.get(
    "/projects/{project_id}", operation_id="getProject", response_model=ProjectView
)
async def get_project(
    project_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ProjectView:
    workspace, _ = await _workspace_and_draft(session, principal)
    result = await _project_in_workspace(session, workspace["id"], project_id)
    await session.commit()
    return ProjectView(**result)


@router.post(
    "/projects/{project_id}/products",
    operation_id="createProduct",
    response_model=ProductView,
    status_code=201,
)
async def create_product(
    project_id: UUID,
    payload: ProductCreate,
    response: Response,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> ProductView:
    _require_idempotency(idempotency_key)
    workspace, _ = await _workspace_and_draft(session, principal)
    await _project_in_workspace(session, workspace["id"], project_id)
    result = await session.execute(
        text(
            """
            INSERT INTO products (id, project_id, slug, name)
            VALUES (:id, :project_id, 'sandbox', 'Sandbox')
            ON CONFLICT (project_id, slug) DO UPDATE SET slug = EXCLUDED.slug
            RETURNING id, project_id, slug, name, (xmax = 0) AS created
            """
        ),
        {"id": uuid4(), "project_id": project_id},
    )
    row = dict(result.mappings().one())
    await session.execute(
        text(
            """
            UPDATE onboarding_drafts SET current_step = 'configuration', product_id = :product_id,
                updated_at = now() WHERE workspace_id = :workspace_id
            """
        ),
        {"product_id": row["id"], "workspace_id": workspace["id"]},
    )
    await session.commit()
    if not row.pop("created"):
        response.status_code = status.HTTP_200_OK
    return ProductView(**row)


async def _product_in_workspace(
    session: AsyncSession, workspace_id: UUID, product_id: UUID
) -> dict[str, Any]:
    result = await session.execute(
        text(
            """
            SELECT products.id, products.project_id, products.slug, products.name
            FROM products JOIN projects ON projects.id = products.project_id
            WHERE products.id = :id AND projects.workspace_id = :workspace_id
            """
        ),
        {"id": product_id, "workspace_id": workspace_id},
    )
    row = result.mappings().one_or_none()
    if row is None:
        raise _not_found()
    return dict(row)


@router.post(
    "/products/{product_id}/configurations",
    operation_id="createProductConfiguration",
    response_model=ConfigurationView,
    status_code=201,
)
async def create_configuration(
    product_id: UUID,
    payload: ConfigurationCreate,
    response: Response,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> ConfigurationView:
    _require_idempotency(idempotency_key)
    workspace, _ = await _workspace_and_draft(session, principal)
    await _product_in_workspace(session, workspace["id"], product_id)
    result = await session.execute(
        text(
            """
            INSERT INTO product_configurations (id, product_id, version, sources, packages)
            VALUES (:id, :product_id, 1, CAST(:sources AS jsonb), CAST(:packages AS jsonb))
            ON CONFLICT (product_id, version) DO NOTHING
            RETURNING id, product_id, version, sources, packages, created_at
            """
        ),
        {
            "id": uuid4(),
            "product_id": product_id,
            "sources": json.dumps(payload.sources),
            "packages": json.dumps([item.model_dump() for item in payload.packages]),
        },
    )
    row = result.mappings().one_or_none()
    if row is None:
        existing = await session.execute(
            text(
                """
                SELECT id, product_id, version, sources, packages, created_at
                FROM product_configurations WHERE product_id = :product_id AND version = 1
                """
            ),
            {"product_id": product_id},
        )
        row = existing.mappings().one()
        response.status_code = status.HTTP_200_OK
    row_data = dict(row)
    await session.execute(
        text(
            """
            UPDATE workspaces SET onboarding_complete = true, updated_at = now()
            WHERE id = :workspace_id
            """
        ),
        {"workspace_id": workspace["id"]},
    )
    await session.execute(
        text(
            """
            UPDATE onboarding_drafts SET current_step = 'complete', updated_at = now()
            WHERE workspace_id = :workspace_id
            """
        ),
        {"workspace_id": workspace["id"]},
    )
    await session.commit()
    return ConfigurationView(**row_data)


@router.get(
    "/products/{product_id}/configuration",
    operation_id="getProductConfiguration",
    response_model=ConfigurationView,
)
async def get_configuration(
    product_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ConfigurationView:
    workspace, _ = await _workspace_and_draft(session, principal)
    await _product_in_workspace(session, workspace["id"], product_id)
    result = await session.execute(
        text(
            """
            SELECT id, product_id, version, sources, packages, created_at
            FROM product_configurations WHERE product_id = :product_id AND version = 1
            """
        ),
        {"product_id": product_id},
    )
    row = result.mappings().one_or_none()
    if row is None:
        raise _not_found()
    await session.commit()
    return ConfigurationView(**dict(row))
