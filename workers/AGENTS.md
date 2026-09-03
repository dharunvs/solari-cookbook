# Verification worker guidance

These rules apply to background jobs and Solari Sandbox execution.

- Read the root `AGENTS.md`, the finalized MVP architecture, and the local
  `$solari-sandbox-sdk` skill before changing execution behavior.
- Claim jobs with leases, heartbeat long work, and complete terminal state
  idempotently. Recovery must not duplicate findings or proposals.
- Build an explicit execution unit before contacting Solari: language, exact
  package, exact version, source hash, command plan, timeout, and evidence limit.
- Use a fresh verification sandbox per language and phase. If the artifact
  creates a Sandbox, treat it as a nested subject sandbox and clean up both.
- Keep infrastructure and subject results separate. Provisioning, transport,
  and controller failures produce infrastructure `FAIL` and subject `NOT_RUN`.
- A nonzero subject exit after successful infrastructure produces subject
  `FAIL` and may establish `REPRODUCED`.
- Do not interpolate unreviewed strings into a shell command. Prefer executable
  plus argv; use a shell only for reviewed harness behavior that requires it.
- Apply timeouts and output ceilings. Redact secrets before logs leave memory.
- Clean up in `finally`, record cleanup outcome separately, and never conceal a
  cleanup failure behind the subject result.
- Retry bounded infrastructure failures. Never automatically retry a subject
  failure as though it were infrastructure noise.
- Fix verification is a new attempt in a new sandbox against the same exact
  package version and source-bound proposal bytes.
- Live tests are opt-in and must assert cleanup. Deterministic replay remains
  the default for ordinary CI.

