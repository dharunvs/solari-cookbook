"""Workspace-scoped deterministic fix proposals and verification requests."""
# ruff: noqa: E501

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from noxyn_api.artifacts import ArtifactRecord, ArtifactUnavailable
from noxyn_api.auth import Principal, current_principal
from noxyn_api.onboarding import (
    _not_found,
    _require_idempotency,
    _workspace_and_draft,
    session_dependency,
)
from noxyn_api.proposal_engine import ProposalRejected, propose_memory_rename
from noxyn_api.runs import (
    EXECUTION_SELECT,
    ArtifactView,
    ExecutionView,
    _artifact_reader,
    _execution_view,
    _require_csrf,
    _run_in_workspace,
)

router = APIRouter(prefix="/v1", tags=["fix proposals"])


class ProposalView(BaseModel):
    id: UUID
    run_id: UUID
    finding_id: UUID
    state: Literal["FIX_PROPOSED", "FIX_VERIFIED", "DISMISSED"]
    source_surface: Literal["python", "docs_python"]
    source_path: str
    source_sha256: str
    proposed_sha256: str
    changed_lines: int
    patch: str
    created_at: datetime
    verified_at: datetime | None
    verification_job_state: (
        Literal["QUEUED", "LEASED", "COMPLETED", "FAILED", "CANCELLED"] | None
    )
    verification: ExecutionView | None
    source_artifact: ArtifactView
    proposed_artifact: ArtifactView
    patch_artifact: ArtifactView
    checkout_modified: Literal[False] = False


class ProposalList(BaseModel):
    items: list[ProposalView]


PROPOSAL_SELECT = """
SELECT p.id, p.run_id, p.finding_id, p.state, p.source_sha256,
       p.proposed_sha256, p.changed_lines, p.created_at, p.verified_at,
       f.source_surface, f.source_path,
       source.id AS source_artifact_id, source.kind AS source_artifact_kind,
       source.object_key AS source_object_key, source.sha256 AS source_artifact_sha256,
       source.byte_length AS source_artifact_byte_length, source.created_at AS source_artifact_created_at,
       proposed.id AS proposed_artifact_id, proposed.kind AS proposed_artifact_kind,
       proposed.object_key AS proposed_object_key, proposed.sha256 AS proposed_artifact_sha256,
       proposed.byte_length AS proposed_artifact_byte_length, proposed.created_at AS proposed_artifact_created_at,
       patch.id AS patch_artifact_id, patch.kind AS patch_artifact_kind,
       patch.object_key AS patch_object_key, patch.sha256 AS patch_artifact_sha256,
       patch.byte_length AS patch_artifact_byte_length, patch.created_at AS patch_artifact_created_at,
       job.state AS verification_job_state
FROM proposals p
JOIN findings f ON f.id = p.finding_id AND f.workspace_id = p.workspace_id
JOIN artifacts source ON source.id = p.source_artifact_id AND source.workspace_id = p.workspace_id
JOIN artifacts proposed ON proposed.id = p.proposed_artifact_id AND proposed.workspace_id = p.workspace_id
JOIN artifacts patch ON patch.id = p.patch_artifact_id AND patch.workspace_id = p.workspace_id
LEFT JOIN LATERAL (
  SELECT state FROM verification_jobs
  WHERE proposal_id = p.id AND workspace_id = p.workspace_id
  ORDER BY created_at DESC LIMIT 1
) job ON true
"""


def _artifact_view(row: dict[str, Any], prefix: str) -> ArtifactView:
    return ArtifactView(
        id=row[f"{prefix}_artifact_id"],
        kind=row[f"{prefix}_artifact_kind"],
        sha256=row[f"{prefix}_artifact_sha256"],
        byte_length=row[f"{prefix}_artifact_byte_length"],
        created_at=row[f"{prefix}_artifact_created_at"],
    )


async def _proposal_view(session: AsyncSession, row: dict[str, Any]) -> ProposalView:
    try:
        patch_body = await asyncio.to_thread(
            _artifact_reader().read,
            ArtifactRecord(
                row["patch_object_key"],
                row["patch_artifact_sha256"],
                row["patch_artifact_byte_length"],
            ),
        )
    except (ArtifactUnavailable, UnicodeDecodeError):
        raise HTTPException(
            status_code=409, detail="proposal evidence unavailable"
        ) from None
    result = await session.execute(
        text(
            EXECUTION_SELECT
            + " WHERE e.proposal_id = :proposal_id AND e.workspace_id = :workspace_id"
            + " ORDER BY e.attempt_number DESC LIMIT 1"
        ),
        {"proposal_id": row["id"], "workspace_id": row["workspace_id"]},
    )
    execution_row = result.mappings().one_or_none()
    return ProposalView(
        id=row["id"],
        run_id=row["run_id"],
        finding_id=row["finding_id"],
        state=row["state"],
        source_surface=row["source_surface"],
        source_path=row["source_path"],
        source_sha256=row["source_sha256"],
        proposed_sha256=row["proposed_sha256"],
        changed_lines=row["changed_lines"],
        patch=patch_body.decode("utf-8"),
        created_at=row["created_at"],
        verified_at=row["verified_at"],
        verification_job_state=row["verification_job_state"],
        verification=(
            await _execution_view(dict(execution_row)) if execution_row else None
        ),
        source_artifact=_artifact_view(row, "source"),
        proposed_artifact=_artifact_view(row, "proposed"),
        patch_artifact=_artifact_view(row, "patch"),
    )


