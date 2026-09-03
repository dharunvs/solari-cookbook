"""Environment-backed API configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_DATABASE_URL = (
    "postgresql://noxyn:noxyn-local-only@127.0.0.1:55432/noxyn_solari"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]

# Local development accepts a root file and the console's standard Next.js file.
# Deployed services receive the same values from their platform's server-side
# environment.
load_dotenv(REPOSITORY_ROOT / ".env.local")
# Next.js treats this as the console's canonical local environment. Prefer it
# when both files exist so a stale root value cannot replace the active Clerk
# application credentials.
load_dotenv(REPOSITORY_ROOT / "apps" / "console" / ".env.local", override=True)


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    app_env: str
    e2e_auth_bypass: bool
    clerk_secret_key: str | None
    clerk_authorized_parties: tuple[str, ...]
    artifact_root: Path = REPOSITORY_ROOT / ".artifacts" / "noxyn"


def load_settings() -> Settings:
    """Load settings without reading a checked-in secret file."""
    app_env = os.getenv("APP_ENV", "development")
    bypass_requested = os.getenv("NOXYN_E2E_AUTH_BYPASS", "").lower() == "true"
    return Settings(
        database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        app_env=app_env,
        e2e_auth_bypass=bypass_requested and app_env != "production",
        clerk_secret_key=os.getenv("CLERK_SECRET_KEY"),
        clerk_authorized_parties=(
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://[::1]:3000",
        ),
        artifact_root=Path(
            os.getenv(
                "NOXYN_ARTIFACT_ROOT",
                str(REPOSITORY_ROOT / ".artifacts" / "noxyn"),
            )
        ).resolve(),
    )


def sqlalchemy_database_url(url: str) -> str:
    """Normalize a PostgreSQL URL for SQLAlchemy's psycopg 3 dialect."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url
