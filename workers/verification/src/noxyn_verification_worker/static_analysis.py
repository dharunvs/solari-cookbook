"""Deterministic analysis for the controlled Sandbox API-evolution fixture."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

StaticState = Literal["ALIGNED", "SUSPECTED", "NOT_EXPECTED", "UNVERIFIED"]
Surface = Literal[
    "contract", "python", "typescript", "go", "docs_python", "docs_typescript"
]

PARSER_VERSION = "sandbox-create-static/1.0"
CANONICAL_CAPABILITY = "sandbox.create.memory_mb"


def canonical_json(value: object) -> bytes:
    """Serialize evidence in one stable representation before hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    surface: str
    kind: str
    path: str
    body: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class Observation:
    state: StaticState
    observed: str | None
    locator: str | None
    excerpt: str | None
    summary: str


def load_manifest(
    repository_root: Path, manifest_path: Path
) -> tuple[dict[str, Any], bytes]:
    root = repository_root.resolve(strict=True)
    resolved = manifest_path.resolve(strict=True)
    if root not in resolved.parents:
        raise ValueError("manifest escapes repository root")
    body = resolved.read_bytes()
    manifest = json.loads(body)
    if manifest.get("schemaVersion") != "noxyn-solari-manifest/1.0":
        raise ValueError("unsupported manifest schema")
    if manifest.get("scenario") != "sandbox-create-evolution" or not manifest.get(
        "fixture"
    ):
        raise ValueError("worker accepts only the controlled fixture manifest")
    return manifest, body


def snapshot_sources(
    repository_root: Path, manifest: dict[str, Any]
) -> tuple[SourceSnapshot, ...]:
    snapshots: list[SourceSnapshot] = []
    paths: list[tuple[str, str, str]] = [
        ("contract_before", "contract", manifest["contracts"]["before"]),
        ("contract_after", "contract", manifest["contracts"]["after"]),
    ]
    paths.extend(
        (item["surface"], item["kind"], item["path"]) for item in manifest["sources"]
    )
    for surface, kind, relative in paths:
        path = _safe_source_path(repository_root, relative)
        body = path.read_bytes()
        snapshots.append(SourceSnapshot(surface, kind, relative, body, sha256(body)))
    return tuple(snapshots)


def build_matrix(
    manifest: dict[str, Any],
    manifest_body: bytes,
    snapshots: tuple[SourceSnapshot, ...],
) -> dict[str, Any]:
    by_surface = {item.surface: item for item in snapshots}
    before = json.loads(by_surface["contract_before"].body)
    after = json.loads(by_surface["contract_after"].body)
    before_capability = _capability(before, CANONICAL_CAPABILITY)
    after_capability = _capability(after, CANONICAL_CAPABILITY)
    if not after_capability.get("bindings"):
        raise ValueError("after-contract has no reviewed language bindings")

    cells: list[dict[str, Any]] = []
    contract_state: StaticState = (
        "ALIGNED"
        if before_capability["wireName"] == "memory"
        and after_capability["wireName"] == "memMb"
        else "UNVERIFIED"
    )
    cells.append(
        _cell(
            "contract",
            contract_state,
            after_capability["wireName"],
            before_capability["wireName"],
            by_surface["contract_after"],
            "$.capabilities[0].wireName",
            '"wireName": "memMb"',
            "Reviewed fixture contract changes the wire field from memory to memMb."
            if contract_state == "ALIGNED"
            else "The controlled contract evolution could not be normalized.",
        )
    )

    extractors = {
        "python": (_extract_python, after_capability["bindings"]["python"]),
        "typescript": (
            _extract_typescript,
            after_capability["bindings"]["typescript"],
        ),
        "go": (_extract_go, after_capability["bindings"]["go"]),
        "docs_python": (
            lambda body, expected: _extract_markdown(body, "python", expected),
            after_capability["bindings"]["python"],
        ),
        "docs_typescript": (
            lambda body, expected: _extract_markdown(body, "typescript", expected),
            after_capability["bindings"]["typescript"],
        ),
    }
    for surface, (extractor, expected) in extractors.items():
        source = by_surface.get(surface)
        if source is None:
            cells.append(
                _cell(
                    surface,
                    "NOT_EXPECTED",
                    expected,
                    None,
                    None,
                    None,
                    None,
                    "This surface is not configured in the reviewed manifest.",
                )
            )
            continue
        observation = extractor(source.body.decode("utf-8"), expected)
        cells.append(
            _cell(
                surface,
                observation.state,
                expected,
                observation.observed,
                source,
                observation.locator,
                observation.excerpt,
                observation.summary,
            )
        )

    states = [cell["state"] for cell in cells]
    summary = {
        "capabilities": 1,
        "aligned": states.count("ALIGNED"),
        "suspected": states.count("SUSPECTED"),
        "notExpected": states.count("NOT_EXPECTED"),
        "unverified": states.count("UNVERIFIED"),
    }
    return {
        "schemaVersion": "noxyn-static-analysis-result/1.0",
        "scenario": manifest["scenario"],
        "fixture": True,
        "parserVersion": PARSER_VERSION,
        "manifestSha256": sha256(manifest_body),
        "contractDiff": {
            "capabilityId": CANONICAL_CAPABILITY,
            "before": before_capability["wireName"],
            "after": after_capability["wireName"],
            "classification": "RENAMED",
        },
        "packages": manifest["packages"],
        "summary": summary,
        "rows": [
            {
                "capabilityId": CANONICAL_CAPABILITY,
                "label": "Create sandbox memory limit",
                "cells": cells,
                "runtime": {
                    "state": "NOT_RUN",
                    "summary": "Runtime verification begins in Phase 5.",
                },
            }
        ],
    }


