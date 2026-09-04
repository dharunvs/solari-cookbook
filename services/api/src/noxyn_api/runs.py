"""Workspace-scoped durable verification run API."""
# ruff: noqa: E501

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime
from functools import lru_cache
from typing import Annotated, Any, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from noxyn_api.artifacts import (
    ArtifactRecord,
    ArtifactUnavailable,
    LocalArtifactReader,
)
from noxyn_api.auth import Principal, current_principal
from noxyn_api.config import load_settings
from noxyn_api.onboarding import (
    _not_found,
    _product_in_workspace,
    _require_idempotency,
    _workspace_and_draft,
    session_dependency,
)

router = APIRouter(prefix="/v1", tags=["verification runs"])

RunState = Literal[
    "QUEUED",
    "SNAPSHOTTING",
    "ANALYZING",
    "VERIFYING",
    "PROPOSING",
    "REVERIFYING",
    "CANCEL_REQUESTED",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
]
TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED"}


class RunCreate(BaseModel):
    scenario: Literal["controlled_api_evolution", "current_configured_solari"] = (
        "controlled_api_evolution"
    )


class ArtifactView(BaseModel):
    id: UUID
    kind: str
    sha256: str
    byte_length: int
    created_at: datetime


class RunView(BaseModel):
    id: UUID
    product_id: UUID
    configuration_id: UUID
    configuration_version: int
    scenario: str
    state: RunState
    attempt: int
    max_attempts: int
    cancel_requested_at: datetime | None = None
    error_code: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    artifact: ArtifactView | None = None


class RunList(BaseModel):
    items: list[RunView]


def _camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.title() for part in rest)


class AnalysisModel(BaseModel):
    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)


class MatrixEvidenceView(AnalysisModel):
    path: str
    sha256: str
    locator: str
    excerpt: str


class MatrixCellView(AnalysisModel):
    surface: str
    state: Literal["ALIGNED", "SUSPECTED", "NOT_EXPECTED", "UNVERIFIED"]
    expected: str
    observed: str | None
    summary: str
    evidence: MatrixEvidenceView | None
    finding_id: UUID | None = None


class RuntimeCellView(AnalysisModel):
    state: Literal["NOT_RUN", "PASS", "FAIL", "UNVERIFIED"]
    summary: str
    language: Literal["python", "typescript", "go"] = "python"
    source_surface: str = "python"
    infrastructure_state: Literal["PASS", "FAIL"] | None = None
    subject_state: Literal["PASS", "FAIL", "NOT_RUN"] | None = None
    execution_id: UUID | None = None
    backend: Literal["REPLAY", "SOLARI"] | None = None


class MatrixRowView(AnalysisModel):
    capability_id: str
    label: str
    cells: list[MatrixCellView]
    runtime: RuntimeCellView
    runtime_cells: list[RuntimeCellView] = Field(default_factory=list)


class ParityView(AnalysisModel):
    state: Literal["MATCH", "DIFFERENT", "INCOMPLETE"]
    summary: str
    compared_languages: list[Literal["python", "typescript", "go"]]


class MatrixSummaryView(AnalysisModel):
    capabilities: int
    aligned: int
    suspected: int
    not_expected: int
    unverified: int


class ContractDiffView(AnalysisModel):
    capability_id: str
    before: str
    after: str
    classification: Literal["RENAMED"]


class SourceSnapshotView(AnalysisModel):
    surface: str
    kind: str
    path: str
    sha256: str | None = None
    identity: str
    source_revision: str | None = None
    retrieved_at: datetime
    unavailable_reason: str | None = None


class PackageIdentityView(AnalysisModel):
    name: str
    version: str
    import_: str = Field(alias="import")


class MatrixView(AnalysisModel):
    schema_version: Literal["noxyn-static-analysis-result/1.0"]
    scenario: Literal["sandbox-create-evolution", "current-configured-solari"]
    fixture: bool
    parser_version: str
    manifest_sha256: str
    contract_diff: ContractDiffView | None = None
    packages: dict[str, PackageIdentityView]
    source_snapshots: list[SourceSnapshotView] = Field(default_factory=list)
    summary: MatrixSummaryView
    rows: list[MatrixRowView]
    parity: ParityView | None = None


class FindingEvidenceView(BaseModel):
    artifact_id: UUID
    path: str
    sha256: str
    locator: str
    excerpt: str


