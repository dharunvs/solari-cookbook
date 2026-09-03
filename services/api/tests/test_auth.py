from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from noxyn_api.auth import _authenticate_clerk_session
from noxyn_api.config import Settings
from noxyn_api.main import create_app


def settings() -> Settings:
    return Settings(
        database_url="postgresql://unused",
        app_env="development",
        e2e_auth_bypass=False,
        clerk_secret_key="sk_test_valid",
        clerk_authorized_parties=(
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ),
    )


def test_official_clerk_sdk_verifies_only_browser_session_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeClerk:
        def __init__(self, **values: Any) -> None:
            captured["constructor"] = values

        def authenticate_request(self, request: Any, options: Any) -> Any:
            captured["headers"] = request.headers
            captured["options"] = options
            return SimpleNamespace(
                is_signed_in=True,
                payload={"sub": "user_clerk", "sid": "session_clerk"},
            )

    monkeypatch.setattr("noxyn_api.auth.Clerk", FakeClerk)

    claims = _authenticate_clerk_session(
        "signed-session",
        "sk_test_valid",
        ("http://localhost:3000", "http://127.0.0.1:3000"),
    )

    assert claims["sub"] == "user_clerk"
    assert captured["headers"] == {"Authorization": "Bearer signed-session"}
    options = captured["options"]
    assert options.accepts_token == ["session_token"]
    assert options.authorized_parties == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_clerk_verification_failure_is_unauthorized_not_a_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(_: str, __: str, ___: tuple[str, ...]) -> dict[str, Any]:
        raise PermissionError("Clerk session is unavailable")

    monkeypatch.setattr("noxyn_api.auth.load_settings", settings)
    monkeypatch.setattr("noxyn_api.auth._authenticate_clerk_session", unavailable)

    with TestClient(create_app()) as client:
        response = client.get("/v1/me", headers={"Authorization": "Bearer token"})

    assert response.status_code == 401
    assert response.json() == {"detail": "authentication required"}
