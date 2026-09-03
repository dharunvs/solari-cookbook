# Noxyn-Solari repository guidance

## Current state

This repository currently contains the Solari cookbook examples and the
Noxyn-Solari MVP specifications. The application scaffold described below may
not exist yet. Do not invent commands or pretend an uncreated service is
available; inspect the tree before acting.

## Sources of truth

Use these sources in order when they conflict:

1. The current user request.
2. `noxyn_solari/docs/implementation-decisions.md` for locked technology,
   package, fixture, persistence, and deployment choices.
3. `noxyn_solari/docs/finalized-mvp.md` for architecture and scope.
4. `noxyn_solari/docs/mvp-ux-lifecycle.md` for routes and user experience.
5. `DESIGN.md` for visual tokens and design character.
6. Version-matched framework documentation and installed package behavior.
7. Cookbook examples as candidate consumer evidence, not unquestionable API
   truth.

Do not expand the MVP with Browser, Desktop, organizations, teams, arbitrary
repositories, automatic merges, package publication, or deployment unless the
user explicitly changes scope.

## Domain hierarchy

Preserve this ownership chain everywhere:

```text
Workspace
└── Project: Solari
    └── Product: Sandbox
        ├── immutable configuration versions
        ├── verification runs
        ├── findings
        └── proposals
```

Solari is a project. Sandbox is its first implemented product. Runs belong to
Sandbox and one exact Sandbox configuration, never directly to the project.

## Product truth

Keep these dimensions separate:

```text
Static:         ALIGNED | SUSPECTED | NOT_EXPECTED | UNVERIFIED
Infrastructure: PASS | FAIL
Subject:        PASS | FAIL | NOT_RUN
Finding:        SUSPECTED | REPRODUCED | FIX_PROPOSED |
                FIX_VERIFIED | DISMISSED | UNVERIFIED
```

- A subject is broken only when infrastructure passed and the subject failed.
- Infrastructure failure produces `UNVERIFIED`, not a product failure.
- A proposal is fixed only after a separate fresh sandbox passes.
- Noxyn may generate proposals but must not merge, publish, or deploy them.
- Controlled API-evolution fixtures must always be labelled as fixtures.

## Authentication and data isolation

- Clerk owns sign-in credentials and session handling.
- FastAPI verifies identity and performs object authorization.
- Scope every query through the authenticated workspace.
- Derive project, product, run, finding, proposal, and artifact relationships
  server-side. Client-provided IDs are locators, never ownership proof.
- Mutations require CSRF protection and idempotency where specified.
- Never expose `SOLARI_API_KEY` or another server secret to the browser.
- Do not persist secrets in commands, logs, errors, fixtures, or artifacts.

## Evidence and execution

- Pin exact source revisions and package versions for reproducible evidence.
- Treat source snapshots and terminal evidence as immutable and content-hashed.
- Use a fresh Solari Sandbox per language and verification phase.
- Bound commands by timeout, output size, and an explicit execution plan.
- Redact captured output before persistence.
- Always clean up verification and subject sandboxes in `finally` paths.
- Retry infrastructure failures only within a small bound. A subject failure is
  evidence and must not be retried as infrastructure noise.

Use `$solari-sandbox-sdk` for Solari Sandbox SDK calls, verification harnesses,
package identities, and execution-result interpretation.

## Frontend

- Follow `DESIGN.md` for palette, typography, radii, spacing, and restrained
  elevation. It is inspiration, not a requirement to reproduce Vercel branding.
- The protected console is denser than a marketing page. Reserve large mesh
  gradients and extreme whitespace for authentication or onboarding.
- Use the local `tailwind-4-docs` skill for Tailwind v4 work. Confirm its docs
  snapshot is initialized and no older than one week before relying on it.
- Use `react-best-practices` when implementing or reviewing React/Next.js code.
- Use `web-design-guidelines` for accessibility and UX review.
- Prefer semantic HTML, visible focus, keyboard operation, useful labels, and
  reduced-motion support.
- Every data page needs loading, empty, authorization-failure, recoverable
  error, and narrow-screen states.
- URL state should preserve meaningful filters, selected runs, and deep links.

When Next.js is installed, read the bundled version-matched documentation at
`node_modules/next/dist/docs/` before changing framework code. Preserve any
Next.js-managed block that `next dev` adds to this file.

Use `next-dev-loop` after the console is runnable to inspect the live Next.js
server and verify relevant routes after edits.

## API and generated client

- FastAPI OpenAPI is the HTTP contract authority.
- The console must use the generated TypeScript client rather than handwritten
  duplicate request/response types.
- A changed OpenAPI document without a regenerated client must fail validation.
- Use fresh, minimal migrations; do not transplant the full `../noxyn`
  migration history.

## Testing and verification

- Test behavior and invariants rather than generated wording.
- Unit-test normalization, lifecycle transitions, hashing, redaction, and
  proposal ambiguity rejection.
- Integration-test workspace isolation, idempotency, job leases, recovery, and
  immutable artifact reads.
- Use the local `playwright-cli` skill for browser journeys once the console
  runs. Cover registration, resumable onboarding, project/product creation,
  run polling, evidence inspection, cancellation, session expiry, and mobile
  matrix cards.
- Live Solari tests must be opt-in, bounded, and cleanup-asserting. CI must have
  a deterministic replay path that does not require `SOLARI_API_KEY`.

## Working conventions

- Preserve unrelated user changes and existing cookbook examples unless the
  task explicitly changes them.
- Use `rg` and `rg --files` for discovery.
- Use the nearest package's documented commands; there is no root application
  command until the monorepo scaffold is created.
- Add narrow tests with each behavior change and report what was actually run.