class FindingView(BaseModel):
    id: UUID
    run_id: UUID
    capability_id: str
    source_surface: str
    static_state: Literal["SUSPECTED"]
    lifecycle_state: Literal[
        "SUSPECTED",
        "REPRODUCED",
        "FIX_PROPOSED",
        "FIX_VERIFIED",
        "DISMISSED",
        "UNVERIFIED",
    ]
    expected_value: str
    observed_value: str | None
    summary: str
    evidence: FindingEvidenceView
    created_at: datetime


class FindingList(BaseModel):
    items: list[FindingView]


class ExecutionView(BaseModel):
    id: UUID
    run_id: UUID
    finding_id: UUID | None
    proposal_id: UUID | None
    attempt_number: int
    language: Literal["python", "typescript", "go"]
    source_surface: str
    phase: Literal["VERIFY", "FIX_VERIFY"]
    backend: Literal["REPLAY", "SOLARI"]
    infrastructure_state: Literal["PASS", "FAIL"]
    infrastructure_step: str
    subject_state: Literal["PASS", "FAIL", "NOT_RUN"]
    sandbox_id: str | None
    package_name: str
    package_version: str
    source_path: str
    source_sha256: str
    command_sha256: str
    exit_code: int | None
    stdout: str
    stderr: str
    output_truncated: bool
    cleanup_state: Literal["PASS", "FAIL", "NOT_REQUIRED"]
    cancelled: bool
    error_code: str | None
    duration_ms: int
    started_at: datetime
    completed_at: datetime
    evidence: ArtifactView


class ExecutionList(BaseModel):
    items: list[ExecutionView]


@lru_cache(maxsize=1)
def _artifact_reader() -> LocalArtifactReader:
    return LocalArtifactReader(load_settings().artifact_root)


def _require_csrf(value: str | None) -> None:
    if value != "same-origin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="request origin unavailable",
        )