def suspected_cells(matrix: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(
        cell
        for row in matrix["rows"]
        for cell in row["cells"]
        if cell["state"] == "SUSPECTED"
    )


def extract_python_fence(source: bytes) -> bytes:
    """Return the one exact runnable Python block from a documentation artifact."""
    text = source.decode("utf-8")
    blocks = list(re.finditer(r"```python[ \t]*\n(?P<body>.*?)```", text, re.DOTALL))
    if len(blocks) != 1:
        raise ValueError(
            f"expected one Python documentation block; found {len(blocks)}"
        )
    body = blocks[0].group("body")
    ast.parse(body)
    return body.encode()


def _capability(contract: dict[str, Any], capability_id: str) -> dict[str, Any]:
    matches = [item for item in contract["capabilities"] if item["id"] == capability_id]
    if len(matches) != 1:
        raise ValueError(f"contract must define {capability_id} exactly once")
    return cast(dict[str, Any], matches[0])


def _safe_source_path(repository_root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("manifest source path is unsafe")
    root = repository_root.resolve(strict=True)
    path = (root / relative).resolve(strict=True)
    if root not in path.parents or not path.is_file() or path.is_symlink():
        raise ValueError("manifest source is unavailable")
    return path


def _cell(
    surface: str,
    state: StaticState,
    expected: str,
    observed: str | None,
    source: SourceSnapshot | None,
    locator: str | None,
    excerpt: str | None,
    summary: str,
) -> dict[str, Any]:
    evidence = None
    if source is not None and locator is not None and excerpt is not None:
        evidence = {
            "path": source.path,
            "sha256": source.sha256,
            "locator": locator,
            "excerpt": excerpt[:300],
        }
    return {
        "surface": surface,
        "state": state,
        "expected": expected,
        "observed": observed,
        "summary": summary,
        "evidence": evidence,
    }


def _extract_python(source: str, expected: str) -> Observation:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return Observation(
            "UNVERIFIED", None, None, None, "Python source did not parse."
        )
    matches: list[tuple[str, int, str]] = []
    lines = source.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_create_call(node.func):
            continue
        for keyword in node.keywords:
            if keyword.arg in {"memory", "mem_mb"}:
                matches.append(
                    (keyword.arg, node.lineno, lines[node.lineno - 1].strip())
                )
    return _observation(matches, expected, "Python")


def _is_create_call(node: ast.expr) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "create"


def _extract_typescript(source: str, expected: str) -> Observation:
    return _regex_observation(
        source,
        expected,
        r"\b(?:Sandbox|sandbox)\.create\s*\(\s*\{(?P<body>[^}]*)\}",
        r"\b(?P<name>memory|memMb)\s*:",
        "TypeScript",
    )


def _extract_go(source: str, expected: str) -> Observation:
    return _regex_observation(
        source,
        expected,
        r"CreateOptions\s*\{(?P<body>[^}]*)\}",
        r"\b(?P<name>Memory|MemMb)\s*:",
        "Go",
    )


def _extract_markdown(source: str, language: str, expected: str) -> Observation:
    pattern = re.compile(rf"```{language}\s*\n(?P<body>.*?)```", re.DOTALL)
    blocks = [match.group("body") for match in pattern.finditer(source)]
    if len(blocks) != 1:
        return Observation(
            "UNVERIFIED",
            None,
            None,
            None,
            f"Expected one {language} documentation block; found {len(blocks)}.",
        )
    observation = (
        _extract_python(blocks[0], expected)
        if language == "python"
        else _extract_typescript(blocks[0], expected)
    )
    if observation.locator:
        fence_line = source[: pattern.search(source).start()].count("\n") + 2  # type: ignore[union-attr]
        block_line = int(observation.locator.removeprefix("line "))
        observation = Observation(
            observation.state,
            observation.observed,
            f"line {fence_line + block_line - 1}",
            observation.excerpt,
            observation.summary.replace(language.title(), f"{language.title()} docs"),
        )
    return observation


def _regex_observation(
    source: str, expected: str, call_pattern: str, field_pattern: str, label: str
) -> Observation:
    matches: list[tuple[str, int, str]] = []
    for call in re.finditer(call_pattern, source, re.DOTALL):
        body = call.group("body")
        for field in re.finditer(field_pattern, body):
            absolute = call.start("body") + field.start("name")
            line_number = source.count("\n", 0, absolute) + 1
            matches.append(
                (
                    field.group("name"),
                    line_number,
                    source.splitlines()[line_number - 1].strip(),
                )
            )
    return _observation(matches, expected, label)


def _observation(
    matches: list[tuple[str, int, str]], expected: str, label: str
) -> Observation:
    unique = {name for name, _, _ in matches}
    if len(matches) != 1 or len(unique) != 1:
        return Observation(
            "UNVERIFIED",
            None,
            None,
            None,
            f"{label} extraction found {len(matches)} candidate fields; "
            "no claim was made.",
        )
    observed, line, excerpt = matches[0]
    if observed == expected:
        return Observation(
            "ALIGNED",
            observed,
            f"line {line}",
            excerpt,
            f"{label} uses the reviewed {expected} binding.",
        )
    return Observation(
        "SUSPECTED",
        observed,
        f"line {line}",
        excerpt,
        f"{label} uses {observed}; the reviewed binding is {expected}.",
    )
