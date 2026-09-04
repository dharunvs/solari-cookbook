import asyncio
import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest
from noxyn_verification_worker.executor import (
    ExecutionRequest,
    ReplayVerificationExecutor,
    SolariSandboxExecutor,
    command_sha256,
    redact_and_bound,
)

ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = (
    ROOT
    / "noxyn_solari"
    / "fixtures"
    / "sandbox-create-evolution"
    / "runtime-python"
    / "main.py"
)
TYPESCRIPT_SOURCE_PATH = (
    ROOT
    / "noxyn_solari"
    / "fixtures"
    / "sandbox-create-evolution"
    / "runtime-typescript"
    / "main.mjs"
)
GO_SOURCE_PATH = (
    ROOT
    / "noxyn_solari"
    / "fixtures"
    / "sandbox-create-evolution"
    / "runtime-go"
    / "main.go"
)
CURRENT_SOURCE_PATHS = {
    "python": ROOT
    / "noxyn_solari"
    / "current_sources"
    / "cookbook"
    / "python"
    / "main.py",
    "typescript": ROOT
    / "noxyn_solari"
    / "current_sources"
    / "cookbook"
    / "typescript"
    / "main.mjs",
    "go": ROOT / "noxyn_solari" / "current_sources" / "cookbook" / "go" / "main.go",
}
CURRENT_PACKAGES = {
    "python": ("solari-sandbox", "0.2.0"),
    "typescript": ("@solarisdk/sandbox", "0.1.2"),
    "go": ("github.com/solari-sdk/solari-sandbox-go", "v0.1.2"),
}


def _request() -> ExecutionRequest:
    body = SOURCE_PATH.read_bytes()
    return ExecutionRequest(
        language="python",
        source_surface="python",
        phase="VERIFY",
        package_name="solari-sandbox",
        package_version="0.2.0",
        source_path=str(SOURCE_PATH.relative_to(ROOT)),
        source=body,
        source_sha256="d8129181ad58b87239f9f9c19f3a2f21c4fa426075878c26fa37306e6c7a09fb",
        timeout_seconds=45,
        max_output_bytes=16384,
        replay_path=ROOT
        / "noxyn_solari"
        / "fixtures"
        / "sandbox-create-evolution"
        / "replay"
        / "python-memory-failure.json",
    )


def _typescript_request() -> ExecutionRequest:
    body = TYPESCRIPT_SOURCE_PATH.read_bytes()
    return ExecutionRequest(
        language="typescript",
        source_surface="typescript",
        phase="VERIFY",
        package_name="@solarisdk/sandbox",
        package_version="0.1.2",
        source_path=str(TYPESCRIPT_SOURCE_PATH.relative_to(ROOT)),
        source=body,
        source_sha256="c44f01192490598f36ecc593b38d53d7194afc74288f0017850dbba5823d1e88",
        timeout_seconds=45,
        max_output_bytes=16384,
        replay_path=ROOT
        / "noxyn_solari"
        / "fixtures"
        / "sandbox-create-evolution"
        / "replay"
        / "typescript-memory-pass.json",
    )


def _go_request() -> ExecutionRequest:
    body = GO_SOURCE_PATH.read_bytes()
    return ExecutionRequest(
        language="go",
        source_surface="go",
        phase="VERIFY",
        package_name="github.com/solari-sdk/solari-sandbox-go",
        package_version="v0.1.2",
        source_path=str(GO_SOURCE_PATH.relative_to(ROOT)),
        source=body,
        source_sha256="54fbf77c06c0344dc583ab9ad363b6d998b2187c5c17bd4a7ae6c5628fbc700f",
        timeout_seconds=45,
        max_output_bytes=16384,
        replay_path=ROOT
        / "noxyn_solari"
        / "fixtures"
        / "sandbox-create-evolution"
        / "replay"
        / "go-mem-mb-pass.json",
    )


def _current_request(language: str) -> ExecutionRequest:
    source_path = CURRENT_SOURCE_PATHS[language]
    package_name, package_version = CURRENT_PACKAGES[language]
    source = source_path.read_bytes()
    return ExecutionRequest(
        language=language,  # type: ignore[arg-type]
        source_surface=language,
        phase="VERIFY",
        package_name=package_name,
        package_version=package_version,
        source_path=str(source_path.relative_to(ROOT)),
        source=source,
        source_sha256=hashlib.sha256(source).hexdigest(),
        timeout_seconds=45,
        max_output_bytes=16384,
        replay_path=(
            ROOT
            / "noxyn_solari"
            / "fixtures"
            / "current-configured-solari"
            / "replay"
            / f"{language}-pass.json"
        ),
    )


