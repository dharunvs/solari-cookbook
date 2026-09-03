import asyncio

from noxyn_verification_worker.heartbeat import run_heartbeat_loop


def test_once_writes_one_heartbeat() -> None:
    observed: list[str] = []

    async def record(worker_id: str) -> None:
        observed.append(worker_id)

    asyncio.run(
        run_heartbeat_loop(
            record,
            worker_id="worker-test",
            interval_seconds=0.01,
            once=True,
        )
    )

    assert observed == ["worker-test"]


def test_stop_event_prevents_a_heartbeat() -> None:
    observed: list[str] = []

    async def record(worker_id: str) -> None:
        observed.append(worker_id)

    stop = asyncio.Event()
    stop.set()
    asyncio.run(
        run_heartbeat_loop(
            record,
            worker_id="worker-test",
            interval_seconds=0.01,
            stop_event=stop,
        )
    )

    assert observed == []
