"""Durable worker heartbeat implementation."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import psycopg

Heartbeat = Callable[[str], Awaitable[None]]


class PostgresHeartbeat:
    """Write process liveness into PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    async def __call__(self, worker_id: str) -> None:
        async with await psycopg.AsyncConnection.connect(
            self._database_url,
            autocommit=True,
        ) as connection:
            await connection.execute(
                """
                INSERT INTO verification_worker_heartbeats (
                    worker_id,
                    started_at,
                    heartbeat_at
                )
                VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (worker_id) DO UPDATE
                SET heartbeat_at = EXCLUDED.heartbeat_at
                """,
                (worker_id,),
            )


async def run_heartbeat_loop(
    heartbeat: Heartbeat,
    *,
    worker_id: str,
    interval_seconds: float,
    once: bool = False,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Heartbeat once or until a cooperative stop is requested."""
    stop = stop_event or asyncio.Event()
    while not stop.is_set():
        await heartbeat(worker_id)
        if once:
            return
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
        except TimeoutError:
            continue
