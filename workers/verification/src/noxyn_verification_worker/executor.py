"""Bounded, evidence-producing Python, TypeScript, and Go executors."""

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
Language = Literal["python", "typescript", "go"]
ExecutionPhase = Literal["VERIFY", "FIX_VERIFY"]

GO_MODULE_PATH = "github.com/solari-sdk/solari-sandbox-go"
GO_MODULE_VERSION = "v0.1.2"
GO_MODULE_COMMIT = "15ae65c3177f4eeb270e000f5065787abe581e0f"
GO_MODULE_SUM = "h1:kQNL62OzUnIDSzYRn8reVNwqMsE0hEa6WpdZteCpeWQ="
GO_MODULE_GO_MOD_SUM = "h1:271EoaPtL6UayY2TC2j+dN/jBVaibX/TP4XqFgs9uwQ="
GO_WEBSOCKET_VERSION = "v1.5.3"
GO_WEBSOCKET_SUM = "h1:saDtZ6Pbx/0u+bgYQ3q96pZgCzfhKXGPqt7kZ72aNNg="
GO_WEBSOCKET_GO_MOD_SUM = "h1:YR8l580nyteQvAITg2hZ9XVh4b55+EU/adAjf1fMHhE="
GO_SUBJECT_DIRECTORY = "/tmp/noxyn-go"


@dataclass(frozen=True, slots=True)
class CommandPlan:
    """One reviewed executable-plus-argv command."""

    executable: str
    argv: tuple[str, ...]
    cwd: str | None = None