def _request_hash(*, product_id: UUID, scenario: str) -> str:
    canonical = json.dumps(
        {"product_id": str(product_id), "scenario": scenario},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


RUN_SELECT = """
SELECT r.id, r.product_id, r.configuration_id,
       c.version AS configuration_version, r.scenario, r.state,
       j.attempt, j.max_attempts, r.cancel_requested_at, r.error_code,
       r.created_at, r.started_at, r.completed_at,
       a.id AS artifact_id, a.kind AS artifact_kind, a.sha256 AS artifact_sha256,
       a.byte_length AS artifact_byte_length, a.created_at AS artifact_created_at
FROM verification_runs r
JOIN product_configurations c ON c.id = r.configuration_id
JOIN verification_jobs j ON j.run_id = r.id AND j.kind = 'STATIC_ANALYSIS'
LEFT JOIN artifacts a ON a.id = r.result_artifact_id
                     AND a.workspace_id = r.workspace_id
"""


def _run_view(row: dict[str, Any]) -> RunView:
    artifact = None
    if row["artifact_id"] is not None:
        artifact = ArtifactView(
            id=row["artifact_id"],
            kind=row["artifact_kind"],
            sha256=row["artifact_sha256"],
            byte_length=row["artifact_byte_length"],
            created_at=row["artifact_created_at"],
        )
    return RunView(
        **{key: value for key, value in row.items() if not key.startswith("artifact_")},
        artifact=artifact,
    )


async def _run_in_workspace(
    session: AsyncSession, workspace_id: UUID, run_id: UUID
) -> RunView:
    result = await session.execute(
        text(RUN_SELECT + " WHERE r.id = :run_id AND r.workspace_id = :workspace_id"),
        {"run_id": run_id, "workspace_id": workspace_id},
    )
    row = result.mappings().one_or_none()
    if row is None:
        raise _not_found()
    return _run_view(dict(row))


@router.post(
    "/products/{product_id}/runs",
    operation_id="startVerificationRun",
    response_model=RunView,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_run(
    product_id: UUID,
    payload: RunCreate,
    response: Response,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> RunView:
    key = _require_idempotency(idempotency_key)
    _require_csrf(csrf_token)
    workspace, _ = await _workspace_and_draft(session, principal)
    await _product_in_workspace(session, workspace["id"], product_id)
    request_sha256 = _request_hash(product_id=product_id, scenario=payload.scenario)

    # Serialize a workspace/key pair so concurrent retries cannot create orphan runs.
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
        {"lock_key": f"{workspace['id']}:{key}"},
    )
    existing = await session.execute(
        text(
            """
            SELECT run_id, request_sha256 FROM verification_jobs
            WHERE workspace_id = :workspace_id AND idempotency_key = :key
            """
        ),
        {"workspace_id": workspace["id"], "key": key},
    )
    existing_row = existing.mappings().one_or_none()
    if existing_row is not None:
        if existing_row["request_sha256"] != request_sha256:
            raise HTTPException(status_code=409, detail="idempotency key conflict")
        response.status_code = status.HTTP_200_OK
        view = await _run_in_workspace(session, workspace["id"], existing_row["run_id"])
        await session.commit()
        return view

    configuration = await session.execute(
        text(
            """
            SELECT id FROM product_configurations
            WHERE product_id = :product_id ORDER BY version DESC LIMIT 1
            """
        ),
        {"product_id": product_id},
    )
    configuration_id = configuration.scalar_one_or_none()
    if configuration_id is None:
        raise HTTPException(status_code=409, detail="product is not configured")
    run_id, job_id = uuid4(), uuid4()
    await session.execute(
        text(
            """
            INSERT INTO verification_runs (
                id, workspace_id, product_id, configuration_id, scenario, state
            ) VALUES (
                :run_id, :workspace_id, :product_id, :configuration_id, :scenario, 'QUEUED'
            )
            """
        ),
        {
            "run_id": run_id,
            "workspace_id": workspace["id"],
            "product_id": product_id,
            "configuration_id": configuration_id,
            "scenario": payload.scenario,
        },
    )
    await session.execute(
        text(
            """
            INSERT INTO verification_jobs (
                id, workspace_id, run_id, kind, state,
                idempotency_key, request_sha256
            ) VALUES (
                :job_id, :workspace_id, :run_id, 'STATIC_ANALYSIS', 'QUEUED',
                :idempotency_key, :request_sha256
            )
            """
        ),
        {
            "job_id": job_id,
            "workspace_id": workspace["id"],
            "run_id": run_id,
            "idempotency_key": key,
            "request_sha256": request_sha256,
        },
    )
    await session.commit()
    return await _run_in_workspace(session, workspace["id"], run_id)


@router.get(
    "/products/{product_id}/runs",
    operation_id="listVerificationRuns",
    response_model=RunList,
)
async def list_runs(
    product_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    limit: Annotated[int, Query(ge=1, le=50)] = 25,
) -> RunList:
    workspace, _ = await _workspace_and_draft(session, principal)
    await _product_in_workspace(session, workspace["id"], product_id)
    result = await session.execute(
        text(
            RUN_SELECT
            + " WHERE r.product_id = :product_id AND r.workspace_id = :workspace_id"
            + " ORDER BY r.created_at DESC LIMIT :limit"
        ),
        {"product_id": product_id, "workspace_id": workspace["id"], "limit": limit},
    )
    await session.commit()
    return RunList(items=[_run_view(dict(row)) for row in result.mappings().all()])


@router.get("/runs/{run_id}", operation_id="getVerificationRun", response_model=RunView)
async def get_run(
    run_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> RunView:
    workspace, _ = await _workspace_and_draft(session, principal)
    view = await _run_in_workspace(session, workspace["id"], run_id)
    await session.commit()
    return view


@router.post(
    "/runs/{run_id}/cancel",
    operation_id="cancelVerificationRun",
    response_model=RunView,
)
async def cancel_run(
    run_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> RunView:
    _require_idempotency(idempotency_key)
    _require_csrf(csrf_token)
    workspace, _ = await _workspace_and_draft(session, principal)
    current = await _run_in_workspace(session, workspace["id"], run_id)
    if current.state not in TERMINAL_STATES:
        job = await session.execute(
            text(
                """
                SELECT state FROM verification_jobs
                WHERE run_id = :run_id AND workspace_id = :workspace_id
                FOR UPDATE
                """
            ),
            {"run_id": run_id, "workspace_id": workspace["id"]},
        )
        job_state = job.scalar_one()
        if job_state == "QUEUED":
            await session.execute(
                text(
                    """
                    UPDATE verification_jobs SET state = 'CANCELLED', updated_at = now()
                    WHERE run_id = :run_id AND workspace_id = :workspace_id AND state = 'QUEUED'
                    """
                ),
                {"run_id": run_id, "workspace_id": workspace["id"]},
            )
            target_state, completed_at = "CANCELLED", "now()"
        else:
            target_state, completed_at = "CANCEL_REQUESTED", "NULL"
        await session.execute(
            text(
                f"""
                UPDATE verification_runs
                SET state = :state, cancel_requested_at = COALESCE(cancel_requested_at, now()),
                    completed_at = {completed_at}
                WHERE id = :run_id AND workspace_id = :workspace_id
                  AND state NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')
                """
            ),
            {
                "state": target_state,
                "run_id": run_id,
                "workspace_id": workspace["id"],
            },
        )
    await session.commit()
    return await _run_in_workspace(session, workspace["id"], run_id)


async def _matrix_for_run(
    session: AsyncSession, workspace_id: UUID, run_id: UUID
) -> MatrixView:
    await _run_in_workspace(session, workspace_id, run_id)
    result = await session.execute(
        text(
            """
            SELECT a.object_key, a.sha256, a.byte_length
            FROM artifacts a
            WHERE a.run_id = :run_id AND a.workspace_id = :workspace_id
              AND a.kind = 'CAPABILITY_MATRIX'
            ORDER BY a.created_at DESC LIMIT 1
            """
        ),
        {"run_id": run_id, "workspace_id": workspace_id},
    )
    row = result.mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=409, detail="analysis not available")
    try:
        body = await asyncio.to_thread(
            _artifact_reader().read,
            ArtifactRecord(
                object_key=row["object_key"],
                sha256=row["sha256"],
                byte_length=row["byte_length"],
            ),
        )
        matrix = MatrixView.model_validate_json(body)
    except (ArtifactUnavailable, ValueError):
        raise HTTPException(
            status_code=409, detail="analysis evidence unavailable"
        ) from None
    executions = await session.execute(
        text(
            """
            SELECT DISTINCT ON (source_surface)
                   id, language, source_surface, backend,
                   infrastructure_state, subject_state
            FROM execution_attempts
            WHERE run_id = :run_id AND workspace_id = :workspace_id
              AND source_surface IN ('python', 'docs_python', 'typescript', 'go')
              AND phase = 'VERIFY'
            ORDER BY source_surface, attempt_number DESC
            """
        ),
        {"run_id": run_id, "workspace_id": workspace_id},
    )
    runtime_rows = {row["source_surface"]: row for row in executions.mappings().all()}
    runtime_cells: list[RuntimeCellView] = []
    for source_surface, language, label in (
        ("python", "python", "Python example"),
        ("docs_python", "python", "Python documentation"),
        ("typescript", "typescript", "TypeScript example"),
        ("go", "go", "Go example"),
    ):
        runtime = runtime_rows.get(source_surface)
        if runtime is None:
            runtime_cells.append(
                RuntimeCellView(
                    language=cast(Literal["python", "typescript", "go"], language),
                    source_surface=source_surface,
                    state="NOT_RUN",
                    summary=f"The {label} subject has not run.",
                )
            )
            continue
        runtime_state = cast(
            Literal["PASS", "FAIL", "UNVERIFIED"],
            "UNVERIFIED"
            if runtime["infrastructure_state"] == "FAIL"
            else runtime["subject_state"],
        )
        summary = (
            f"Infrastructure failed; the {label} subject was not run."
            if runtime_state == "UNVERIFIED"
            else f"The {label} subject passed."
            if runtime_state == "PASS"
            else f"The {label} failure was reproduced."
        )
        runtime_cells.append(
            RuntimeCellView(
                language=cast(Literal["python", "typescript", "go"], language),
                source_surface=source_surface,
                state=runtime_state,
                summary=summary,
                infrastructure_state=runtime["infrastructure_state"],
                subject_state=runtime["subject_state"],
                execution_id=runtime["id"],
                backend=runtime["backend"],
            )
        )
    comparable = [
        cell
        for cell in runtime_cells
        if cell.source_surface in {"python", "typescript", "go"}
        and cell.infrastructure_state == "PASS"
        and cell.subject_state in {"PASS", "FAIL"}
    ]
    if len(comparable) < 3:
        parity = ParityView(
            state="INCOMPLETE",
            summary=(
                "Python, TypeScript, and Go subjects need verified infrastructure "
                "results before comparison."
            ),
            compared_languages=[cell.language for cell in comparable],
        )
    elif len({cell.subject_state for cell in comparable}) == 1:
        parity = ParityView(
            state="MATCH",
            summary=(
                f"Python, TypeScript, and Go all report {comparable[0].subject_state}."
            ),
            compared_languages=["python", "typescript", "go"],
        )
    else:
        parity = ParityView(
            state="DIFFERENT",
            summary=(
                "Python reproduces the stale parameter while TypeScript and Go "
                "pass with memMb and MemMb."
            ),
            compared_languages=["python", "typescript", "go"],
        )
    legacy_runtime = next(
        (cell for cell in runtime_cells if cell.source_surface == "python"),
        RuntimeCellView(
            language="python",
            state="NOT_RUN",
            summary="The Python subject has not run.",
        ),
    )
    rows = [
        row.model_copy(
            update={"runtime": legacy_runtime, "runtime_cells": runtime_cells}
        )
        for row in matrix.rows
    ]
    matrix = matrix.model_copy(update={"rows": rows, "parity": parity})
    return matrix


@router.get(
    "/runs/{run_id}/matrix",
    operation_id="getVerificationMatrix",
    response_model=MatrixView,
)
async def get_matrix(
    run_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> MatrixView:
    workspace, _ = await _workspace_and_draft(session, principal)
    matrix = await _matrix_for_run(session, workspace["id"], run_id)
    await session.commit()
    return matrix


EXECUTION_SELECT = """
SELECT e.id, e.run_id, e.finding_id, e.proposal_id, e.attempt_number,
       e.language, e.source_surface, e.phase,
       e.backend, e.infrastructure_state, e.infrastructure_step, e.subject_state,
       e.sandbox_id, e.package_name, e.package_version, e.source_sha256,
       e.command_sha256, e.exit_code, e.output_truncated, e.cleanup_state,
       e.cancelled, e.error_code, e.duration_ms, e.started_at, e.completed_at,
       a.id AS evidence_id, a.kind AS evidence_kind, a.object_key,
       a.sha256 AS evidence_sha256, a.byte_length AS evidence_byte_length,
       a.created_at AS evidence_created_at
FROM execution_attempts e
JOIN artifacts a ON a.id = e.evidence_artifact_id
                AND a.workspace_id = e.workspace_id
"""


async def _execution_view(row: dict[str, Any]) -> ExecutionView:
    try:
        body = await asyncio.to_thread(
            _artifact_reader().read,
            ArtifactRecord(
                object_key=row["object_key"],
                sha256=row["evidence_sha256"],
                byte_length=row["evidence_byte_length"],
            ),
        )
        payload = json.loads(body)
        if (
            payload.get("schemaVersion") != "noxyn-execution-evidence/1.0"
            or payload.get("sourceSha256") != row["source_sha256"]
            or payload.get("commandSha256") != row["command_sha256"]
            or payload.get("backend") != row["backend"]
            or payload.get("language") != row["language"]
            or payload.get("sourceSurface", row["source_surface"])
            != row["source_surface"]
            or payload.get("phase") != row["phase"]
            or payload.get("packageName") != row["package_name"]
            or payload.get("packageVersion") != row["package_version"]
        ):
            raise ArtifactUnavailable("execution evidence disagrees with metadata")
    except (ArtifactUnavailable, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=409, detail="execution evidence unavailable"
        ) from None
    evidence = ArtifactView(
        id=row["evidence_id"],
        kind=row["evidence_kind"],
        sha256=row["evidence_sha256"],
        byte_length=row["evidence_byte_length"],
        created_at=row["evidence_created_at"],
    )
    excluded = {
        "evidence_id",
        "evidence_kind",
        "evidence_sha256",
        "evidence_byte_length",
        "evidence_created_at",
        "object_key",
    }
    values = {key: value for key, value in row.items() if key not in excluded}
    return ExecutionView(
        **values,
        source_path=payload["sourcePath"],
        stdout=payload["stdout"],
        stderr=payload["stderr"],
        evidence=evidence,
    )


@router.get(
    "/runs/{run_id}/executions",
    operation_id="listRunExecutions",
    response_model=ExecutionList,
)
async def list_executions(
    run_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ExecutionList:
    workspace, _ = await _workspace_and_draft(session, principal)
    await _run_in_workspace(session, workspace["id"], run_id)
    result = await session.execute(
        text(
            EXECUTION_SELECT
            + " WHERE e.run_id = :run_id AND e.workspace_id = :workspace_id"
            + " ORDER BY e.language, e.attempt_number DESC"
        ),
        {"run_id": run_id, "workspace_id": workspace["id"]},
    )
    views = [await _execution_view(dict(row)) for row in result.mappings().all()]
    await session.commit()
    return ExecutionList(items=views)


@router.get(
    "/executions/{execution_id}",
    operation_id="getExecution",
    response_model=ExecutionView,
)
async def get_execution(
    execution_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> ExecutionView:
    workspace, _ = await _workspace_and_draft(session, principal)
    result = await session.execute(
        text(
            EXECUTION_SELECT
            + " WHERE e.id = :execution_id AND e.workspace_id = :workspace_id"
        ),
        {"execution_id": execution_id, "workspace_id": workspace["id"]},
    )
    row = result.mappings().one_or_none()
    if row is None:
        raise _not_found()
    view = await _execution_view(dict(row))
    await session.commit()
    return view


FINDING_SELECT = """
SELECT f.id, f.run_id, f.capability_id, f.source_surface, f.static_state,
       f.lifecycle_state, f.expected_value, f.observed_value, f.summary,
       f.created_at, f.evidence_artifact_id, f.source_path, f.source_locator,
       f.source_excerpt, a.object_key, a.sha256, a.byte_length
FROM findings f
JOIN artifacts a ON a.id = f.evidence_artifact_id
                AND a.workspace_id = f.workspace_id
"""


async def _finding_view(row: dict[str, Any]) -> FindingView:
    try:
        body = await asyncio.to_thread(
            _artifact_reader().read,
            ArtifactRecord(
                object_key=row["object_key"],
                sha256=row["sha256"],
                byte_length=row["byte_length"],
            ),
        )
        if row["source_excerpt"] not in body.decode("utf-8"):
            raise ArtifactUnavailable("finding excerpt does not match source")
    except (ArtifactUnavailable, UnicodeDecodeError):
        raise HTTPException(
            status_code=409, detail="finding evidence unavailable"
        ) from None
    evidence = FindingEvidenceView(
        artifact_id=row["evidence_artifact_id"],
        path=row["source_path"],
        sha256=row["sha256"],
        locator=row["source_locator"],
        excerpt=row["source_excerpt"],
    )
    excluded = {
        "evidence_artifact_id",
        "source_path",
        "source_locator",
        "source_excerpt",
        "object_key",
        "sha256",
        "byte_length",
    }
    return FindingView(
        **{key: value for key, value in row.items() if key not in excluded},
        evidence=evidence,
    )


@router.get(
    "/runs/{run_id}/findings",
    operation_id="listRunFindings",
    response_model=FindingList,
)
async def list_findings(
    run_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> FindingList:
    workspace, _ = await _workspace_and_draft(session, principal)
    await _run_in_workspace(session, workspace["id"], run_id)
    result = await session.execute(
        text(
            FINDING_SELECT
            + " WHERE f.run_id = :run_id AND f.workspace_id = :workspace_id"
            + " ORDER BY f.capability_id, f.source_surface"
        ),
        {"run_id": run_id, "workspace_id": workspace["id"]},
    )
    views = [await _finding_view(dict(row)) for row in result.mappings().all()]
    await session.commit()
    return FindingList(items=views)


@router.get(
    "/findings/{finding_id}",
    operation_id="getFinding",
    response_model=FindingView,
)
async def get_finding(
    finding_id: UUID,
    principal: Annotated[Principal, Depends(current_principal)],
    session: Annotated[AsyncSession, Depends(session_dependency)],
) -> FindingView:
    workspace, _ = await _workspace_and_draft(session, principal)
    result = await session.execute(
        text(
            FINDING_SELECT
            + " WHERE f.id = :finding_id AND f.workspace_id = :workspace_id"
        ),
        {"finding_id": finding_id, "workspace_id": workspace["id"]},
    )
    row = result.mappings().one_or_none()
    if row is None:
        raise _not_found()
    view = await _finding_view(dict(row))
    await session.commit()
    return view
