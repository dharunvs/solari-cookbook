# API guidance

These rules apply to the FastAPI service and its persistence boundary.

- Read the root `AGENTS.md` and `noxyn_solari/docs/finalized-mvp.md` first.
- FastAPI OpenAPI is authoritative. Regenerate the TypeScript client whenever
  the contract changes and fail validation on drift.
- Verify Clerk tokens server-side and derive the workspace principal there.
- Scope every read and mutation by workspace. Resolve the ownership chain
  workspace → project → product → configuration/run on the server.
- Never accept a workspace ID, owner ID, or parent-child relationship from the
  request body as authorization proof.
- Require CSRF protection and idempotency keys for relevant mutations.
- Keep configurations, terminal results, evidence, and proposal bindings
  immutable. Editing Sandbox settings creates a new configuration version.
- Store ownership, state, indexes, leases, and artifact references in
  PostgreSQL. Store artifact bodies behind the immutable `ArtifactStore`
  interface and verify their hashes on read.
- Redact and size-limit stdout/stderr before persistence. Secrets are never
  artifacts or API response fields.
- Use explicit typed states. Do not collapse `UNVERIFIED`, `NOT_RUN`, and
  `FAIL` into one boolean.
- Keep migrations minimal and forward-only. Do not copy the historical Noxyn
  migration chain.
- Test cross-workspace denial, opaque not-found responses, idempotent retries,
  configuration/run ownership, and stale proposal source hashes.