@dataclass(frozen=True, slots=True)
class MaterializedFile:
    """One immutable byte sequence written before a command phase."""

    path: str
    body: bytes
    mode: int = 0o600


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Reviewed per-language execution unit; no shell interpretation."""

    directories: tuple[str, ...]
    preinstall_files: tuple[MaterializedFile, ...]
    install: tuple[CommandPlan, ...]
    subject_file: MaterializedFile
    execute: CommandPlan
    package_evidence: dict[str, str]


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
    execution_plan = _execution_plan(request)
    if request.language == "go":
        plan = {
            "directories": execution_plan.directories,
            "preinstallFiles": [
                {
                    "path": file.path,
                    "sha256": hashlib.sha256(file.body).hexdigest(),
                    "mode": file.mode,
                }
                for file in execution_plan.preinstall_files
            ],
            "install": [
                {
                    "executable": command.executable,
                    "argv": command.argv,
                    "cwd": command.cwd,
                }
                for command in execution_plan.install
            ],
            "subject": {
                "path": execution_plan.subject_file.path,
                "sha256": hashlib.sha256(execution_plan.subject_file.body).hexdigest(),
                "mode": execution_plan.subject_file.mode,
            },
            "execute": {
                "executable": execution_plan.execute.executable,
                "argv": execution_plan.execute.argv,
                "cwd": execution_plan.execute.cwd,
            },
            "packageEvidence": execution_plan.package_evidence,
            "environmentNames": ["SOLARI_API_BASE_URL", "SOLARI_API_KEY"],
            "phase": request.phase,
            "sourceSurface": request.source_surface,
            "timeoutSeconds": request.timeout_seconds,
            "maxOutputBytes": request.max_output_bytes,
        }
    else:
        # Preserve the previously persisted Python and TypeScript plan hashes.
        plan = {
            "install": [
                execution_plan.install[0].executable,
                *execution_plan.install[0].argv,
            ],
            "subjectPath": execution_plan.subject_file.path,
            "execute": [
                execution_plan.execute.executable,
                *execution_plan.execute.argv,
            ],
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
                        execution_plan = _execution_plan(request)
                        infra_step = "materialize"
                        for directory in execution_plan.directories:
                            await sandbox.files.mkdir(directory)
                        for file in execution_plan.preinstall_files:
                            await sandbox.files.write(
                                file.path, file.body, mode=file.mode
                            )
                        infra_step = "install"
                        for install_plan in execution_plan.install:
                            install = await _run_bounded(
                                sandbox,
                                install_plan.executable,
                                list(install_plan.argv),
                                {},
                                request.timeout_seconds,
                                should_cancel,
                                cwd=install_plan.cwd,
                            )
                            if install is None:
                                cancelled = True
                                break
                            if install[0] != 0:
                                stdout, stderr, exit_code = (
                                    install[1],
                                    install[2],
                                    install[0],
                                )
                                error_code = "PACKAGE_INSTALL_FAILED"
                                break
                        if not cancelled and error_code is None:
                            infra_step = "materialize"
                            await sandbox.files.write(
                                execution_plan.subject_file.path,
                                execution_plan.subject_file.body,
                                mode=execution_plan.subject_file.mode,
                            )
                            infra_step = "execute"
                            result = await _run_bounded(
                                sandbox,
                                execution_plan.execute.executable,
                                list(execution_plan.execute.argv),
                                {
                                    "SOLARI_API_KEY": self.api_key,
                                    "SOLARI_API_BASE_URL": self.base_url,
                                },
                                request.timeout_seconds,
                                should_cancel,
                                cwd=execution_plan.execute.cwd,
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
    *,
    cwd: str | None = None,
) -> tuple[int, str, str] | None:
    stdout: list[str] = []
    stderr: list[str] = []
    commands = getattr(sandbox, "commands")
    handle = await commands.start(
        command,
        args=args,
        cwd=cwd,
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


def _execution_plan(request: ExecutionRequest) -> ExecutionPlan:
    """Return reviewed argv-only install and execution commands."""
    if request.language == "python":
        return ExecutionPlan(
            directories=(),
            preinstall_files=(),
            install=(
                CommandPlan(
                    "python",
                    (
                        "-m",
                        "pip",
                        "install",
                        "--disable-pip-version-check",
                        "--no-input",
                        f"{request.package_name}=={request.package_version}",
                    ),
                ),
            ),
            subject_file=MaterializedFile("/tmp/noxyn_subject.py", request.source),
            execute=CommandPlan("python", ("/tmp/noxyn_subject.py",)),
            package_evidence={},
        )
    if request.language == "typescript":
        return ExecutionPlan(
            directories=(),
            preinstall_files=(),
            install=(
                CommandPlan(
                    "npm",
                    (
                        "install",
                        "--prefix",
                        "/tmp/noxyn-typescript",
                        "--no-audit",
                        "--no-fund",
                        "--ignore-scripts",
                        "--save-exact",
                        f"{request.package_name}@{request.package_version}",
                    ),
                ),
            ),
            subject_file=MaterializedFile(
                "/tmp/noxyn-typescript/subject.mjs", request.source
            ),
            execute=CommandPlan("node", ("/tmp/noxyn-typescript/subject.mjs",)),
            package_evidence={},
        )
    if (
        request.package_name != GO_MODULE_PATH
        or request.package_version != GO_MODULE_VERSION
    ):
        raise ValueError("Go execution must use the reviewed pinned module")
    return ExecutionPlan(
        directories=(GO_SUBJECT_DIRECTORY,),
        preinstall_files=(
            MaterializedFile(f"{GO_SUBJECT_DIRECTORY}/go.mod", _go_mod()),
            MaterializedFile(f"{GO_SUBJECT_DIRECTORY}/go.sum", _go_sum()),
        ),
        install=(CommandPlan("go", ("mod", "download"), GO_SUBJECT_DIRECTORY),),
        subject_file=MaterializedFile(
            f"{GO_SUBJECT_DIRECTORY}/main.go", request.source
        ),
        execute=CommandPlan("go", ("run", "."), GO_SUBJECT_DIRECTORY),
        package_evidence={
            "moduleCommit": GO_MODULE_COMMIT,
            "moduleSum": GO_MODULE_SUM,
            "moduleGoModSum": GO_MODULE_GO_MOD_SUM,
            "dependencyModule": "github.com/gorilla/websocket",
            "dependencyVersion": GO_WEBSOCKET_VERSION,
            "dependencySum": GO_WEBSOCKET_SUM,
            "dependencyGoModSum": GO_WEBSOCKET_GO_MOD_SUM,
        },
    )


def _go_mod() -> bytes:
    return (
        "module noxyn/verification-subject\n\n"
        "go 1.23.4\n\n"
        f"require {GO_MODULE_PATH} {GO_MODULE_VERSION}\n\n"
        f"require github.com/gorilla/websocket {GO_WEBSOCKET_VERSION} // indirect\n"
    ).encode()


def _go_sum() -> bytes:
    return (
        f"{GO_MODULE_PATH} {GO_MODULE_VERSION} {GO_MODULE_SUM}\n"
        f"{GO_MODULE_PATH} {GO_MODULE_VERSION}/go.mod {GO_MODULE_GO_MOD_SUM}\n"
        f"github.com/gorilla/websocket {GO_WEBSOCKET_VERSION} {GO_WEBSOCKET_SUM}\n"
        "github.com/gorilla/websocket "
        f"{GO_WEBSOCKET_VERSION}/go.mod {GO_WEBSOCKET_GO_MOD_SUM}\n"
    ).encode()
