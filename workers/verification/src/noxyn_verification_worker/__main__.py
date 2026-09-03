"""Start the verification worker heartbeat process."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import socket

from noxyn_verification_worker.artifacts import LocalArtifactStore
from noxyn_verification_worker.config import load_settings
from noxyn_verification_worker.executor import (
    ReplayVerificationExecutor,
    SolariSandboxExecutor,
)
from noxyn_verification_worker.heartbeat import PostgresHeartbeat, run_heartbeat_loop
from noxyn_verification_worker.queue import PostgresJobQueue, run_job_loop


async def async_main(*, once: bool) -> None:
    settings = load_settings()
    worker_id = f"{socket.gethostname()}:{os.getpid()}"
    heartbeat = PostgresHeartbeat(settings.database_url)
    executor = (
        ReplayVerificationExecutor()
        if settings.executor_mode == "replay"
        else SolariSandboxExecutor(
            api_key=settings.solari_api_key or "",
            base_url=settings.solari_api_base_url,
        )
    )
    queue = PostgresJobQueue(
        settings.database_url,
        lease_seconds=settings.lease_seconds,
        repository_root=settings.repository_root,
        manifest_path=settings.manifest_path,
        executor=executor,
    )
    store = LocalArtifactStore(settings.artifact_root)
    logging.info("verification worker starting", extra={"worker_id": worker_id})
    await asyncio.gather(
        run_heartbeat_loop(
            heartbeat,
            worker_id=worker_id,
            interval_seconds=settings.heartbeat_seconds,
            once=once,
        ),
        run_job_loop(
            queue,
            store,
            worker_id=worker_id,
            poll_seconds=settings.poll_seconds,
            once=once,
        ),
    )
    logging.info("verification worker stopped", extra={"worker_id": worker_id})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--once",
        action="store_true",
        help="Write one heartbeat and exit; useful for readiness checks.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(async_main(once=args.once))


if __name__ == "__main__":
    main()
