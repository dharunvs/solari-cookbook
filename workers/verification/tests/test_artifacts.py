from pathlib import Path
from uuid import uuid4

import pytest
from noxyn_verification_worker.artifacts import ArtifactStoreError, LocalArtifactStore


def test_local_artifacts_are_idempotent_and_hash_verified(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path)
    workspace_id, run_id = uuid4(), uuid4()
    first = store.put(
        workspace_id=workspace_id,
        run_id=run_id,
        kind="readiness",
        body=b'{"status":"ready"}',
    )
    replay = store.put(
        workspace_id=workspace_id,
        run_id=run_id,
        kind="readiness",
        body=b'{"status":"ready"}',
    )
    assert replay == first
    assert store.read(first) == b'{"status":"ready"}'

    (tmp_path / first.object_key).write_bytes(b"tampered")
    with pytest.raises(ArtifactStoreError, match="byte length|checksum"):
        store.read(first)
