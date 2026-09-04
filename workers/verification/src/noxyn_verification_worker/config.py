"""Environment-backed worker configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

DEFAULT_DATABASE_URL = (
    "postgresql://noxyn:noxyn-local-only@127.0.0.1:55432/noxyn_solari"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    heartbeat_seconds: float
    poll_seconds: float
    lease_seconds: int
    artifact_root: Path
    repository_root: Path
    manifest_path: Path
    executor_mode: Literal["replay", "live"]
    solari_api_key: str | None
    solari_api_base_url: str


def load_settings() -> Settings:
    interval = float(os.getenv("NOXYN_WORKER_HEARTBEAT_SECONDS", "10"))
    poll_interval = float(os.getenv("NOXYN_WORKER_POLL_SECONDS", "1"))
    lease_seconds = int(os.getenv("NOXYN_WORKER_LEASE_SECONDS", "30"))
    if interval <= 0:
        raise ValueError("NOXYN_WORKER_HEARTBEAT_SECONDS must be positive")
    if poll_interval <= 0:
        raise ValueError("NOXYN_WORKER_POLL_SECONDS must be positive")
    if lease_seconds <= 0:
        raise ValueError("NOXYN_WORKER_LEASE_SECONDS must be positive")
    executor_mode = os.getenv("NOXYN_EXECUTOR_MODE", "replay")
    if executor_mode not in {"replay", "live"}:
        raise ValueError("NOXYN_EXECUTOR_MODE must be replay or live")
    solari_api_key = os.getenv("SOLARI_API_KEY")
    if executor_mode == "live" and not solari_api_key:
        raise ValueError("SOLARI_API_KEY is required when NOXYN_EXECUTOR_MODE=live")
    return Settings(
        database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        heartbeat_seconds=interval,
        poll_seconds=poll_interval,
        lease_seconds=lease_seconds,
        artifact_root=Path(
            os.getenv("NOXYN_ARTIFACT_ROOT", str(Path.cwd() / ".artifacts" / "noxyn"))
        ).resolve(),
        repository_root=REPOSITORY_ROOT,
        manifest_path=REPOSITORY_ROOT
        / "noxyn_solari"
        / "manifests"
        / "sandbox-create-evolution.v5.json",
        executor_mode=cast(Literal["replay", "live"], executor_mode),
        solari_api_key=solari_api_key,
        solari_api_base_url=os.getenv(
            "SOLARI_API_BASE_URL", "https://api.getsolari.com"
        ),
    )
