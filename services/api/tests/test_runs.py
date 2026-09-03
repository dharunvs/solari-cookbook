import asyncio
from pathlib import Path
from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient
from noxyn_api.main import create_app
from noxyn_verification_worker.artifacts import LocalArtifactStore
from noxyn_verification_worker.config import DEFAULT_DATABASE_URL
from noxyn_verification_worker.queue import JobLease, PostgresJobQueue

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _headers(subject: str, key: str | None = None) -> dict[str, str]:
    headers = {"X-Noxyn-Test-User": subject}
    if key:
        headers.update({"Idempotency-Key": key, "X-CSRF-Token": "same-origin"})
    return headers


def _configured_product(client: TestClient, subject: str) -> str:
    project = client.post(
        "/v1/projects",
        headers={**_headers(subject), "Idempotency-Key": "project"},
        json={"name": "Solari", "slug": "solari"},
    ).json()
    product = client.post(
        f"/v1/projects/{project['id']}/products",
        headers={**_headers(subject), "Idempotency-Key": "product"},
        json={"slug": "sandbox"},
    ).json()
    client.post(
        f"/v1/products/{product['id']}/configurations",
        headers={**_headers(subject), "Idempotency-Key": "configuration"},
        json={
            "sources": ["cookbook-examples"],
            "packages": [
                {
                    "ecosystem": "python",
                    "package": "solari-sandbox",
                    "version": "0.2.0",
                }
            ],
        },
    )
    return str(product["id"])


def test_run_is_idempotent_pollable_and_cancellable(monkeypatch: object) -> None:
    monkeypatch.setenv("NOXYN_E2E_AUTH_BYPASS", "true")  # type: ignore[attr-defined]
    subject = f"e2e_{uuid4().hex}"
    with TestClient(create_app()) as client:
        product_id = _configured_product(client, subject)
        first = client.post(
            f"/v1/products/{product_id}/runs",
            headers=_headers(subject, "run-1"),
            json={"scenario": "controlled_api_evolution"},
        )
        replay = client.post(
            f"/v1/products/{product_id}/runs",
            headers=_headers(subject, "run-1"),
            json={"scenario": "controlled_api_evolution"},
        )
        assert first.status_code == 202
        assert replay.status_code == 200
        assert replay.json()["id"] == first.json()["id"]

        listed = client.get(
            f"/v1/products/{product_id}/runs", headers=_headers(subject)
        )
        assert listed.json()["items"][0]["id"] == first.json()["id"]
        cancelled = client.post(
            f"/v1/runs/{first.json()['id']}/cancel",
            headers=_headers(subject, "cancel-1"),
        )
        assert cancelled.status_code == 200
        assert cancelled.json()["state"] == "CANCELLED"
        assert cancelled.json()["completed_at"] is not None


def test_leased_run_cancellation_waits_for_worker_cleanup(
    monkeypatch: object, tmp_path: Path
) -> None:
    monkeypatch.setenv("NOXYN_E2E_AUTH_BYPASS", "true")  # type: ignore[attr-defined]
    subject = f"e2e_{uuid4().hex}"
    with TestClient(create_app()) as client:
        product_id = _configured_product(client, subject)
        run = client.post(
            f"/v1/products/{product_id}/runs",
            headers=_headers(subject, "leased-cancel-run"),
            json={"scenario": "controlled_api_evolution"},
        ).json()

        async def claim() -> tuple[PostgresJobQueue, JobLease]:
            queue = PostgresJobQueue(DEFAULT_DATABASE_URL, lease_seconds=30)
            for _ in range(30):
                lease = await queue.claim("cancel-test-worker")
                assert lease is not None
                if str(lease.run_id) == run["id"]:
                    return queue, lease
                await queue.execute(lease, LocalArtifactStore(tmp_path))
            raise AssertionError("cancel test run was not claimed")

        queue, lease = asyncio.run(claim())
        requested = client.post(
            f"/v1/runs/{run['id']}/cancel",
            headers=_headers(subject, "cancel-leased"),
        )
        assert requested.json()["state"] == "CANCEL_REQUESTED"
        assert requested.json()["completed_at"] is None

        asyncio.run(queue.execute(lease, LocalArtifactStore(tmp_path)))
        cancelled = client.get(
            f"/v1/runs/{run['id']}", headers=_headers(subject)
        ).json()
        assert cancelled["state"] == "CANCELLED"
        assert cancelled["completed_at"] is not None