def test_replay_is_bound_to_source_and_reproduces_subject_failure() -> None:
    async def journey() -> None:
        result = await ReplayVerificationExecutor().execute(
            _request(), lambda: asyncio.sleep(0, result=False)
        )
        assert result.backend == "REPLAY"
        assert result.infrastructure_state == "PASS"
        assert result.subject_state == "FAIL"
        assert result.exit_code == 1
        assert "unexpected keyword argument 'memory'" in result.stderr
        assert result.cleanup_state == "PASS"
        assert b'"fixture":true' in result.evidence()

    asyncio.run(journey())


def test_replay_rejects_changed_source() -> None:
    request = _request()
    changed = replace(request, source_sha256="0" * 64)
    with pytest.raises(ValueError, match="immutable request"):
        asyncio.run(
            ReplayVerificationExecutor().execute(
                changed, lambda: asyncio.sleep(0, result=False)
            )
        )


def test_typescript_replay_uses_same_contract_and_passes() -> None:
    async def journey() -> None:
        result = await ReplayVerificationExecutor().execute(
            _typescript_request(), lambda: asyncio.sleep(0, result=False)
        )
        assert result.backend == "REPLAY"
        assert result.language == "typescript"
        assert result.infrastructure_state == "PASS"
        assert result.subject_state == "PASS"
        assert result.exit_code == 0
        assert "memMb" in result.stdout
        assert result.cleanup_state == "PASS"

    asyncio.run(journey())


def test_go_replay_is_labelled_and_bound_to_the_pinned_module() -> None:
    async def journey() -> None:
        result = await ReplayVerificationExecutor().execute(
            _go_request(), lambda: asyncio.sleep(0, result=False)
        )
        assert result.backend == "REPLAY"
        assert result.language == "go"
        assert result.package_name == "github.com/solari-sdk/solari-sandbox-go"
        assert result.package_version == "v0.1.2"
        assert result.infrastructure_state == "PASS"
        assert result.subject_state == "PASS"
        assert result.exit_code == 0
        assert "MemMb" in result.stdout
        assert result.cleanup_state == "PASS"

    asyncio.run(journey())


def test_current_replay_runs_python_typescript_and_go_independently() -> None:
    async def journey() -> None:
        results = await asyncio.gather(
            *(
                ReplayVerificationExecutor().execute(
                    _current_request(language), lambda: asyncio.sleep(0, result=False)
                )
                for language in ("python", "typescript", "go")
            )
        )
        assert [result.language for result in results] == ["python", "typescript", "go"]
        assert all(result.backend == "REPLAY" for result in results)
        assert all(result.infrastructure_state == "PASS" for result in results)
        assert all(result.subject_state == "PASS" for result in results)
        assert all(result.cleanup_state == "PASS" for result in results)
        assert len({result.source_sha256 for result in results}) == 3

    asyncio.run(journey())


def test_current_replay_preserves_infrastructure_and_subject_failure_truth(
    tmp_path: Path,
) -> None:
    request = _current_request("python")
    payload = json.loads(request.replay_path.read_bytes())
    payload["infrastructure"] = {"state": "FAIL", "step": "install"}
    payload["subject"] = {
        "state": "NOT_RUN",
        "exitCode": None,
        "stdout": "",
        "stderr": "",
    }
    unavailable = tmp_path / "infrastructure-failure.json"
    unavailable.write_text(json.dumps(payload), encoding="utf-8")
    result = asyncio.run(
        ReplayVerificationExecutor().execute(
            replace(request, replay_path=unavailable),
            lambda: asyncio.sleep(0, result=False),
        )
    )
    assert result.infrastructure_state == "FAIL"
    assert result.subject_state == "NOT_RUN"
    assert result.cleanup_state == "PASS"


def test_redaction_precedes_combined_output_limit() -> None:
    stdout, stderr, truncated = redact_and_bound(
        "SOLARI_API_KEY=solari_supersecretvalue\n" + "x" * 20,
        "Authorization: Bearer token-secret\n",
        secrets=("solari_supersecretvalue",),
        max_bytes=40,
    )
    combined = (stdout + stderr).encode()
    assert b"supersecret" not in combined
    assert b"token-secret" not in combined
    assert len(combined) <= 40
    assert truncated is True


