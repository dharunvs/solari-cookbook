import pytest
from noxyn_api.proposal_engine import (
    ProposalRejected,
    extract_python_fence,
    propose_memory_rename,
)


def test_python_proposal_is_minimal_and_parseable() -> None:
    source = b"async def main(client):\n    await client.create(memory=2048)\n"
    proposal = propose_memory_rename(source, surface="python", path="main.py")
    assert proposal.proposed == (
        b"async def main(client):\n    await client.create(mem_mb=2048)\n"
    )
    assert proposal.changed_lines == 2
    assert b"-    await client.create(memory=2048)" in proposal.patch
    assert b"+    await client.create(mem_mb=2048)" in proposal.patch


def test_markdown_proposal_changes_only_the_single_python_fence() -> None:
    source = b"Guide\n\n```python\nclient.create(memory=1)\n```\n"
    proposal = propose_memory_rename(source, surface="docs_python", path="README.md")
    assert extract_python_fence(proposal.proposed) == b"client.create(mem_mb=1)\n"
    assert proposal.proposed.startswith(b"Guide\n\n```python\n")


@pytest.mark.parametrize(
    "source",
    [
        b"client.create(memory=1)\nclient.create(memory=2)\n",
        b"client.create(mem_mb=1)\n",
        b"client.create(memory = 1)\n",
    ],
)
def test_ambiguous_or_non_exact_python_change_is_rejected(source: bytes) -> None:
    with pytest.raises(ProposalRejected):
        propose_memory_rename(source, surface="python", path="main.py")


def test_multiple_documentation_fences_are_rejected() -> None:
    source = b"```python\nclient.create(memory=1)\n```\n```python\npass\n```\n"
    with pytest.raises(ProposalRejected, match="exactly one Python fence"):
        propose_memory_rename(source, surface="docs_python", path="README.md")
