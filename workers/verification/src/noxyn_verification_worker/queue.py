"""PostgreSQL job leasing and controlled static-analysis orchestration."""
# ruff: noqa: E501

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import psycopg
from psycopg.rows import dict_row

from noxyn_verification_worker.artifacts import ArtifactReference, LocalArtifactStore
from noxyn_verification_worker.executor import (
    ExecutionRequest,
    ExecutionResult,
    Language,
    ReplayVerificationExecutor,
    VerificationExecutor,
)
from noxyn_verification_worker.static_analysis import (
    build_matrix,
    canonical_json,
    extract_python_fence,
    load_manifest,
    snapshot_sources,
    suspected_cells,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class JobLease:
    id: UUID
    workspace_id: UUID
    run_id: UUID
    kind: str
    proposal_id: UUID | None
    attempt: int
    lease_owner: str
    lease_expires_at: datetime


class PostgresJobQueue:
    def __init__(
        self,
        database_url: str,
        *,
        lease_seconds: int,
        repository_root: Path | None = None,
        manifest_path: Path | None = None,
        executor: VerificationExecutor | None = None,
    ) -> None:
        self.database_url = database_url
        self.lease_seconds = lease_seconds
        self.repository_root = repository_root or Path(__file__).resolve().parents[4]
        self.manifest_path = manifest_path or (
            self.repository_root
            / "noxyn_solari"
            / "manifests"
            / "sandbox-create-evolution.v5.json"
        )
        self.executor = executor or ReplayVerificationExecutor()

    async def claim(self, worker_id: str) -> JobLease | None:
        async with await psycopg.AsyncConnection.connect(
            self.database_url, row_factory=dict_row
        ) as connection:
            await connection.execute(
                """
                WITH exhausted AS (
                    UPDATE verification_jobs
                    SET state = 'FAILED', error_code = 'LEASE_ATTEMPTS_EXHAUSTED',
                        lease_owner = NULL, lease_expires_at = NULL, updated_at = now()
                    WHERE state = 'LEASED' AND lease_expires_at <= now()
                      AND attempt >= max_attempts
                    RETURNING run_id, kind
                )
                UPDATE verification_runs
                SET state = 'FAILED', error_code = 'LEASE_ATTEMPTS_EXHAUSTED',
                    completed_at = now()
                WHERE id IN (SELECT run_id FROM exhausted WHERE kind = 'STATIC_ANALYSIS')
                  AND state NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')
                """
            )
            result = await connection.execute(
                """
                WITH candidate AS (
                    SELECT id FROM verification_jobs
                    WHERE attempt < max_attempts
                      AND available_at <= now()
                      AND (state = 'QUEUED' OR (state = 'LEASED' AND lease_expires_at <= now()))
                    ORDER BY available_at, created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE verification_jobs AS job
                SET state = 'LEASED', attempt = attempt + 1, lease_owner = %s,
                    lease_expires_at = now() + (%s * interval '1 second'), updated_at = now()
                FROM candidate
                WHERE job.id = candidate.id
                RETURNING job.id, job.workspace_id, job.run_id, job.kind,
                          job.proposal_id, job.attempt,
                          job.lease_owner, job.lease_expires_at
                """,
                (worker_id, self.lease_seconds),
            )
            row = await result.fetchone()
            await connection.commit()
        return JobLease(**row) if row else None

    async def execute(self, lease: JobLease, store: LocalArtifactStore) -> None:
        if lease.kind == "FIX_VERIFICATION":
            await self._execute_fix_verification(lease, store)
            return
        if lease.kind != "STATIC_ANALYSIS":
            raise RuntimeError("unsupported verification job kind")
        await self._execute_analysis(lease, store)

    async def _execute_analysis(
        self, lease: JobLease, store: LocalArtifactStore
    ) -> None:
        if not await self._begin_snapshot(lease):
            if await self._cancel_requested(lease):
                await self._finish_cancelled(lease)
            return
        manifest, manifest_body = await asyncio.to_thread(
            load_manifest, self.repository_root, self.manifest_path
        )
        snapshots = await asyncio.to_thread(
            snapshot_sources, self.repository_root, manifest
        )
        manifest_reference = await asyncio.to_thread(
            store.put,
            workspace_id=lease.workspace_id,
            run_id=lease.run_id,
            kind="source-manifest",
            body=manifest_body,
        )
        await asyncio.to_thread(store.read, manifest_reference)
        await self._record_artifact(lease, manifest_reference, "SOURCE_MANIFEST")

        source_artifacts: dict[str, UUID] = {}
        for snapshot in snapshots:
            reference = await asyncio.to_thread(
                store.put,
                workspace_id=lease.workspace_id,
                run_id=lease.run_id,
                kind=f"source-{snapshot.surface.replace('_', '-')}",
                body=snapshot.body,
            )
            await asyncio.to_thread(store.read, reference)
            source_artifacts[snapshot.surface] = await self._record_artifact(
                lease, reference, "SOURCE_SNAPSHOT"
            )

        if not await self._begin_analysis(lease):
            if await self._cancel_requested(lease):
                await self._finish_cancelled(lease)
            return
        matrix = await asyncio.to_thread(
            build_matrix, manifest, manifest_body, snapshots
        )
        finding_records: list[tuple[UUID, dict[str, object], UUID]] = []
        for cell in suspected_cells(matrix):
            finding_id = uuid5(
                NAMESPACE_URL,
                f"noxyn:{lease.run_id}:sandbox.create.memory_mb:{cell['surface']}",
            )
            cell["findingId"] = str(finding_id)
            source_evidence_id = source_artifacts[str(cell["surface"])]
            finding_records.append((finding_id, cell, source_evidence_id))
        matrix_body = canonical_json(matrix)
        matrix_reference = await asyncio.to_thread(
            store.put,
            workspace_id=lease.workspace_id,
            run_id=lease.run_id,
            kind="capability-matrix",
            body=matrix_body,
        )
        await asyncio.to_thread(store.read, matrix_reference)
        await self._record_artifact(lease, matrix_reference, "CAPABILITY_MATRIX")
        await self._record_findings(lease, finding_records)
        if not await self._begin_verification(lease):
            if await self._cancel_requested(lease):
                await self._finish_cancelled(lease)
            return

        last_evidence_artifact_id: UUID | None = None
        for execution_key in ("python", "docs_python", "typescript", "go"):
            execution_config = manifest["execution"][execution_key]
            language = cast(Language, str(execution_config["language"]))
            surface = str(execution_config["sourceSurface"])
            snapshot = next(item for item in snapshots if item.surface == surface)
            execution_source = (
                extract_python_fence(snapshot.body)
                if surface == "docs_python"
                else snapshot.body
            )
            execution_source_artifact_id = source_artifacts[surface]
            if execution_source != snapshot.body:
                source_reference = await asyncio.to_thread(
                    store.put,
                    workspace_id=lease.workspace_id,
                    run_id=lease.run_id,
                    kind=f"execution-source-{surface.replace('_', '-')}",
                    body=execution_source,
                )
                execution_source_artifact_id = await self._record_artifact(
                    lease, source_reference, "EXECUTION_SOURCE"
                )
            finding = next(
                (
                    record
                    for record in finding_records
                    if record[1]["surface"] == surface
                ),
                None,
            )
            replay_path = (
                self.repository_root / str(execution_config["replay"])
            ).resolve()
            if self.repository_root.resolve() not in replay_path.parents:
                raise ValueError("execution replay escapes repository root")
            request = ExecutionRequest(
                language=language,
                source_surface=surface,
                phase="VERIFY",
                package_name=str(manifest["packages"][language]["name"]),
                package_version=str(manifest["packages"][language]["version"]),
                source_path=snapshot.path,
                source=execution_source,
                source_sha256=hashlib.sha256(execution_source).hexdigest(),
                timeout_seconds=int(execution_config["timeoutSeconds"]),
                max_output_bytes=int(execution_config["maxOutputBytes"]),
                replay_path=replay_path,
            )
            execution: ExecutionResult | None = None
            for infrastructure_attempt in range(1, 3):
                execution = await self.executor.execute(
                    request, lambda: self._should_stop(lease)
                )
                evidence_reference = await asyncio.to_thread(
                    store.put,
                    workspace_id=lease.workspace_id,
                    run_id=lease.run_id,
                    kind=f"{language}-execution-evidence",
                    body=execution.evidence(),
                )
                await asyncio.to_thread(store.read, evidence_reference)
                last_evidence_artifact_id = await self._record_artifact(
                    lease, evidence_reference, "EXECUTION_EVIDENCE"
                )
                attempt_number = (lease.attempt - 1) * 2 + infrastructure_attempt
                await self._record_execution(
                    lease,
                    finding_id=finding[0] if finding else None,
                    source_artifact_id=execution_source_artifact_id,
                    evidence_artifact_id=last_evidence_artifact_id,
                    attempt_number=attempt_number,
                    source_surface=surface,
                    proposal_id=None,
                    result=execution,
                )
                if execution.cancelled or execution.infrastructure_state == "PASS":
                    break
            if execution is None or last_evidence_artifact_id is None:
                raise RuntimeError("verification produced no execution evidence")
            if execution.cancelled or await self._cancel_requested(lease):
                await self._finish_cancelled(lease, last_evidence_artifact_id)
                return
        if last_evidence_artifact_id is None:
            raise RuntimeError("verification produced no execution evidence")
        await self._finish(lease, last_evidence_artifact_id, manifest_reference.sha256)

    async def _execute_fix_verification(
        self, lease: JobLease, store: LocalArtifactStore
    ) -> None:
        if lease.proposal_id is None:
            raise RuntimeError("fix verification job has no proposal")
        async with await psycopg.AsyncConnection.connect(
            self.database_url, row_factory=dict_row
        ) as connection:
            result = await connection.execute(
                """
                SELECT p.finding_id, p.source_sha256, p.proposed_sha256,
                       f.source_surface, f.source_path,
                       original.object_key AS original_key,
                       original.sha256 AS original_sha, original.byte_length AS original_length,
                       proposed.id AS proposed_artifact_id,
                       proposed.object_key AS proposed_key,
                       proposed.sha256 AS proposed_sha, proposed.byte_length AS proposed_length
                FROM proposals p
                JOIN findings f ON f.id = p.finding_id AND f.workspace_id = p.workspace_id
                JOIN artifacts original ON original.id = p.source_artifact_id
                  AND original.workspace_id = p.workspace_id
                JOIN artifacts proposed ON proposed.id = p.proposed_artifact_id
                  AND proposed.workspace_id = p.workspace_id
                WHERE p.id = %s AND p.workspace_id = %s AND p.run_id = %s
                  AND p.state = 'FIX_PROPOSED'
                """,
                (lease.proposal_id, lease.workspace_id, lease.run_id),
            )
            proposal = await result.fetchone()
        if proposal is None:
            await self._complete_fix_job(lease, verified=False)
            return
        original = ArtifactReference(
            proposal["original_key"],
            proposal["original_sha"],
            proposal["original_length"],
        )
        proposed = ArtifactReference(
            proposal["proposed_key"],
            proposal["proposed_sha"],
            proposal["proposed_length"],
        )
        await asyncio.to_thread(store.read, original)
        proposed_body = await asyncio.to_thread(store.read, proposed)
        if (
            original.sha256 != proposal["source_sha256"]
            or proposed.sha256 != proposal["proposed_sha256"]
            or hashlib.sha256(proposed_body).hexdigest() != proposal["proposed_sha256"]
        ):
            raise RuntimeError("proposal source binding changed")

        manifest, _ = await asyncio.to_thread(
            load_manifest, self.repository_root, self.manifest_path
        )
        surface = str(proposal["source_surface"])
        execution_config = manifest["execution"][surface]
        language = cast(Language, str(execution_config["language"]))
        execution_source = (
            extract_python_fence(proposed_body)
            if surface == "docs_python"
            else proposed_body
        )
        source_artifact_id = UUID(str(proposal["proposed_artifact_id"]))
        if execution_source != proposed_body:
            reference = await asyncio.to_thread(
                store.put,
                workspace_id=lease.workspace_id,
                run_id=lease.run_id,
                kind=f"fix-execution-source-{surface.replace('_', '-')}",
                body=execution_source,
            )
            source_artifact_id = await self._record_artifact(
                lease, reference, "FIX_EXECUTION_SOURCE"
            )
        replay_path = (
            self.repository_root / str(execution_config["fixReplay"])
        ).resolve()
        if self.repository_root.resolve() not in replay_path.parents:
            raise ValueError("fix replay escapes repository root")
        request = ExecutionRequest(
            language=language,
            source_surface=surface,
            phase="FIX_VERIFY",
            package_name=str(manifest["packages"][language]["name"]),
            package_version=str(manifest["packages"][language]["version"]),
            source_path=str(proposal["source_path"]),
            source=execution_source,
            source_sha256=hashlib.sha256(execution_source).hexdigest(),
            timeout_seconds=int(execution_config["timeoutSeconds"]),
            max_output_bytes=int(execution_config["maxOutputBytes"]),
            replay_path=replay_path,
        )
        execution: ExecutionResult | None = None
        for infrastructure_attempt in range(1, 3):
            execution = await self.executor.execute(
                request, lambda: self._should_stop(lease)
            )
            reference = await asyncio.to_thread(
                store.put,
                workspace_id=lease.workspace_id,
                run_id=lease.run_id,
                kind=f"fix-{surface.replace('_', '-')}-execution-evidence",
                body=execution.evidence(),
            )
            evidence_id = await self._record_artifact(
                lease, reference, "FIX_EXECUTION_EVIDENCE"
            )
            attempt_number = (lease.attempt - 1) * 2 + infrastructure_attempt
            await self._record_execution(
                lease,
                finding_id=UUID(str(proposal["finding_id"])),
                proposal_id=lease.proposal_id,
                source_surface=surface,
                source_artifact_id=source_artifact_id,
                evidence_artifact_id=evidence_id,
                attempt_number=attempt_number,
                result=execution,
            )
            if execution.cancelled or execution.infrastructure_state == "PASS":
                break
        if execution is None:
            raise RuntimeError("fix verification produced no evidence")
        verified = (
            execution.infrastructure_state == "PASS"
            and execution.subject_state == "PASS"
            and execution.cleanup_state == "PASS"
        )
        await self._complete_fix_job(lease, verified=verified)

    async def _complete_fix_job(self, lease: JobLease, *, verified: bool) -> None:
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            async with connection.transaction():
                changed = await connection.execute(
                    """
                    UPDATE verification_jobs SET state = 'COMPLETED', lease_owner = NULL,
                        lease_expires_at = NULL, updated_at = now()
                    WHERE id = %s AND state = 'LEASED' AND lease_owner = %s
                    """,
                    (lease.id, lease.lease_owner),
                )
                if not changed.rowcount or not verified or lease.proposal_id is None:
                    return
                result = await connection.execute(
                    """
                    UPDATE proposals SET state = 'FIX_VERIFIED', verified_at = now()
                    WHERE id = %s AND workspace_id = %s AND state = 'FIX_PROPOSED'
                    RETURNING finding_id
                    """,
                    (lease.proposal_id, lease.workspace_id),
                )
                row = await result.fetchone()
                if row:
                    await connection.execute(
                        """
                        UPDATE findings SET lifecycle_state = 'FIX_VERIFIED'
                        WHERE id = %s AND workspace_id = %s
                        """,
                        (row[0], lease.workspace_id),
                    )

    async def fail(
        self, lease: JobLease, error_code: str = "STATIC_ANALYSIS_FAILED"
    ) -> None:
        if await self._cancel_requested(lease):
            await self._finish_cancelled(lease)
            return
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            async with connection.transaction():
                changed = await connection.execute(
                    """
                    UPDATE verification_jobs SET state = 'FAILED', error_code = %s,
                        lease_owner = NULL, lease_expires_at = NULL, updated_at = now()
                    WHERE id = %s AND state = 'LEASED' AND lease_owner = %s
                    """,
                    (error_code, lease.id, lease.lease_owner),
                )
                if changed.rowcount and lease.kind == "STATIC_ANALYSIS":
                    await connection.execute(
                        """
                        UPDATE verification_runs SET state = 'FAILED', error_code = %s,
                            completed_at = now()
                        WHERE id = %s AND state NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')
                        """,
                        (error_code, lease.run_id),
                    )

    async def _begin_snapshot(self, lease: JobLease) -> bool:
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            result = await connection.execute(
                """
                UPDATE verification_runs SET state = 'SNAPSHOTTING',
                    started_at = COALESCE(started_at, now())
                WHERE id = %s AND workspace_id = %s
                  AND state NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')
                  AND cancel_requested_at IS NULL
                  AND EXISTS (
                    SELECT 1 FROM verification_jobs WHERE id = %s
                      AND state = 'LEASED' AND lease_owner = %s
                  )
                """,
                (lease.run_id, lease.workspace_id, lease.id, lease.lease_owner),
            )
            await connection.commit()
            return result.rowcount == 1

    async def _record_artifact(
        self, lease: JobLease, reference: ArtifactReference, kind: str
    ) -> UUID:
        artifact_id = uuid4()
        async with await psycopg.AsyncConnection.connect(
            self.database_url, row_factory=dict_row
        ) as connection:
            result = await connection.execute(
                """
                INSERT INTO artifacts (id, workspace_id, run_id, kind, object_key, sha256, byte_length)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (object_key) DO NOTHING
                RETURNING id
                """,
                (
                    artifact_id,
                    lease.workspace_id,
                    lease.run_id,
                    kind,
                    reference.object_key,
                    reference.sha256,
                    reference.byte_length,
                ),
            )
            row = await result.fetchone()
            if row is None:
                result = await connection.execute(
                    """
                    SELECT id, sha256, byte_length FROM artifacts
                    WHERE object_key = %s AND workspace_id = %s AND run_id = %s
                    """,
                    (reference.object_key, lease.workspace_id, lease.run_id),
                )
                row = await result.fetchone()
                if (
                    row is None
                    or row["sha256"] != reference.sha256
                    or row["byte_length"] != reference.byte_length
                ):
                    raise RuntimeError("artifact metadata conflict")
            await connection.commit()
            return UUID(str(row["id"]))

    async def _begin_analysis(self, lease: JobLease) -> bool:
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            result = await connection.execute(
                """
                UPDATE verification_runs SET state = 'ANALYZING'
                WHERE id = %s AND workspace_id = %s AND state = 'SNAPSHOTTING'
                  AND EXISTS (
                    SELECT 1 FROM verification_jobs WHERE id = %s
                      AND state = 'LEASED' AND lease_owner = %s
                  )
                """,
                (lease.run_id, lease.workspace_id, lease.id, lease.lease_owner),
            )
            await connection.commit()
            return result.rowcount == 1

    async def _begin_verification(self, lease: JobLease) -> bool:
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            result = await connection.execute(
                """
                UPDATE verification_runs SET state = 'VERIFYING'
                WHERE id = %s AND workspace_id = %s AND state = 'ANALYZING'
                  AND EXISTS (
                    SELECT 1 FROM verification_jobs WHERE id = %s
                      AND state = 'LEASED' AND lease_owner = %s
                  )
                """,
                (lease.run_id, lease.workspace_id, lease.id, lease.lease_owner),
            )
            await connection.commit()
            return result.rowcount == 1

    async def renew(self, lease: JobLease) -> bool:
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            result = await connection.execute(
                """
                UPDATE verification_jobs
                SET lease_expires_at = now() + (%s * interval '1 second'),
                    updated_at = now()
                WHERE id = %s AND state = 'LEASED' AND lease_owner = %s
                """,
                (self.lease_seconds, lease.id, lease.lease_owner),
            )
            await connection.commit()
            return result.rowcount == 1

    async def _should_stop(self, lease: JobLease) -> bool:
        async with await psycopg.AsyncConnection.connect(
            self.database_url, row_factory=dict_row
        ) as connection:
            result = await connection.execute(
                """
                SELECT r.cancel_requested_at IS NOT NULL AS cancelled,
                       j.state = 'LEASED' AND j.lease_owner = %s
                         AND j.lease_expires_at > now() AS owns_lease
                FROM verification_runs r
                JOIN verification_jobs j ON j.run_id = r.id
                WHERE r.id = %s AND r.workspace_id = %s AND j.id = %s
                """,
                (lease.lease_owner, lease.run_id, lease.workspace_id, lease.id),
            )
            row = await result.fetchone()
            return row is None or bool(row["cancelled"]) or not bool(row["owns_lease"])

    async def _cancel_requested(self, lease: JobLease) -> bool:
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            result = await connection.execute(
                "SELECT cancel_requested_at IS NOT NULL FROM verification_runs WHERE id = %s AND workspace_id = %s",
                (lease.run_id, lease.workspace_id),
            )
            row = await result.fetchone()
            return bool(row and row[0])

    async def _record_execution(
        self,
        lease: JobLease,
        *,
        finding_id: UUID | None,
        source_artifact_id: UUID,
        evidence_artifact_id: UUID,
        attempt_number: int,
        source_surface: str,
        proposal_id: UUID | None,
        result: ExecutionResult,
    ) -> None:
        execution_id = uuid5(
            NAMESPACE_URL,
            f"noxyn:{lease.run_id}:{source_surface}:{result.phase}:{proposal_id}:{attempt_number}",
        )
        lifecycle = (
            "REPRODUCED"
            if result.infrastructure_state == "PASS" and result.subject_state == "FAIL"
            else "DISMISSED"
            if result.infrastructure_state == "PASS" and result.subject_state == "PASS"
            else "UNVERIFIED"
        )
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            async with connection.transaction():
                await connection.execute(
                    """
                    INSERT INTO execution_attempts (
                        id, workspace_id, run_id, finding_id, proposal_id,
                        attempt_number, language, source_surface, phase,
                        backend, infrastructure_state,
                        infrastructure_step, subject_state, sandbox_id, package_name,
                        package_version, source_artifact_id, source_sha256,
                        command_sha256, exit_code, output_truncated, cleanup_state,
                        cancelled, error_code, evidence_artifact_id, duration_ms,
                        started_at, completed_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s
                    ) ON CONFLICT DO NOTHING
                    """,
                    (
                        execution_id,
                        lease.workspace_id,
                        lease.run_id,
                        finding_id,
                        proposal_id,
                        attempt_number,
                        result.language,
                        source_surface,
                        result.phase,
                        result.backend,
                        result.infrastructure_state,
                        result.infrastructure_step,
                        result.subject_state,
                        result.sandbox_id,
                        result.package_name,
                        result.package_version,
                        source_artifact_id,
                        result.source_sha256,
                        result.command_sha256,
                        result.exit_code,
                        result.output_truncated,
                        result.cleanup_state,
                        result.cancelled,
                        result.error_code,
                        evidence_artifact_id,
                        result.duration_ms,
                        datetime.fromisoformat(result.started_at),
                        datetime.fromisoformat(result.completed_at),
                    ),
                )
                if finding_id is not None and result.phase == "VERIFY":
                    await connection.execute(
                        """
                        UPDATE findings SET lifecycle_state = %s
                        WHERE id = %s AND workspace_id = %s
                        """,
                        (lifecycle, finding_id, lease.workspace_id),
                    )

    async def _finish_cancelled(
        self, lease: JobLease, artifact_id: UUID | None = None
    ) -> None:
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            async with connection.transaction():
                changed = await connection.execute(
                    """
                    UPDATE verification_jobs SET state = 'CANCELLED', lease_owner = NULL,
                        lease_expires_at = NULL, updated_at = now()
                    WHERE id = %s AND state = 'LEASED' AND lease_owner = %s
                    """,
                    (lease.id, lease.lease_owner),
                )
                if changed.rowcount:
                    await connection.execute(
                        """
                        UPDATE verification_runs SET state = 'CANCELLED',
                            result_artifact_id = COALESCE(%s, result_artifact_id),
                            cancel_requested_at = COALESCE(cancel_requested_at, now()),
                            completed_at = now()
                        WHERE id = %s AND state NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')
                        """,
                        (artifact_id, lease.run_id),
                    )

    async def _record_findings(
        self,
        lease: JobLease,
        records: list[tuple[UUID, dict[str, object], UUID]],
    ) -> None:
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            async with connection.transaction():
                for finding_id, cell, evidence_artifact_id in records:
                    await connection.execute(
                        """
                        INSERT INTO findings (
                            id, workspace_id, run_id, capability_id, source_surface,
                            static_state, lifecycle_state, expected_value, observed_value,
                            summary, source_path, source_locator, source_excerpt,
                            evidence_artifact_id
                        ) VALUES (%s, %s, %s, %s, %s, 'SUSPECTED', 'SUSPECTED',
                                  %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (run_id, capability_id, source_surface) DO NOTHING
                        """,
                        (
                            finding_id,
                            lease.workspace_id,
                            lease.run_id,
                            "sandbox.create.memory_mb",
                            cell["surface"],
                            cell["expected"],
                            cell["observed"],
                            cell["summary"],
                            cell["evidence"]["path"],  # type: ignore[index]
                            cell["evidence"]["locator"],  # type: ignore[index]
                            cell["evidence"]["excerpt"],  # type: ignore[index]
                            evidence_artifact_id,
                        ),
                    )

    async def _finish(
        self, lease: JobLease, artifact_id: UUID, manifest_sha256: str
    ) -> None:
        async with await psycopg.AsyncConnection.connect(
            self.database_url
        ) as connection:
            async with connection.transaction():
                cancellation = await connection.execute(
                    """
                    SELECT cancel_requested_at IS NOT NULL
                    FROM verification_runs WHERE id = %s FOR UPDATE
                    """,
                    (lease.run_id,),
                )
                row = await cancellation.fetchone()
                if row and row[0]:
                    await connection.execute(
                        """
                        UPDATE verification_jobs SET state = 'CANCELLED', lease_owner = NULL,
                            lease_expires_at = NULL, updated_at = now()
                        WHERE id = %s AND state = 'LEASED' AND lease_owner = %s
                        """,
                        (lease.id, lease.lease_owner),
                    )
                    await connection.execute(
                        """
                        UPDATE verification_runs SET state = 'CANCELLED',
                            result_artifact_id = %s, manifest_sha256 = %s,
                            completed_at = now()
                        WHERE id = %s AND state NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')
                        """,
                        (artifact_id, manifest_sha256, lease.run_id),
                    )
                    return
                changed = await connection.execute(
                    """
                    UPDATE verification_jobs SET state = 'COMPLETED', lease_owner = NULL,
                        lease_expires_at = NULL, updated_at = now()
                    WHERE id = %s AND state = 'LEASED' AND lease_owner = %s
                    """,
                    (lease.id, lease.lease_owner),
                )
                if not changed.rowcount:
                    return
                await connection.execute(
                    """
                    UPDATE verification_runs SET state = 'COMPLETED', result_artifact_id = %s,
                        manifest_sha256 = %s,
                        completed_at = now()
                    WHERE id = %s AND state NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')
                    """,
                    (artifact_id, manifest_sha256, lease.run_id),
                )


async def run_job_loop(
    queue: PostgresJobQueue,
    store: LocalArtifactStore,
    *,
    worker_id: str,
    poll_seconds: float,
    once: bool = False,
    stop_event: asyncio.Event | None = None,
) -> None:
    stop = stop_event or asyncio.Event()
    while not stop.is_set():
        lease = await queue.claim(worker_id)
        if lease is not None:
            renewal_stop = asyncio.Event()
            renewal_task = asyncio.create_task(
                _renew_lease_loop(queue, lease, renewal_stop)
            )
            try:
                await queue.execute(lease, store)
            except Exception:
                logger.exception(
                    "verification job failed",
                    extra={"job_id": str(lease.id), "run_id": str(lease.run_id)},
                )
                await queue.fail(lease)
            finally:
                renewal_stop.set()
                await renewal_task
        if once:
            return
        try:
            await asyncio.wait_for(stop.wait(), timeout=poll_seconds)
        except TimeoutError:
            continue


async def _renew_lease_loop(
    queue: PostgresJobQueue, lease: JobLease, stop: asyncio.Event
) -> None:
    interval = max(0.25, queue.lease_seconds / 3)
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except TimeoutError:
            try:
                if not await queue.renew(lease):
                    return
            except Exception:
                logger.exception(
                    "verification lease renewal failed",
                    extra={"job_id": str(lease.id), "run_id": str(lease.run_id)},
                )
                return