def test_run_mutations_require_csrf_and_cross_workspace_is_opaque(
    monkeypatch: object,
) -> None:
    monkeypatch.setenv("NOXYN_E2E_AUTH_BYPASS", "true")  # type: ignore[attr-defined]
    owner = f"e2e_{uuid4().hex}"
    outsider = f"e2e_{uuid4().hex}"
    with TestClient(create_app()) as client:
        product_id = _configured_product(client, owner)
        denied = client.post(
            f"/v1/products/{product_id}/runs",
            headers={"X-Noxyn-Test-User": owner, "Idempotency-Key": "no-csrf"},
            json={"scenario": "controlled_api_evolution"},
        )
        assert denied.status_code == 403
        run = client.post(
            f"/v1/products/{product_id}/runs",
            headers=_headers(owner, "private-run"),
            json={"scenario": "controlled_api_evolution"},
        ).json()
        unavailable = client.get(f"/v1/runs/{run['id']}", headers=_headers(outsider))
        assert unavailable.status_code == 404
        assert unavailable.json() == {"detail": "resource unavailable"}


def test_completed_run_exposes_runtime_matrix_findings_and_execution(
    monkeypatch: object,
) -> None:
    monkeypatch.setenv("NOXYN_E2E_AUTH_BYPASS", "true")  # type: ignore[attr-defined]
    owner = f"e2e_{uuid4().hex}"
    outsider = f"e2e_{uuid4().hex}"
    with TestClient(create_app()) as client:
        product_id = _configured_product(client, owner)
        run = client.post(
            f"/v1/products/{product_id}/runs",
            headers=_headers(owner, "analysis-run"),
            json={"scenario": "controlled_api_evolution"},
        ).json()

        async def finish_run() -> None:
            queue = PostgresJobQueue(DEFAULT_DATABASE_URL, lease_seconds=30)
            store = LocalArtifactStore(REPOSITORY_ROOT / ".artifacts" / "noxyn")
            for _ in range(40):
                lease = await queue.claim("api-analysis-test")
                if lease is not None:
                    await queue.execute(lease, store)
                    if str(lease.run_id) == run["id"]:
                        return
                with psycopg.connect(DEFAULT_DATABASE_URL) as connection:
                    state = connection.execute(
                        "SELECT state FROM verification_runs WHERE id = %s",
                        (run["id"],),
                    ).fetchone()
                if state == ("COMPLETED",):
                    return
                await asyncio.sleep(0.05)
            raise AssertionError("analysis run was not claimed")

        asyncio.run(finish_run())
        matrix = client.get(f"/v1/runs/{run['id']}/matrix", headers=_headers(owner))
        assert matrix.status_code == 200
        assert matrix.json()["summary"]["suspected"] == 2
        runtime = matrix.json()["rows"][0]["runtime"]
        assert runtime["state"] == "FAIL"
        assert runtime["backend"] == "REPLAY"
        assert runtime["executionId"]
        runtime_cells = matrix.json()["rows"][0]["runtimeCells"]
        assert [cell["sourceSurface"] for cell in runtime_cells] == [
            "python",
            "docs_python",
            "typescript",
        ]
        assert [cell["state"] for cell in runtime_cells] == [
            "FAIL",
            "FAIL",
            "PASS",
        ]
        assert matrix.json()["parity"] == {
            "state": "DIFFERENT",
            "summary": (
                "Python reproduces the stale parameter while TypeScript "
                "passes with memMb."
            ),
            "comparedLanguages": ["python", "typescript"],
        }

        findings = client.get(
            f"/v1/runs/{run['id']}/findings", headers=_headers(owner)
        ).json()["items"]
        assert {item["source_surface"] for item in findings} == {
            "python",
            "docs_python",
        }
        python_finding = next(
            item for item in findings if item["source_surface"] == "python"
        )
        assert python_finding["lifecycle_state"] == "REPRODUCED"
        assert all(item["lifecycle_state"] == "REPRODUCED" for item in findings)
        detail = client.get(
            f"/v1/findings/{findings[0]['id']}", headers=_headers(owner)
        )
        assert detail.status_code == 200
        assert len(detail.json()["evidence"]["sha256"]) == 64

        executions = client.get(
            f"/v1/runs/{run['id']}/executions", headers=_headers(owner)
        ).json()["items"]
        assert len(executions) == 3
        execution = next(
            item for item in executions if item["source_surface"] == "python"
        )
        assert execution["infrastructure_state"] == "PASS"
        assert execution["subject_state"] == "FAIL"
        assert execution["exit_code"] == 1
        assert execution["cleanup_state"] == "PASS"
        assert "unexpected keyword argument 'memory'" in execution["stderr"]
        assert len(execution["source_sha256"]) == 64
        assert len(execution["evidence"]["sha256"]) == 64
        typescript = next(
            item for item in executions if item["source_surface"] == "typescript"
        )
        assert typescript["finding_id"] is None
        assert typescript["infrastructure_state"] == "PASS"
        assert typescript["subject_state"] == "PASS"
        assert typescript["exit_code"] == 0
        assert typescript["package_name"] == "@solarisdk/sandbox"
        execution_detail = client.get(
            f"/v1/executions/{execution['id']}", headers=_headers(owner)
        )
        assert execution_detail.status_code == 200

        unavailable_matrix = client.get(
            f"/v1/runs/{run['id']}/matrix", headers=_headers(outsider)
        )
        unavailable_finding = client.get(
            f"/v1/findings/{findings[0]['id']}", headers=_headers(outsider)
        )
        unavailable_execution = client.get(
            f"/v1/executions/{execution['id']}", headers=_headers(outsider)
        )
        assert unavailable_matrix.status_code == 404
        assert unavailable_finding.status_code == 404
        assert unavailable_execution.status_code == 404

        proposals = []
        for finding in findings:
            created = client.post(
                f"/v1/findings/{finding['id']}/proposals",
                headers=_headers(owner, f"proposal-{finding['id']}"),
            )
            assert created.status_code == 201
            proposal = created.json()
            assert proposal["state"] == "FIX_PROPOSED"
            assert proposal["checkout_modified"] is False
            assert "memory=2048" in proposal["patch"]
            assert "mem_mb=2048" in proposal["patch"]
            replayed = client.post(
                f"/v1/findings/{finding['id']}/proposals",
                headers=_headers(owner, f"proposal-replay-{finding['id']}"),
            )
            assert replayed.status_code == 200
            assert replayed.json()["id"] == proposal["id"]
            queued = client.post(
                f"/v1/proposals/{proposal['id']}/verify",
                headers=_headers(owner, f"verify-{proposal['id']}"),
            )
            assert queued.status_code == 202
            proposals.append(proposal)

        async def verify_proposals() -> None:
            queue = PostgresJobQueue(DEFAULT_DATABASE_URL, lease_seconds=30)
            store = LocalArtifactStore(REPOSITORY_ROOT / ".artifacts" / "noxyn")
            pending = {item["id"] for item in proposals}
            for _ in range(20):
                lease = await queue.claim("api-proposal-test")
                if lease is None:
                    await asyncio.sleep(0.02)
                    continue
                await queue.execute(lease, store)
                if lease.proposal_id is not None:
                    pending.discard(str(lease.proposal_id))
                if not pending:
                    return
            raise AssertionError("proposal verification jobs were not completed")

        asyncio.run(verify_proposals())
        listed_proposals = client.get(
            f"/v1/runs/{run['id']}/proposals", headers=_headers(owner)
        ).json()["items"]
        assert len(listed_proposals) == 2
        assert all(item["state"] == "FIX_VERIFIED" for item in listed_proposals)
        assert all(
            item["verification"]["phase"] == "FIX_VERIFY" for item in listed_proposals
        )
        assert all(
            item["verification"]["subject_state"] == "PASS" for item in listed_proposals
        )
        unavailable_proposal = client.get(
            f"/v1/proposals/{proposals[0]['id']}", headers=_headers(outsider)
        )
        assert unavailable_proposal.status_code == 404
