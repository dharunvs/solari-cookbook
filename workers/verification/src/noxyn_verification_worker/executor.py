"""Bounded, evidence-producing Python and TypeScript verification executors."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Literal, Protocol

InfrastructureState = Literal["PASS", "FAIL"]
SubjectState = Literal["PASS", "FAIL", "NOT_RUN"]
CleanupState = Literal["PASS", "FAIL", "NOT_REQUIRED"]
ExecutorBackend = Literal["REPLAY", "SOLARI"]
ShouldCancel = Callable[[], Awaitable[bool]]
Language = Literal["python", "typescript"]
ExecutionPhase = Literal["VERIFY", "FIX_VERIFY"]


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    language: Language
    source_surface: str
    phase: ExecutionPhase
    package_name: str
    package_version: str
    source_path: str
    source: bytes
    source_sha256: str
    timeout_seconds: int
    max_output_bytes: int
    replay_path: Path


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    schema_version: Literal["noxyn-execution-evidence/1.0"]
    fixture: Literal[True]
    backend: ExecutorBackend
    language: Language
    source_surface: str
    phase: ExecutionPhase
    infrastructure_state: InfrastructureState
    infrastructure_step: str
    subject_state: SubjectState
    sandbox_id: str | None
    package_name: str
    package_version: str
    source_path: str
    source_sha256: str
    command_sha256: str
    exit_code: int | None
    stdout: str
    stderr: str
    output_truncated: bool
    duration_ms: int
    cleanup_state: CleanupState
    cancelled: bool
    error_code: str | None
    started_at: str
    completed_at: str

    def evidence(self) -> bytes:
        return json.dumps(
            _camelize(asdict(self)), sort_keys=True, separators=(",", ":")
        ).encode()


class VerificationExecutor(Protocol):
    """Execution boundary shared by deterministic replay and live Solari."""

    async def execute(
        self, request: ExecutionRequest, should_cancel: ShouldCancel
    ) -> ExecutionResult: ...


def command_sha256(request: ExecutionRequest) -> str:
    install, subject_path, execute = _execution_plan(request)
    plan = {
        "install": install,
        "subjectPath": subject_path,
        "execute": execute,
        "environmentNames": ["SOLARI_API_BASE_URL", "SOLARI_API_KEY"],
        "phase": request.phase,
        "sourceSurface": request.source_surface,
        "timeoutSeconds": request.timeout_seconds,
        "maxOutputBytes": request.max_output_bytes,
    }
    return hashlib.sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def redact_and_bound(
    stdout: str, stderr: str, *, secrets: tuple[str, ...], max_bytes: int
) -> tuple[str, str, bool]:
    """Redact known and recognizable credentials, then enforce one byte budget."""
    redacted = []
    patterns = (
        re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+"),
        re.compile(r"(?i)((?:solari_api_key|api[_-]?key)\s*[=:]\s*)[^\s]+"),
        re.compile(r"\b(?:sk|solari)_[A-Za-z0-9_-]{12,}\b"),
    )
    for value in (stdout, stderr):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        for pattern in patterns:
            value = pattern.sub(
                r"\1[REDACTED]" if pattern.groups else "[REDACTED]", value
            )
        redacted.append(value)

    remaining = max_bytes
    bounded: list[str] = []
    truncated = False
    for value in redacted:
        encoded = value.encode("utf-8")
        if len(encoded) > remaining:
            encoded = encoded[:remaining]
            value = encoded.decode("utf-8", "ignore")
            truncated = True
        bounded.append(value)
        remaining -= len(value.encode("utf-8"))
    return bounded[0], bounded[1], truncated


class ReplayVerificationExecutor:
    """Deterministic, explicitly labelled CI/dev evidence replay."""

    async def execute(
        self, request: ExecutionRequest, should_cancel: ShouldCancel
    ) -> ExecutionResult:
        started = datetime.now(UTC)
        if await should_cancel():
            return _cancelled_result(request, "REPLAY", started, "replay-load")
        payload = json.loads(request.replay_path.read_bytes())
        if (
            payload.get("schemaVersion") != "noxyn-execution-replay/1.0"
            or payload.get("fixture") is not True
            or payload.get("language") != request.language
            or payload.get("phase", "VERIFY") != request.phase
            or payload.get("sourceSurface", request.source_surface)
            != request.source_surface
            or payload.get("package")
            != {"name": request.package_name, "version": request.package_version}
            or payload.get("sourceSha256") != request.source_sha256
        ):
            raise ValueError("execution replay does not match the immutable request")
        stdout, stderr, truncated = redact_and_bound(
            payload["subject"]["stdout"],
            payload["subject"]["stderr"],
            secrets=(),
            max_bytes=request.max_output_bytes,
        )
        completed = datetime.now(UTC)
        return ExecutionResult(
            schema_version="noxyn-execution-evidence/1.0",
            fixture=True,
            backend="REPLAY",
            language=request.language,
            source_surface=request.source_surface,
            phase=request.phase,
            infrastructure_state=payload["infrastructure"]["state"],
            infrastructure_step=payload["infrastructure"]["step"],
            subject_state=payload["subject"]["state"],
            sandbox_id=f"replay:{request.source_sha256[:12]}",
            package_name=request.package_name,
            package_version=request.package_version,
            source_path=request.source_path,
            source_sha256=request.source_sha256,
            command_sha256=command_sha256(request),
            exit_code=payload["subject"]["exitCode"],
            stdout=stdout,
            stderr=stderr,
            output_truncated=truncated,
            duration_ms=payload["durationMs"],
            cleanup_state=payload["cleanupState"],
            cancelled=False,
            error_code=None,
            started_at=started.isoformat(),
            completed_at=completed.isoformat(),
        )


class SolariSandboxExecutor:
    """Run one pinned subject inside one freshly-created Solari Sandbox."""

    def __init__(self, *, api_key: str, base_url: str) -> None:
        if not api_key:
            raise ValueError("SOLARI_API_KEY is required for live execution")
        self.api_key = api_key
        self.base_url = base_url

    async def execute(
        self, request: ExecutionRequest, should_cancel: ShouldCancel
    ) -> ExecutionResult:
        from solari_sandbox import SandboxClient  # type: ignore[import-untyped]

        started = datetime.now(UTC)
        began = monotonic()
        sandbox = None
        sandbox_id: str | None = None
        cleanup: CleanupState = "NOT_REQUIRED"
        infra_state: InfrastructureState = "FAIL"
        infra_step = "create"
        subject_state: SubjectState = "NOT_RUN"
        exit_code: int | None = None
        stdout = ""
        stderr = ""
        cancelled = False
        error_code: str | None = None
        try:
            if await should_cancel():
                cancelled = True
            else:
                async with SandboxClient(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    call_timeout_ms=request.timeout_seconds * 1000,
                ) as client:
                    try:
                        async with asyncio.timeout(request.timeout_seconds):
                            sandbox = await client.create(
                                template="base",
                                timeout_ms=(request.timeout_seconds + 30) * 1000,
                                metadata={"purpose": "noxyn-verification"},
                            )
                            sandbox_id = sandbox.sandboxId
                            await sandbox.connect()
                        install_plan, subject_path, execute_plan = _execution_plan(
                            request
                        )
                        infra_step = "install"
                        install = await _run_bounded(
                            sandbox,
                            install_plan[0],
                            install_plan[1:],
                            {},
                            request.timeout_seconds,
                            should_cancel,
                        )
                        if install is None:
                            cancelled = True
                        elif install[0] != 0:
                            stdout, stderr, exit_code = (
                                install[1],
                                install[2],
                                install[0],
                            )
                            error_code = "PACKAGE_INSTALL_FAILED"
                        else:
                            infra_step = "materialize"
                            await sandbox.files.write(
                                subject_path, request.source, mode=0o600
                            )
                            infra_step = "execute"
                            result = await _run_bounded(
                                sandbox,
                                execute_plan[0],
                                execute_plan[1:],
                                {
                                    "SOLARI_API_KEY": self.api_key,
                                    "SOLARI_API_BASE_URL": self.base_url,
                                },
                                request.timeout_seconds,
                                should_cancel,
                            )
                            if result is None:
                                cancelled = True
                            else:
                                exit_code, stdout, stderr = result
                                infra_state = "PASS"
                                subject_state = "PASS" if exit_code == 0 else "FAIL"
                    finally:
                        if sandbox is not None:
                            try:
                                await client.kill(sandbox.sandboxId)
                                cleanup = "PASS"
                            except Exception as exc:  # cleanup is part of evidence
                                cleanup = "FAIL"
                                stderr = f"{stderr}\nCleanup error: {exc}".strip()
        except TimeoutError:
            error_code = "EXECUTION_TIMEOUT"
            stderr = f"{stderr}\nExecution exceeded its bounded timeout.".strip()
        except Exception as exc:
            error_code = "SOLARI_INFRASTRUCTURE_FAILED"
            stderr = f"{stderr}\n{type(exc).__name__}: {exc}".strip()

        stdout, stderr, truncated = redact_and_bound(
            stdout,
            stderr,
            secrets=(self.api_key,),
            max_bytes=request.max_output_bytes,
        )
        completed = datetime.now(UTC)
        return ExecutionResult(
            schema_version="noxyn-execution-evidence/1.0",
            fixture=True,
            backend="SOLARI",
            language=request.language,
            source_surface=request.source_surface,
            phase=request.phase,
            infrastructure_state=infra_state,
            infrastructure_step=infra_step,
            subject_state=subject_state,
            sandbox_id=sandbox_id,
            package_name=request.package_name,
            package_version=request.package_version,
            source_path=request.source_path,
            source_sha256=request.source_sha256,
            command_sha256=command_sha256(request),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            output_truncated=truncated,
            duration_ms=max(0, round((monotonic() - began) * 1000)),
            cleanup_state=cleanup,
            cancelled=cancelled,
            error_code=error_code,
            started_at=started.isoformat(),
            completed_at=completed.isoformat(),
        )


async def _run_bounded(
    sandbox: object,
    command: str,
    args: list[str],
    env: dict[str, str],
    timeout_seconds: int,
    should_cancel: ShouldCancel,
) -> tuple[int, str, str] | None:
    stdout: list[str] = []
    stderr: list[str] = []
    commands = getattr(sandbox, "commands")
    handle = await commands.start(
        command,
        args=args,
        env=env,
        on_stdout=stdout.append,
        on_stderr=stderr.append,
    )
    wait_task = asyncio.create_task(handle.wait())
    deadline = monotonic() + timeout_seconds
    try:
        while not wait_task.done():
            if await should_cancel():
                await handle.kill()
                await asyncio.gather(wait_task, return_exceptions=True)
                return None
            remaining = deadline - monotonic()
            if remaining <= 0:
                await handle.kill()
                await asyncio.gather(wait_task, return_exceptions=True)
                raise TimeoutError
            await asyncio.wait({wait_task}, timeout=min(0.25, remaining))
        return await wait_task, "".join(stdout), "".join(stderr)
    finally:
        if not wait_task.done():
            wait_task.cancel()


def _cancelled_result(
    request: ExecutionRequest,
    backend: ExecutorBackend,
    started: datetime,
    step: str,
) -> ExecutionResult:
    completed = datetime.now(UTC)
    return ExecutionResult(
        schema_version="noxyn-execution-evidence/1.0",
        fixture=True,
        backend=backend,
        language=request.language,
        source_surface=request.source_surface,
        phase=request.phase,
        infrastructure_state="FAIL",
        infrastructure_step=step,
        subject_state="NOT_RUN",
        sandbox_id=None,
        package_name=request.package_name,
        package_version=request.package_version,
        source_path=request.source_path,
        source_sha256=request.source_sha256,
        command_sha256=command_sha256(request),
        exit_code=None,
        stdout="",
        stderr="",
        output_truncated=False,
        duration_ms=0,
        cleanup_state="NOT_REQUIRED",
        cancelled=True,
        error_code=None,
        started_at=started.isoformat(),
        completed_at=completed.isoformat(),
    )


def _camelize(value: object) -> object:
    if isinstance(value, dict):
        return {_camel(key): _camelize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_camelize(item) for item in value]
    return value


def _camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.title() for part in rest)


def _execution_plan(request: ExecutionRequest) -> tuple[list[str], str, list[str]]:
    """Return reviewed argv-only install and execution commands."""
    if request.language == "python":
        return (
            [
                "python",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                f"{request.package_name}=={request.package_version}",
            ],
            "/tmp/noxyn_subject.py",
            ["python", "/tmp/noxyn_subject.py"],
        )
    return (
        [
            "npm",
            "install",
            "--prefix",
            "/tmp/noxyn-typescript",
            "--no-audit",
            "--no-fund",
            "--ignore-scripts",
            "--save-exact",
            f"{request.package_name}@{request.package_version}",
        ],
        "/tmp/noxyn-typescript/subject.mjs",
        ["node", "/tmp/noxyn-typescript/subject.mjs"],
    )
