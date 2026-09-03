import json
from pathlib import Path

from noxyn_verification_worker.static_analysis import (
    build_matrix,
    load_manifest,
    snapshot_sources,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = (
    REPOSITORY_ROOT / "noxyn_solari" / "manifests" / "sandbox-create-evolution.v1.json"
)
EXPECTED = (
    REPOSITORY_ROOT
    / "noxyn_solari"
    / "fixtures"
    / "sandbox-create-evolution"
    / "expected-results.json"
)
PHASE6_MANIFEST = (
    REPOSITORY_ROOT / "noxyn_solari" / "manifests" / "sandbox-create-evolution.v3.json"
)


def test_controlled_fixture_matches_the_golden_result() -> None:
    manifest, body = load_manifest(REPOSITORY_ROOT, MANIFEST)
    snapshots = snapshot_sources(REPOSITORY_ROOT, manifest)
    first = build_matrix(manifest, body, snapshots)
    second = build_matrix(manifest, body, snapshots)
    expected = json.loads(EXPECTED.read_bytes())

    cells = [
        {
            "capabilityId": row["capabilityId"],
            "surface": cell["surface"],
            "state": cell["state"],
        }
        for row in first["rows"]
        for cell in row["cells"]
    ]
    assert first == second
    assert first["summary"] == expected["summary"]
    assert cells == expected["cells"]
    assert first["rows"][0]["runtime"]["state"] == "NOT_RUN"
    assert all(len(snapshot.sha256) == 64 for snapshot in snapshots)


def test_ambiguous_python_source_is_unverified(tmp_path: Path) -> None:
    ambiguous = tmp_path / "ambiguous.py"
    ambiguous.write_text(
        "Sandbox.create(memory=1)\nSandbox.create(mem_mb=1)\n", encoding="utf-8"
    )
    # Exercise the extractor through a replaced immutable snapshot so the
    # manifest path-safety contract remains independent of pytest temp paths.
    loaded, body = load_manifest(REPOSITORY_ROOT, MANIFEST)
    snapshots = list(snapshot_sources(REPOSITORY_ROOT, loaded))
    python = next(item for item in snapshots if item.surface == "python")
    snapshots[snapshots.index(python)] = type(python)(
        python.surface,
        python.kind,
        python.path,
        ambiguous.read_bytes(),
        "0" * 64,
    )
    matrix = build_matrix(loaded, body, tuple(snapshots))
    cell = next(
        item for item in matrix["rows"][0]["cells"] if item["surface"] == "python"
    )
    assert cell["state"] == "UNVERIFIED"
    assert "no claim" in cell["summary"]


def test_phase6_executable_typescript_source_is_statically_aligned() -> None:
    manifest, body = load_manifest(REPOSITORY_ROOT, PHASE6_MANIFEST)
    matrix = build_matrix(manifest, body, snapshot_sources(REPOSITORY_ROOT, manifest))
    cell = next(
        item for item in matrix["rows"][0]["cells"] if item["surface"] == "typescript"
    )
    assert cell["state"] == "ALIGNED"
    assert cell["observed"] == "memMb"
