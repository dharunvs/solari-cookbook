"""Immutable, content-addressed artifact storage for local development."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID


class ArtifactStoreError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    object_key: str
    sha256: str
    byte_length: int


class ArtifactStore(Protocol):
    def put(
        self, *, workspace_id: UUID, run_id: UUID, kind: str, body: bytes
    ) -> ArtifactReference: ...

    def read(self, reference: ArtifactReference) -> bytes: ...


class LocalArtifactStore:
    """Exclusive local writes and hash-verified reads.

    The content hash makes a retry return the same immutable object rather than
    creating duplicate evidence after a worker interruption.
    """

    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        if root.is_symlink() or not root.is_dir():
            raise ArtifactStoreError("artifact root must be a real directory")
        self._root = root.resolve(strict=True)

    def put(
        self, *, workspace_id: UUID, run_id: UUID, kind: str, body: bytes
    ) -> ArtifactReference:
        digest = hashlib.sha256(body).hexdigest()
        object_key = f"workspaces/{workspace_id}/runs/{run_id}/{kind}/{digest}.json"
        reference = ArtifactReference(object_key, digest, len(body))
        path = self._path(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._require_safe_parents(path)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(path, flags, 0o600)
        except FileExistsError:
            self.read(reference)
            return reference
        try:
            with os.fdopen(descriptor, "wb") as target:
                target.write(body)
                target.flush()
                os.fsync(target.fileno())
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        self.read(reference)
        return reference

    def read(self, reference: ArtifactReference) -> bytes:
        path = self._path(reference.object_key)
        if not path.is_file() or path.is_symlink():
            raise ArtifactStoreError("artifact is unavailable")
        body = path.read_bytes()
        if len(body) != reference.byte_length:
            raise ArtifactStoreError("artifact byte length does not match")
        if hashlib.sha256(body).hexdigest() != reference.sha256:
            raise ArtifactStoreError("artifact checksum does not match")
        return body

    def _path(self, object_key: str) -> Path:
        candidate = self._root.joinpath(*object_key.split("/"))
        if self._root not in candidate.parents:
            raise ArtifactStoreError("artifact path escapes its root")
        return candidate

    def _require_safe_parents(self, path: Path) -> None:
        current = path.parent
        while current != self._root:
            if current.is_symlink():
                raise ArtifactStoreError("artifact path contains a symlink")
            current = current.parent