async def _proposal_row(
    session: AsyncSession, workspace_id: UUID, proposal_id: UUID
) -> dict[str, Any]:
    result = await session.execute(
        text(
            PROPOSAL_SELECT
            + " WHERE p.id = :proposal_id AND p.workspace_id = :workspace_id"
        ),
        {"proposal_id": proposal_id, "workspace_id": workspace_id},
    )
    row = result.mappings().one_or_none()
    if row is None:
        raise _not_found()
    return {**dict(row), "workspace_id": workspace_id}


async def _record_artifact(
    session: AsyncSession, *, workspace_id: UUID, run_id: UUID, kind: str, body: bytes
) -> UUID:
    reference = await asyncio.to_thread(
        _artifact_reader().put,
        workspace_id=workspace_id,
        run_id=run_id,
        kind=kind.lower().replace("_", "-"),
        body=body,
    )
    artifact_id = uuid5(NAMESPACE_URL, f"noxyn:{reference.object_key}")
    await session.execute(
        text("""
            INSERT INTO artifacts (id, workspace_id, run_id, kind, object_key, sha256, byte_length)
            VALUES (:id, :workspace_id, :run_id, :kind, :object_key, :sha256, :byte_length)
            ON CONFLICT (object_key) DO NOTHING
        """),
        {
            "id": artifact_id,
            "workspace_id": workspace_id,
            "run_id": run_id,
            "kind": kind,
            "object_key": reference.object_key,
            "sha256": reference.sha256,
            "byte_length": reference.byte_length,
        },
    )
    return artifact_id


@router.post(
    "/findings/{finding_id}/proposals",
    operation_id="createFindingProposal",
    response_model=ProposalView,
    status_code=201,
)
async def create_proposal(
    finding_id: UUID,
    response: Response,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> ProposalView:
    _require_idempotency(idempotency_key)
    _require_csrf(csrf_token)
    workspace, _ = await _workspace_and_draft(session, principal)
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"proposal:{workspace['id']}:{finding_id}"},
    )
    result = await session.execute(
        text("""
        SELECT f.id, f.run_id, f.source_surface, f.source_path, f.lifecycle_state,
               f.evidence_artifact_id, a.object_key, a.sha256, a.byte_length
        FROM findings f JOIN artifacts a ON a.id = f.evidence_artifact_id AND a.workspace_id = f.workspace_id
        WHERE f.id = :finding_id AND f.workspace_id = :workspace_id FOR UPDATE OF f
    """),
        {"finding_id": finding_id, "workspace_id": workspace["id"]},
    )
    finding = result.mappings().one_or_none()
    if finding is None:
        raise _not_found()
    existing = await session.execute(
        text(
            "SELECT id FROM proposals WHERE finding_id = :finding_id AND workspace_id = :workspace_id"
        ),
        {"finding_id": finding_id, "workspace_id": workspace["id"]},
    )
    existing_id = existing.scalar_one_or_none()
    if existing_id is not None:
        response.status_code = 200
        await session.commit()
        return await _proposal_view(
            session, await _proposal_row(session, workspace["id"], existing_id)
        )
    if finding["lifecycle_state"] != "REPRODUCED":
        raise HTTPException(status_code=409, detail="finding is not reproduced")
    record = ArtifactRecord(
        finding["object_key"], finding["sha256"], finding["byte_length"]
    )
    try:
        source = await asyncio.to_thread(_artifact_reader().read, record)
        change = propose_memory_rename(
            source, surface=finding["source_surface"], path=finding["source_path"]
        )
    except (ArtifactUnavailable, ProposalRejected) as exc:
        raise HTTPException(
            status_code=409, detail=f"proposal rejected: {exc}"
        ) from None
    proposed_sha = hashlib.sha256(change.proposed).hexdigest()
    proposed_id = await _record_artifact(
        session,
        workspace_id=workspace["id"],
        run_id=finding["run_id"],
        kind="PROPOSED_SOURCE",
        body=change.proposed,
    )
    patch_id = await _record_artifact(
        session,
        workspace_id=workspace["id"],
        run_id=finding["run_id"],
        kind="PROPOSAL_PATCH",
        body=change.patch,
    )
    proposal_id = uuid5(
        NAMESPACE_URL, f"noxyn:{finding_id}:{finding['sha256']}:{proposed_sha}"
    )
    await session.execute(
        text("""
        INSERT INTO proposals (id, workspace_id, run_id, finding_id, source_sha256,
          proposed_sha256, source_artifact_id, proposed_artifact_id, patch_artifact_id, changed_lines)
        VALUES (:id, :workspace_id, :run_id, :finding_id, :source_sha256,
          :proposed_sha256, :source_artifact_id, :proposed_artifact_id, :patch_artifact_id, :changed_lines)
    """),
        {
            "id": proposal_id,
            "workspace_id": workspace["id"],
            "run_id": finding["run_id"],
            "finding_id": finding_id,
            "source_sha256": finding["sha256"],
            "proposed_sha256": proposed_sha,
            "source_artifact_id": finding["evidence_artifact_id"],
            "proposed_artifact_id": proposed_id,
            "patch_artifact_id": patch_id,
            "changed_lines": change.changed_lines,
        },
    )
    await session.execute(
        text(
            "UPDATE findings SET lifecycle_state = 'FIX_PROPOSED' WHERE id = :id AND workspace_id = :workspace_id"
        ),
        {"id": finding_id, "workspace_id": workspace["id"]},
    )
    await session.commit()
    return await _proposal_view(
        session, await _proposal_row(session, workspace["id"], proposal_id)
    )


