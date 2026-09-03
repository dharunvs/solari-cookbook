from fastapi.testclient import TestClient
from noxyn_api.main import create_app


async def database_ready() -> bool:
    return True


async def database_unavailable() -> bool:
    return False


def test_health_reports_database_readiness() -> None:
    with TestClient(create_app(database_probe=database_ready)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "noxyn-api",
        "version": "0.1.0",
        "database": "connected",
    }


def test_health_fails_closed_when_database_is_unavailable() -> None:
    with TestClient(create_app(database_probe=database_unavailable)) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}
