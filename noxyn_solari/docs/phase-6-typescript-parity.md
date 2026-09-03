# Phase 6 — TypeScript Runtime Parity

Phase 6 extends the Phase 5 verification path; it does not introduce another
pipeline. A run snapshots and statically analyzes all controlled sources, then
submits one Python request and one TypeScript request through the same
`VerificationExecutor` protocol.

## Controlled result

```text
Sandbox.create memory field
├── Python     solari-sandbox==0.2.0       memory   → FAIL
└── TypeScript @solarisdk/sandbox@0.1.2    memMb    → PASS

Infrastructure: PASS for both
Parity: DIFFERENT
```

This is a controlled API-evolution fixture, not a claim that a current Solari
release is defective.

## Execution contract

Both languages bind immutable evidence to:

- language;
- exact package name and version;
- exact source path and SHA-256;
- reviewed command-plan SHA-256;
- bounded timeout and output size;
- infrastructure and subject outcomes;
- exit code, redacted stdout/stderr, duration, sandbox identity, and cleanup;
- an explicit `REPLAY` or `SOLARI` backend.

The language-specific command plans are data selected inside the executor:

```text
Python
  install: python -m pip install ... solari-sandbox==0.2.0
  execute: python /tmp/noxyn_subject.py

TypeScript
  install: npm install --prefix /tmp/noxyn-typescript ...
           @solarisdk/sandbox@0.1.2
  execute: node /tmp/noxyn-typescript/subject.mjs
```

Commands remain executable-plus-argv. The npm install disables lifecycle
scripts, audit, and funding network work. Each live language attempt creates
and cleans up a separate outer Solari Sandbox.

## Persistence and findings

`execution_attempts.language` accepts `python` and `typescript`. Attempts are
unique per run, language, phase, and attempt number. `finding_id` is nullable
because an aligned passing subject is valid execution evidence without a drift
finding. Finding lifecycle changes only when an execution is bound to a real
finding.

An infrastructure failure remains `Infrastructure FAIL / Subject NOT_RUN`.
Only successful infrastructure results participate in parity:

```text
both subject states equal       → MATCH
both verified but states differ → DIFFERENT
missing or infrastructure fail  → INCOMPLETE
```

## API and console

The capability matrix preserves its Phase 4 static cells and adds
`runtimeCells` for Python and TypeScript plus a top-level `parity` summary.
The legacy Python `runtime` field remains during this MVP transition. Execution
detail routes support both languages; a passing TypeScript execution links
back to the run instead of inventing a finding.

The console shows:

- independent runtime cells on desktop and mobile;
- infrastructure and subject truth separately;
- a Python-versus-TypeScript parity summary;
- deep links to both immutable execution evidence records;
- explicit fixture and replay/live labels.

## Reuse decision

`../noxyn` was searched for a compatible Solari executor or cross-language
parity implementation. It has no matching bounded Sandbox execution layer to
reuse. Pulling in its broader orchestration would increase coupling, so Phase 6
reuses the already-tested local Phase 5 executor, queue, artifact, API, and UI
contracts instead.
