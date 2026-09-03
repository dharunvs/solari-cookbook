"""Conservative, source-bound fixes for the controlled Python fixtures."""

from __future__ import annotations

import ast
import difflib
import re
from dataclasses import dataclass


class ProposalRejected(ValueError):
    """The source cannot be changed unambiguously by the reviewed rule."""


@dataclass(frozen=True, slots=True)
class ProposedChange:
    proposed: bytes
    patch: bytes
    changed_lines: int


def propose_memory_rename(source: bytes, *, surface: str, path: str) -> ProposedChange:
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError:
        raise ProposalRejected("source is not UTF-8") from None
    if surface == "python":
        proposed_text = _replace_python(text)
    elif surface == "docs_python":
        blocks = list(
            re.finditer(r"```python[ \t]*\n(?P<body>.*?)```", text, re.DOTALL)
        )
        if len(blocks) != 1:
            raise ProposalRejected(
                f"expected exactly one Python fence; found {len(blocks)}"
            )
        block = blocks[0]
        replacement = _replace_python(block.group("body"))
        proposed_text = (
            text[: block.start("body")] + replacement + text[block.end("body") :]
        )
    else:
        raise ProposalRejected("this source surface has no reviewed proposal rule")

    patch = "".join(
        difflib.unified_diff(
            text.splitlines(keepends=True),
            proposed_text.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )
    if not patch:
        raise ProposalRejected("proposal produced no change")
    return ProposedChange(
        proposed=proposed_text.encode(),
        patch=patch.encode(),
        changed_lines=sum(
            1
            for line in patch.splitlines()
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        ),
    )


def extract_python_fence(source: bytes) -> bytes:
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError:
        raise ProposalRejected("source is not UTF-8") from None
    blocks = list(re.finditer(r"```python[ \t]*\n(?P<body>.*?)```", text, re.DOTALL))
    if len(blocks) != 1:
        raise ProposalRejected(
            f"expected exactly one Python fence; found {len(blocks)}"
        )
    body = blocks[0].group("body")
    ast.parse(body)
    return body.encode()


def _replace_python(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        raise ProposalRejected("Python source does not parse") from None
    candidates: list[ast.keyword] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "create":
            continue
        candidates.extend(
            keyword for keyword in node.keywords if keyword.arg == "memory"
        )
    if len(candidates) != 1:
        raise ProposalRejected(
            f"expected exactly one stale create keyword; found {len(candidates)}"
        )
    keyword = candidates[0]
    if keyword.col_offset is None or keyword.end_col_offset is None:
        raise ProposalRejected("Python source location is unavailable")
    lines = source.splitlines(keepends=True)
    line = lines[keyword.lineno - 1]
    before = line[: keyword.col_offset]
    tail = line[keyword.col_offset :]
    if not tail.startswith("memory="):
        raise ProposalRejected("stale keyword source is ambiguous")
    lines[keyword.lineno - 1] = before + "mem_mb=" + tail[len("memory=") :]
    proposed = "".join(lines)
    try:
        parsed = ast.parse(proposed)
    except SyntaxError:
        raise ProposalRejected("proposed Python source does not parse") from None
    if (
        sum(
            1
            for node in ast.walk(parsed)
            if isinstance(node, ast.keyword) and node.arg == "mem_mb"
        )
        != 1
    ):
        raise ProposalRejected("proposed binding could not be validated")
    return proposed
