import hashlib
from pathlib import Path

import pytest
from noxyn_api.artifacts import (
    ArtifactRecord,
    ArtifactUnavailable,
    LocalArtifactReader,
)


def test_local_reader_verifies_identity_and_rejects_escape(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    body = b'{"fixture":true}'
    path = root / "matrix.json"
    path.write_bytes(body)
    reader = LocalArtifactReader(root)
    record = ArtifactRecord(
        object_key="matrix.json",
        sha256=hashlib.sha256(body).hexdigest(),
        byte_length=len(body),
    )
    assert reader.read(record) == body

    path.write_bytes(b"tampered")
    with pytest.raises(ArtifactUnavailable, match="length|checksum"):
        reader.read(record)

    outside = tmp_path / "outside.json"
    outside.write_bytes(body)
    with pytest.raises(ArtifactUnavailable, match="unavailable"):
        reader.read(
            ArtifactRecord(
                object_key="../outside.json",
                sha256=hashlib.sha256(body).hexdigest(),
                byte_length=len(body),
            )
        )
