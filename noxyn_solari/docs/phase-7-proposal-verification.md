# Phase 7 — Source-Bound Proposal Verification

Phase 7 completes the MVP lifecycle for the controlled API-evolution fixture:

```text
SUSPECTED → REPRODUCED → FIX_PROPOSED → FIX_VERIFIED
```

The implementation deliberately targets the 2 real controlled findings:

```text
Python executable example      memory= → reproduced failure
Python documentation block     memory= → reproduced failure
TypeScript executable example  memMb=  → aligned pass; no proposal
```

This corrects the older roadmap sentence that called for a TypeScript finding.
Generating drift for an aligned surface would violate Noxyn's truth model.

## Proposal contract

The API accepts proposal creation only for a workspace-scoped `REPRODUCED`
finding. Its deterministic rule:

1. Reads the immutable source artifact through a hash- and length-verifying
   artifact boundary.
2. Requires either Python source or exactly 1 Python Markdown fence.
3. Parses the Python bytes and requires exactly 1 `create(memory=...)`
   candidate.
4. Replaces only the exact `memory=` token with `mem_mb=`.
5. Parses and validates the proposed bytes.
6. Stores the proposed source and unified diff as immutable content-addressed
   artifacts.
7. Binds the proposal to both original and proposed SHA-256 identities.

Zero candidates, multiple candidates, invalid syntax, non-exact token layout,
unsupported surfaces, missing artifacts, and hash mismatches fail closed. The
operation is idempotent and does not write to the repository checkout.

## Fresh verification

```text
POST proposal/verify
        │
        ▼
PostgreSQL FIX_VERIFICATION job
        │ lease + bounded retries for infrastructure only
        ▼
validate original/proposed artifact hashes
        │
        ▼
ExecutionRequest phase=FIX_VERIFY
        │ same exact package version
        │ exact proposed bytes
        ▼
fresh Solari Sandbox (live) or labelled replay (CI/dev)
        │
   ┌────┴────┐
   ▼         ▼
 PASS       FAIL / UNVERIFIED
   │         │
   ▼         ▼
FIX_VERIFIED FIX_PROPOSED remains
```

Live execution creates a new outer Solari Sandbox for every proposal. It
installs `solari-sandbox==0.2.0`, materializes the exact proposed executable
bytes, executes with argv-only bounded commands, redacts and caps output, and
cleans up in `finally`. Documentation verification executes the exact single
Python block extracted from the proposed Markdown artifact. Its extracted
bytes receive their own immutable execution-source hash.

A passing subject is insufficient when infrastructure or cleanup fails. The
proposal and finding advance only when all 3 are `PASS`. The original
reproduction execution remains immutable and independently inspectable.

## Persistence and API

Migration `0007_fix_proposals` adds:

- `proposals`, with workspace/run/finding ownership and immutable artifact
  references;
- `verification_jobs.proposal_id` for separately leased fix jobs;
- `execution_attempts.proposal_id`, `source_surface`, and `FIX_VERIFY` phase;
- independent uniqueness for initial subject attempts and proposal attempts.

Workspace-scoped endpoints:

```text
POST /v1/findings/{finding_id}/proposals
GET  /v1/runs/{run_id}/proposals
GET  /v1/proposals/{proposal_id}
POST /v1/proposals/{proposal_id}/verify
```

Mutations require same-origin CSRF evidence and idempotency keys. Ownership is
derived server-side; guessed cross-workspace identifiers return the opaque
`resource unavailable` response. The FastAPI OpenAPI document remains the
contract authority and the console uses its regenerated TypeScript client.

## User experience

The finding page now moves through 3 concrete states:

```text
REPRODUCED
  Generate proposal
      ↓
FIX_PROPOSED
  exact unified diff + before/after hashes
  Verify proposed fix
      ↓
FIX_VERIFIED
  before failure + fresh passing evidence + cleanup result
```

Polling is limited to an active proposal job. Users can leave the page while
the durable worker continues. Every proposal screen explicitly says that
Noxyn did not modify the checkout, open a PR, merge, publish, or deploy. The run
summary reports `2 / 2 VERIFIED` only after both independent proposal
executions pass.

## Reuse decision

`../noxyn` was inspected for proposal and remediation logic. Its contracts are
designed for multi-repository release planning, approvals, archives, receipts,
PR handoff, and publication boundaries. Importing those systems would make
this fixed-manifest MVP larger and less reliable. Phase 7 therefore reuses the
local Phase 4–6 artifact, queue, executor, truth-state, API, and console paths;
no implementation was copied from `../noxyn`.

## Verification coverage

- Unit tests reject ambiguous, missing, malformed, and non-exact changes.
- Integration tests cover both proposals, idempotent creation, fresh job
  execution, phase separation, final lifecycle state, evidence, and
  cross-workspace denial.
- Playwright covers review, generation, polling, both fix verifications,
  evidence messaging, final summary, and narrow-screen matrix cards.
- Live Solari remains opt-in. Deterministic replay keeps ordinary CI reliable
  without `SOLARI_API_KEY`.
