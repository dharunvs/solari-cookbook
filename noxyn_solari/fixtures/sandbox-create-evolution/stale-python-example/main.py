"""Controlled stale fixture. It is intentionally not a current Solari example."""

from solari_sandbox import Sandbox


def create_sandbox() -> object:
    return Sandbox.create(memory=2048)
