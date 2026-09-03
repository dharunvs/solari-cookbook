"""Authorized, hash-verifying reads from the local development artifact store."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


class ArtifactUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    object_key: str
    sha256: str
    byte_length: int


class LocalArtifactReader:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def read(self, artifact: ArtifactRecord) -> bytes:
        try:
            path = self.root.joinpath(*artifact.object_key.split("/")).resolve(
                strict=True
            )
        except OSError:
            raise ArtifactUnavailable("artifact is unavailable") from None
        if self.root not in path.parents or not path.is_file() or path.is_symlink():
            raise ArtifactUnavailable("artifact is unavailable")
        body = path.read_bytes()
        if len(body) != artifact.byte_length:
            raise ArtifactUnavailable("artifact length does not match")
        if hashlib.sha256(body).hexdigest() != artifact.sha256:
            raise ArtifactUnavailable("artifact checksum does not match")
        return body

    def put(
        self, *, workspace_id: object, run_id: object, kind: str, body: bytes
    ) -> ArtifactRecord:
        """Write one immutable content-addressed artifact for API proposals."""
        digest = hashlib.sha256(body).hexdigest()
        object_key = f"workspaces/{workspace_id}/runs/{run_id}/{kind}/{digest}.json"
        path = self.root.joinpath(*object_key.split("/"))
        if self.root not in path.parents:
            raise ArtifactUnavailable("artifact path escapes its root")
        path.parent.mkdir(parents=True, exist_ok=True)
        current = path.parent
        while current != self.root:
            if current.is_symlink():
                raise ArtifactUnavailable("artifact path contains a symlink")
            current = current.parent
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        record = ArtifactRecord(object_key, digest, len(body))
        try:
            descriptor = os.open(path, flags, 0o600)
        except FileExistsError:
            self.read(record)
            return record
        try:
            with os.fdopen(descriptor, "wb") as target:
                target.write(body)
                target.flush()
                os.fsync(target.fileno())
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        self.read(record)
        return record