@router.get(
    "/proposals/{proposal_id}", operation_id="getProposal", response_model=ProposalView
)
async def get_proposal(
    proposal_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ProposalView:
    workspace, _ = await _workspace_and_draft(session, principal)
    view = await _proposal_view(
        session, await _proposal_row(session, workspace["id"], proposal_id)
    )
    await session.commit()
    return view


@router.get(
    "/runs/{run_id}/proposals",
    operation_id="listRunProposals",
    response_model=ProposalList,
)
async def list_proposals(
    run_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ProposalList:
    workspace, _ = await _workspace_and_draft(session, principal)
    await _run_in_workspace(session, workspace["id"], run_id)
    result = await session.execute(
        text(
            PROPOSAL_SELECT
            + " WHERE p.run_id = :run_id AND p.workspace_id = :workspace_id ORDER BY p.created_at"
        ),
        {"run_id": run_id, "workspace_id": workspace["id"]},
    )
    items = [
        await _proposal_view(session, {**dict(row), "workspace_id": workspace["id"]})
        for row in result.mappings().all()
    ]
    await session.commit()
    return ProposalList(items=items)


@router.post(
    "/proposals/{proposal_id}/verify",
    operation_id="verifyProposal",
    response_model=ProposalView,
    status_code=202,
)
async def verify_proposal(
    proposal_id: UUID,
    response: Response,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> ProposalView:
    key = _require_idempotency(idempotency_key)
    _require_csrf(csrf_token)
    workspace, _ = await _workspace_and_draft(session, principal)
    row = await _proposal_row(session, workspace["id"], proposal_id)
    if row["state"] == "FIX_VERIFIED":
        response.status_code = 200
        return await _proposal_view(session, row)
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"verify:{workspace['id']}:{proposal_id}"},
    )
    existing = await session.execute(
        text("""
        SELECT id FROM verification_jobs WHERE proposal_id = :proposal_id
          AND workspace_id = :workspace_id AND state IN ('QUEUED', 'LEASED', 'COMPLETED')
        ORDER BY created_at DESC LIMIT 1
    """),
        {"proposal_id": proposal_id, "workspace_id": workspace["id"]},
    )
    if existing.scalar_one_or_none() is not None:
        response.status_code = 200
    else:
        request_sha = hashlib.sha256(
            json.dumps(
                {
                    "proposal_id": str(proposal_id),
                    "proposed_sha256": row["proposed_sha256"],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        await session.execute(
            text("""
            INSERT INTO verification_jobs (id, workspace_id, run_id, proposal_id, kind,
              state, idempotency_key, request_sha256, max_attempts)
            VALUES (:id, :workspace_id, :run_id, :proposal_id, 'FIX_VERIFICATION',
              'QUEUED', :key, :request_sha256, 3)
        """),
            {
                "id": uuid4(),
                "workspace_id": workspace["id"],
                "run_id": row["run_id"],
                "proposal_id": proposal_id,
                "key": key,
                "request_sha256": request_sha,
            },
        )
    await session.commit()
    return await _proposal_view(
        session, await _proposal_row(session, workspace["id"], proposal_id)
    )
