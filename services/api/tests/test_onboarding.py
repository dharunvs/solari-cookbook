from uuid import uuid4

from fastapi.testclient import TestClient
from noxyn_api.main import create_app


def _headers(subject: str, key: str = "test-key") -> dict[str, str]:
    return {"X-Noxyn-Test-User": subject, "Idempotency-Key": key}


def test_onboarding_provisions_private_workspace_and_finishes(
    monkeypatch: object,
) -> None:
    monkeypatch.setenv("NOXYN_E2E_AUTH_BYPASS", "true")  # type: ignore[attr-defined]
    subject = f"e2e_{uuid4().hex}"
    with TestClient(create_app()) as client:
        first = client.get("/v1/me", headers=_headers(subject))
        second = client.get("/v1/me", headers=_headers(subject))
        assert first.status_code == 200
        assert first.json()["workspace"]["id"] == second.json()["workspace"]["id"]
        assert first.json()["onboarding"]["current_step"] == "project"

        project = client.post(
            "/v1/projects",
            headers=_headers(subject, "project"),
            json={"name": "Solari", "slug": "solari"},
        )
        assert project.status_code == 201
        project_repeat = client.post(
            "/v1/projects",
            headers=_headers(subject, "project-repeat"),
            json={"name": "Solari", "slug": "solari"},
        )
        assert project_repeat.status_code == 200
        assert project_repeat.json()["id"] == project.json()["id"]

        product = client.post(
            f"/v1/projects/{project.json()['id']}/products",
            headers=_headers(subject, "product"),
            json={"slug": "sandbox"},
        )
        assert product.status_code == 201
        configuration = client.post(
            f"/v1/products/{product.json()['id']}/configurations",
            headers=_headers(subject, "configuration"),
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
        assert configuration.status_code == 201
        assert configuration.json()["version"] == 1
        complete = client.get("/v1/me", headers=_headers(subject))
        assert complete.json()["workspace"]["onboarding_complete"] is True
        assert complete.json()["project_id"] == project.json()["id"]


def test_cross_workspace_project_is_opaque(monkeypatch: object) -> None:
    monkeypatch.setenv("NOXYN_E2E_AUTH_BYPASS", "true")  # type: ignore[attr-defined]
    owner = f"e2e_{uuid4().hex}"
    outsider = f"e2e_{uuid4().hex}"
    with TestClient(create_app()) as client:
        project = client.post(
            "/v1/projects",
            headers=_headers(owner),
            json={"name": "Solari", "slug": "solari"},
        )
        denied = client.get(
            f"/v1/projects/{project.json()['id']}", headers=_headers(outsider)
        )
    assert denied.status_code == 404
    assert denied.json() == {"detail": "resource unavailable"}
