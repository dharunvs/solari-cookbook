---
name: solari-sandbox-sdk
description: Implement, review, or diagnose Solari Sandbox SDK integrations and Noxyn verification harnesses in Python, TypeScript, or Go. Use for sandbox lifecycle, commands, files, code execution, previews, exact package installation, cleanup, or execution-evidence interpretation. Do not use for Solari Browser or Desktop work.
---

# Solari Sandbox SDK

Use current installed-package behavior and evidence instead of assuming a
cookbook example is still correct. Noxyn exists to detect when those examples
drift.

## Start here

1. Identify the language, exact package, requested capability, and whether the
   task is consumer integration or Noxyn verification infrastructure.
2. Read [references/local-sdk-map.md](references/local-sdk-map.md) for local
   package identities, examples, and known caveats.
3. Read only the relevant local example. Treat it as a candidate consumer
   artifact, not API authority.
4. Verify the API against the exact installed/pinned package or an approved
   source snapshot before changing production logic.
5. If the task concerns Noxyn result semantics, also read
   `noxyn_solari/docs/finalized-mvp.md`.

## Authority order

For SDK shape and behavior, prefer:

1. Exact installed package behavior and type information.
2. Approved, pinned Solari SDK documentation/source snapshot.
3. Published package documentation for the same version.
4. Cookbook examples as the subject being evaluated.

If these disagree, record the versioned disagreement. Do not silently update
the expected side to match the artifact under test.

## Integration invariants

- Keep `SOLARI_API_KEY` in server or worker secret environments. Never send it
  to browser code or persist it in artifacts.
- Pin exact package versions when producing verification evidence. A permissive
  range is acceptable for a human-facing example only when reproducibility is
  not being claimed.
- Prefer executable-plus-argv command APIs. Do not assume command strings are
  shell-interpreted.
- Connect only when the selected SDK capability requires a control channel.
- Destroy the remote VM with the SDK's kill operation in a `finally` path.
  Closing a local client/channel is not evidence that the VM was destroyed.
- Put a ceiling on runtime and captured output. Treat rolling idle timeouts and
  hard controller deadlines as different concepts.
- Do not infer Go API spelling from Python or TypeScript. Mark it unverified
  until checked against the exact Go module.

## Noxyn verification harnesses

- Materialize the exact source bytes and record their SHA-256.
- Install the exact registry package version in a fresh verification sandbox.
- Record infrastructure state independently from the executed subject state.
- Infrastructure `FAIL` means subject `NOT_RUN`; it does not reproduce drift.
- Subject `FAIL` after infrastructure `PASS` can establish `REPRODUCED`.
- Capture exit code, bounded/redacted stdout and stderr, package identity,
  sandbox identity, duration, source hash, and cleanup outcome.
- A fix proposal is verified only by a separate attempt in a new sandbox using
  the same exact package version.
- Preserve failed attempts and partial evidence rather than overwriting them.

## Stop conditions

Do not guess a method, field, package, or cleanup behavior when current
versioned evidence is unavailable. Return `UNVERIFIED`, state what source is
missing, and identify the smallest check needed to continue.
