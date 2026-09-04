# ruff: noqa: E501
import asyncio
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from noxyn_verification_worker.artifacts import LocalArtifactStore
from noxyn_verification_worker.config import DEFAULT_DATABASE_URL
from noxyn_verification_worker.queue import PostgresJobQueue


def _job_fixture() -> tuple[UUID, UUID]:
    workspace_id, project_id, product_id = uuid4(), uuid4(), uuid4()
    configuration_id, run_id, job_id = uuid4(), uuid4(), uuid4()
    with psycopg.connect(DEFAULT_DATABASE_URL) as connection:
        connection.execute(
            "INSERT INTO workspaces (id, owner_clerk_user_id, name) VALUES (%s, %s, 'Lease test')",
            (workspace_id, f"e2e_{uuid4().hex}"),
        )
        connection.execute(
            "INSERT INTO projects (id, workspace_id, name, slug) VALUES (%s, %s, 'Solari', %s)",
            (project_id, workspace_id, f"solari-{uuid4().hex}"),
        )
        connection.execute(
            "INSERT INTO products (id, project_id, slug, name) VALUES (%s, %s, 'sandbox', 'Sandbox')",
            (product_id, project_id),
        )
        connection.execute(
            """
            INSERT INTO product_configurations (id, product_id, version, sources, packages)
            VALUES (%s, %s, 1, '[]'::jsonb, '[]'::jsonb)
            """,
            (configuration_id, product_id),
        )
        connection.execute(
            """
            INSERT INTO verification_runs
                (id, workspace_id, product_id, configuration_id, scenario, state)
            VALUES (%s, %s, %s, %s, 'controlled_api_evolution', 'QUEUED')
            """,
            (run_id, workspace_id, product_id, configuration_id),
        )
        connection.execute(
            """
            INSERT INTO verification_jobs
                (id, workspace_id, run_id, kind, idempotency_key, request_sha256, available_at)
            VALUES (%s, %s, %s, 'STATIC_ANALYSIS', %s, %s, '2000-01-01'::timestamptz)
            """,
            (job_id, workspace_id, run_id, f"lease-{job_id}", "a" * 64),
        )
    return run_id, job_id


@pytest.mark.integration
def test_claim_is_exclusive_and_expired_lease_recovers(tmp_path: Path) -> None:
    run_id, job_id = _job_fixture()
    queue = PostgresJobQueue(DEFAULT_DATABASE_URL, lease_seconds=30)

    async def journey() -> None:
        first, competing = await asyncio.gather(
            queue.claim("worker-one"), queue.claim("worker-two")
        )
        leases = [lease for lease in (first, competing) if lease and lease.id == job_id]
        assert len(leases) == 1
        interrupted = leases[0]
        with psycopg.connect(DEFAULT_DATABASE_URL) as connection:
            connection.execute(
                "UPDATE verification_jobs SET lease_expires_at = now() - interval '1 second' WHERE id = %s",
                (job_id,),
            )
        recovered = await queue.claim("worker-restarted")
        assert recovered is not None
        assert recovered.id == job_id
        assert recovered.attempt == interrupted.attempt + 1
        await queue.execute(recovered, LocalArtifactStore(tmp_path))

    asyncio.run(journey())
    with psycopg.connect(DEFAULT_DATABASE_URL) as connection:
        run = connection.execute(
            """
            SELECT r.state, j.state, j.attempt, count(a.id)
            FROM verification_runs r
            JOIN verification_jobs j ON j.run_id = r.id
            LEFT JOIN artifacts a ON a.run_id = r.id
            WHERE r.id = %s GROUP BY r.state, j.state, j.attempt
            """,
            (run_id,),
        ).fetchone()
    assert run == ("COMPLETED", "COMPLETED", 2, 14)
    with psycopg.connect(DEFAULT_DATABASE_URL) as connection:
        findings = connection.execute(
            "SELECT source_surface, lifecycle_state FROM findings WHERE run_id = %s ORDER BY source_surface",
            (run_id,),
        ).fetchall()
    assert findings == [("docs_python", "REPRODUCED"), ("python", "REPRODUCED")]
    with psycopg.connect(DEFAULT_DATABASE_URL) as connection:
        executions = connection.execute(
            """
            SELECT language, finding_id IS NOT NULL, backend,
                   infrastructure_state, subject_state, exit_code,
                   cleanup_state, source_sha256
            FROM execution_attempts WHERE run_id = %s ORDER BY source_surface
            """,
            (run_id,),
        ).fetchall()
    assert executions == [
        (
            "python",
            True,
            "REPLAY",
            "PASS",
            "FAIL",
            1,
            "PASS",
            "cf6de89fa93053e3967c1a64fccf21b75017723f63a602dc4612a03484c8e066",
        ),
        (
            "go",
            False,
            "REPLAY",
            "PASS",
            "PASS",
            0,
            "PASS",
            "54fbf77c06c0344dc583ab9ad363b6d998b2187c5c17bd4a7ae6c5628fbc700f",
        ),
        (
            "python",
            True,
            "REPLAY",
            "PASS",
            "FAIL",
            1,
            "PASS",
            "d8129181ad58b87239f9f9c19f3a2f21c4fa426075878c26fa37306e6c7a09fb",
        ),
        (
            "typescript",
            False,
            "REPLAY",
            "PASS",
            "PASS",
            0,
            "PASS",
            "c44f01192490598f36ecc593b38d53d7194afc74288f0017850dbba5823d1e88",
        ),
    ]
