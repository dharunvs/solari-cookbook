"""Small, fail-closed authentication boundary for Clerk session tokens."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from clerk_backend_api import Clerk
from clerk_backend_api.models import ClerkBaseError
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Header, HTTPException, status

from noxyn_api.config import load_settings

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Principal:
    """The only identity shape available to workspace-scoped routes."""

    subject: str


@dataclass(frozen=True, slots=True)
class _BearerRequest:
    """Minimal request shape accepted by Clerk's backend SDK."""

    headers: Mapping[str, str]


def _authenticate_clerk_session(
    token: str,
    secret_key: str,
    authorized_parties: tuple[str, ...],
) -> dict[str, Any]:
    """Verify one browser-issued token through Clerk's official SDK."""

    if not secret_key.startswith(("sk_test_", "sk_live_")):
        raise PermissionError("Clerk verification is unconfigured")
    try:
        client = Clerk(bearer_auth=secret_key, timeout_ms=5_000)
        state = client.authenticate_request(
            _BearerRequest(headers={"Authorization": f"Bearer {token}"}),
            AuthenticateRequestOptions(
                secret_key=secret_key,
                authorized_parties=list(authorized_parties),
                accepts_token=["session_token"],
            ),
        )
    except (ClerkBaseError, TypeError, ValueError) as error:
        raise PermissionError("Clerk session is unavailable") from error

    payload = state.payload
    if not state.is_signed_in or not isinstance(payload, dict):
        raise PermissionError("Clerk session is unavailable")
    return payload


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
    )


async def current_principal(
    authorization: str | None = Header(default=None),
    test_user: str | None = Header(default=None, alias="X-Noxyn-Test-User"),
) -> Principal:
    """Verify Clerk's signed subject, with a test-only local seam."""

    settings = load_settings()
    if settings.e2e_auth_bypass and test_user and test_user.startswith("e2e_"):
        return Principal(subject=test_user)

    if not authorization:
        LOGGER.warning("Clerk authentication rejected: bearer token missing")
        raise _unauthorized()
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        LOGGER.warning("Clerk authentication rejected: bearer token malformed")
        raise _unauthorized()

    if not settings.clerk_secret_key:
        LOGGER.error("Clerk authentication rejected: verification is unconfigured")
        raise _unauthorized()

    try:
        claims = await asyncio.to_thread(
            _authenticate_clerk_session,
            token,
            settings.clerk_secret_key,
            settings.clerk_authorized_parties,
        )
    except PermissionError:
        # Never log the JWT, its subject, or its claims.
        LOGGER.warning("Clerk authentication rejected: invalid session")
        raise _unauthorized() from None

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise _unauthorized()
    return Principal(subject=subject)