def test_solari_executor_cleans_up_and_separates_subject_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import solari_sandbox  # type: ignore[import-untyped]

    killed: list[str] = []

    class Handle:
        def __init__(self, exit_code: int, output: str = "") -> None:
            self.exit_code = exit_code
            self.output = output

        async def wait(self) -> int:
            return self.exit_code

        async def kill(self) -> None:
            return None

    class Commands:
        calls = 0

        async def start(self, *_args: object, **kwargs: object) -> Handle:
            self.calls += 1
            if self.calls == 1:
                return Handle(0)
            callback = kwargs["on_stderr"]
            assert callable(callback)
            callback("TypeError: bad memory; key=solari_test_secretvalue")
            return Handle(1)

    class Files:
        async def write(self, path: str, body: bytes, mode: int) -> None:
            assert path == "/tmp/noxyn_subject.py"
            assert body == _request().source
            assert mode == 0o600

    class Sandbox:
        sandboxId = "sbx_test"
        commands = Commands()
        files = Files()

        async def connect(self) -> None:
            return None

    class Client:
        def __init__(self, **_kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "Client":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def create(self, **_kwargs: object) -> Sandbox:
            return Sandbox()

        async def kill(self, sandbox_id: str) -> None:
            killed.append(sandbox_id)

    monkeypatch.setattr(solari_sandbox, "SandboxClient", Client)

    async def journey() -> None:
        result = await SolariSandboxExecutor(
            api_key="solari_test_secretvalue", base_url="https://example.test"
        ).execute(_request(), lambda: asyncio.sleep(0, result=False))
        assert result.infrastructure_state == "PASS"
        assert result.subject_state == "FAIL"
        assert result.exit_code == 1
        assert result.cleanup_state == "PASS"
        assert result.sandbox_id == "sbx_test"
        assert "secretvalue" not in result.stderr
        assert killed == ["sbx_test"]

    asyncio.run(journey())


def test_solari_executor_marks_provisioning_failure_unverified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import solari_sandbox  # type: ignore[import-untyped]

    class Client:
        def __init__(self, **_kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "Client":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def create(self, **_kwargs: object) -> object:
            raise RuntimeError("verification sandbox unavailable")

    monkeypatch.setattr(solari_sandbox, "SandboxClient", Client)

    async def journey() -> None:
        result = await SolariSandboxExecutor(
            api_key="solari_test_secretvalue", base_url="https://example.test"
        ).execute(_request(), lambda: asyncio.sleep(0, result=False))
        assert result.infrastructure_state == "FAIL"
        assert result.infrastructure_step == "create"
        assert result.subject_state == "NOT_RUN"
        assert result.cleanup_state == "NOT_REQUIRED"

    asyncio.run(journey())


def test_solari_executor_installs_and_runs_typescript_with_argv_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import solari_sandbox

    calls: list[tuple[str, list[str]]] = []
    writes: list[tuple[str, bytes, int]] = []
    killed: list[str] = []

    class Handle:
        async def wait(self) -> int:
            return 0

        async def kill(self) -> None:
            return None

    class Commands:
        async def start(self, command: str, **kwargs: object) -> Handle:
            args = kwargs["args"]
            assert isinstance(args, list)
            calls.append((command, args))
            if command == "node":
                callback = kwargs["on_stdout"]
                assert callable(callback)
                callback("TypeScript Sandbox.create({ memMb }) succeeded.\n")
            return Handle()

    class Files:
        async def write(self, path: str, body: bytes, mode: int) -> None:
            writes.append((path, body, mode))

    class Sandbox:
        sandboxId = "sbx_typescript"
        commands = Commands()
        files = Files()

        async def connect(self) -> None:
            return None

    class Client:
        def __init__(self, **_kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "Client":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def create(self, **_kwargs: object) -> Sandbox:
            return Sandbox()

        async def kill(self, sandbox_id: str) -> None:
            killed.append(sandbox_id)

    monkeypatch.setattr(solari_sandbox, "SandboxClient", Client)

    async def journey() -> None:
        request = _typescript_request()
        result = await SolariSandboxExecutor(
            api_key="solari_test_secretvalue", base_url="https://example.test"
        ).execute(request, lambda: asyncio.sleep(0, result=False))
        assert result.infrastructure_state == "PASS"
        assert result.subject_state == "PASS"
        assert result.language == "typescript"
        assert calls[0] == (
            "npm",
            [
                "install",
                "--prefix",
                "/tmp/noxyn-typescript",
                "--no-audit",
                "--no-fund",
                "--ignore-scripts",
                "--save-exact",
                "@solarisdk/sandbox@0.1.2",
            ],
        )
        assert calls[1] == ("node", ["/tmp/noxyn-typescript/subject.mjs"])
        assert writes == [("/tmp/noxyn-typescript/subject.mjs", request.source, 0o600)]
        assert killed == ["sbx_typescript"]

    asyncio.run(journey())


def test_solari_executor_installs_and_runs_go_with_pinned_module_and_argv_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import solari_sandbox

    calls: list[tuple[str, list[str], str | None]] = []
    directories: list[str] = []
    writes: list[tuple[str, bytes, int]] = []
    killed: list[str] = []

    class Handle:
        async def wait(self) -> int:
            return 0

        async def kill(self) -> None:
            return None

    class Commands:
        async def start(self, command: str, **kwargs: object) -> Handle:
            args = kwargs["args"]
            cwd = kwargs["cwd"]
            assert isinstance(args, list)
            assert cwd is None or isinstance(cwd, str)
            calls.append((command, args, cwd))
            if command == "go" and args == ["run", "."]:
                callback = kwargs["on_stdout"]
                assert callable(callback)
                callback("Go Sandbox.Create(CreateOptions{MemMb}) succeeded.\n")
            return Handle()

    class Files:
        async def mkdir(self, path: str) -> None:
            directories.append(path)

        async def write(self, path: str, body: bytes, mode: int) -> None:
            writes.append((path, body, mode))

    class Sandbox:
        sandboxId = "sbx_go"
        commands = Commands()
        files = Files()

        async def connect(self) -> None:
            return None

    class Client:
        def __init__(self, **_kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "Client":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def create(self, **_kwargs: object) -> Sandbox:
            return Sandbox()

        async def kill(self, sandbox_id: str) -> None:
            killed.append(sandbox_id)

    monkeypatch.setattr(solari_sandbox, "SandboxClient", Client)

    async def journey() -> None:
        request = _go_request()
        result = await SolariSandboxExecutor(
            api_key="solari_test_secretvalue", base_url="https://example.test"
        ).execute(request, lambda: asyncio.sleep(0, result=False))
        assert result.infrastructure_state == "PASS"
        assert result.subject_state == "PASS"
        assert result.language == "go"
        assert result.cleanup_state == "PASS"
        assert calls == [
            ("go", ["mod", "download"], "/tmp/noxyn-go"),
            ("go", ["run", "."], "/tmp/noxyn-go"),
        ]
        assert directories == ["/tmp/noxyn-go"]
        assert [path for path, _, _ in writes] == [
            "/tmp/noxyn-go/go.mod",
            "/tmp/noxyn-go/go.sum",
            "/tmp/noxyn-go/main.go",
        ]
        assert b"github.com/solari-sdk/solari-sandbox-go v0.1.2" in writes[0][1]
        assert writes[2] == ("/tmp/noxyn-go/main.go", request.source, 0o600)
        assert killed == ["sbx_go"]

    asyncio.run(journey())


def test_go_plan_rejects_an_unpinned_module_request() -> None:
    request = replace(_go_request(), package_version="v0.1.3")
    with pytest.raises(ValueError, match="reviewed pinned module"):
        command_sha256(request)


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("NOXYN_RUN_LIVE_TESTS") != "true" or not os.getenv("SOLARI_API_KEY"),
    reason="set NOXYN_RUN_LIVE_TESTS=true and SOLARI_API_KEY",
)
def test_live_solari_controlled_failure_cleans_up() -> None:
    async def journey() -> None:
        result = await SolariSandboxExecutor(
            api_key=os.environ["SOLARI_API_KEY"],
            base_url=os.getenv("SOLARI_API_BASE_URL", "https://api.getsolari.com"),
        ).execute(_request(), lambda: asyncio.sleep(0, result=False))
        assert result.infrastructure_state == "PASS"
        assert result.subject_state == "FAIL"
        assert result.cleanup_state == "PASS"
        assert result.sandbox_id and result.sandbox_id.startswith("sbx_")

    asyncio.run(journey())


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("NOXYN_RUN_LIVE_TESTS") != "true" or not os.getenv("SOLARI_API_KEY"),
    reason="set NOXYN_RUN_LIVE_TESTS=true and SOLARI_API_KEY",
)
def test_live_solari_controlled_typescript_pass_cleans_up() -> None:
    async def journey() -> None:
        result = await SolariSandboxExecutor(
            api_key=os.environ["SOLARI_API_KEY"],
            base_url=os.getenv("SOLARI_API_BASE_URL", "https://api.getsolari.com"),
        ).execute(_typescript_request(), lambda: asyncio.sleep(0, result=False))
        assert result.infrastructure_state == "PASS"
        assert result.subject_state == "PASS"
        assert result.cleanup_state == "PASS"
        assert result.sandbox_id and result.sandbox_id.startswith("sbx_")

    asyncio.run(journey())


@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("NOXYN_RUN_LIVE_TESTS") != "true" or not os.getenv("SOLARI_API_KEY"),
    reason="set NOXYN_RUN_LIVE_TESTS=true and SOLARI_API_KEY",
)
def test_live_solari_controlled_go_pass_cleans_up() -> None:
    async def journey() -> None:
        result = await SolariSandboxExecutor(
            api_key=os.environ["SOLARI_API_KEY"],
            base_url=os.getenv("SOLARI_API_BASE_URL", "https://api.getsolari.com"),
        ).execute(_go_request(), lambda: asyncio.sleep(0, result=False))
        assert result.infrastructure_state == "PASS"
        assert result.subject_state == "PASS"
        assert result.cleanup_state == "PASS"
        assert result.sandbox_id and result.sandbox_id.startswith("sbx_")

    asyncio.run(journey())
