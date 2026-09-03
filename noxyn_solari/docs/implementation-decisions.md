# Noxyn-Solari MVP implementation decisions

- Status: Accepted
- Decision date: 2026-09-02
- Applies to: MVP repository scaffold and implementation
- Product scope: Solari project, Sandbox product only

This document resolves the implementation choices that must be fixed before
application code is scaffolded. It takes precedence over illustrative package
names, version placeholders, and deployment options in older MVP documents.

The governing product statement remains:

> Noxyn finds the drift. Solari proves it.

## 1. Locked scope

The MVP contains:

```text
authenticated user
  -> one private workspace
      -> project: Solari
          -> product: Sandbox
              -> immutable configurations
              -> verification runs
              -> findings
              -> fix proposals
              -> fresh-sandbox re-verification
```

The following are explicitly not part of this implementation:

- Browser or Desktop products.
- Organizations, teams, invitations, or role management.
- Arbitrary user-supplied repositories.
- GitHub Apps, repository write access, or pull-request creation.
- Temporal or another external workflow orchestrator.
- Automatic merges, package publication, or deployment.
- Scheduled or recurring verification.

No scaffold should create placeholder services, routes, tables, navigation, or
permissions for this deferred scope.

## 2. Repository and runtime baseline

Use one monorepo with two language toolchains:

```text
pnpm workspace
  apps/console                 Next.js application
  packages/generated-client   generated TypeScript API client

uv workspace
  services/api                 FastAPI service
  workers/verification         PostgreSQL queue consumer and analysis
```

Initial runtime and package pins:

| Concern | Accepted choice | Initial exact pin |
|---|---|---:|
| Web framework | Next.js App Router | `16.3.4` |
| UI runtime | React and React DOM | `19.2.8` |
| Styling | Tailwind CSS and PostCSS adapter | `4.3.3` |
| Web authentication adapter | `@clerk/nextjs` | `7.8.4` |
| API framework | FastAPI | `0.141.1` |
| Validation | Pydantic | `2.13.5` |
| ORM and migrations | SQLAlchemy and Alembic | `2.0.52`, `1.19.1` |
| PostgreSQL driver | `psycopg[binary]` | `3.3.5` |
| ASGI server | `uvicorn[standard]` | `0.52.4` |
| Clerk API verification | `clerk-backend-api` | `7.0.0` |
| Client schema generator | `openapi-typescript` | `7.13.0` |
| Generated client runtime | `openapi-fetch` | `0.17.0` |

These are exact starting pins, not floating minimums. Dependency upgrades are
separate reviewed changes that regenerate locks and run the full verification
suite. The scaffold uses Node.js 22 LTS and Python 3.12.

The pins were checked against the npm and PyPI registries on the decision date.
The matching implementation in `../noxyn` is a reuse source for patterns, but
its dependency versions do not override this table.

## 3. Console decision

Build `apps/console` with Next.js 16.3.4, React 19.2.8, and Tailwind CSS
4.3.3. Use the App Router and Server Components by default. Add Client
Components only where interaction or browser APIs require them.

The console is a protected product application, not a marketing site. Its
initial routes cover authentication, resumable onboarding, project/product
configuration, run history, run detail, evidence, findings, proposals, and
fresh verification.

The console must not hand-maintain FastAPI DTOs. Server-side console modules
call the API through `@noxyn/generated-client`. Browser code calls same-origin
Next.js boundaries; it does not receive the FastAPI base URL or a Solari API
key.

Tailwind uses the v4 CSS-first configuration model. Design tokens come from
the repository's `DESIGN.md`; no compatibility Tailwind v3 configuration is
added.

## 4. Authentication decision

Clerk owns credentials, email verification, sessions, sign-in, and sign-out.
Use Clerk email one-time-code sign-up/sign-in for the MVP. Do not enable Clerk
Organizations.

Authentication and authorization are deliberately separate:

```text
Clerk session
  -> Next.js obtains a short-lived Clerk token
  -> generated client sends Authorization: Bearer <token>
  -> FastAPI verifies signature, issuer, audience, and expiry
  -> FastAPI maps Clerk subject to local user and workspace
  -> every resource query is scoped through that workspace
```

On first authenticated API access, create the local user and exactly one
private workspace in one idempotent transaction. Project and product IDs from
the client are locators only; they never prove ownership.

Mutation requests use a same-origin console boundary, an explicit idempotency
key, and API-side authorization. FastAPI exposes no wildcard production CORS
policy. Clerk secrets and `SOLARI_API_KEY` exist only in server/worker secret
environments.

## 5. API and generated TypeScript client

FastAPI/Pydantic is the HTTP contract authority. Use explicit operation IDs and
purpose-built request/response models rather than exposing SQLAlchemy models.

The generation path is:

```text
FastAPI routes + Pydantic models
  -> deterministic services/api/openapi.json
  -> openapi-typescript
  -> packages/generated-client/src/schema.d.ts
  -> small reviewed openapi-fetch wrapper
  -> @noxyn/generated-client
```

Both the OpenAPI document and generated client are committed. CI fails when
regeneration produces a diff. There is no handwritten duplicate TypeScript
API model layer.

Use REST plus polling for run progress in the MVP. Do not add WebSockets,
server-sent events, GraphQL, or a second API gateway.

## 6. PostgreSQL decision

PostgreSQL is the only application database. It stores identity mappings,
workspace ownership, onboarding state, projects, products, immutable product
configuration versions, runs, jobs, executions, findings, proposals, and
artifact metadata.

Use SQLAlchemy 2 asynchronous sessions, psycopg 3, and Alembic. Start with a
new minimal migration history; do not copy the migration history from
`../noxyn`.

Required database behaviors include:

- Foreign keys encode the Workspace -> Project -> Product ownership chain.
- Workspace scoping is present on every resource lookup.
- Configuration versions and terminal execution evidence are append-only.
- Idempotency keys have database uniqueness constraints.
- Timestamps are timezone-aware UTC.
- Status fields use constrained values matching the MVP state dimensions.

Do not add pgvector, Redis, Elasticsearch, or a document database for the MVP.

## 7. PostgreSQL-backed job queue

Use a first-party `verification_jobs` table and a dedicated Python worker. Do
not add Redis, Celery, Temporal, or a hosted queue.

Claiming uses a short transaction with `SELECT ... FOR UPDATE SKIP LOCKED`.
Each claim writes a lease owner, lease expiry, heartbeat time, and attempt
number. The worker performs slow work outside the claim transaction. Expired
leases are recoverable.

Queue rules:

```text
API transaction
  -> create verification_run
  -> create verification_job
  -> commit both or neither

worker
  -> atomically claim one eligible job
  -> heartbeat while executing
  -> persist append-only attempt evidence
  -> mark terminal state idempotently
```

Use bounded polling with jitter. A one-second idle polling baseline is enough
for the MVP. Retry infrastructure failures at most three attempts with bounded
backoff. Never retry a subject failure as infrastructure noise. Cancellation
is cooperative and checked between stages and before each new Solari sandbox.

This queue is intentionally small and inspectable. Revisit it only after
measured throughput or operational needs exceed PostgreSQL leasing.

## 8. Artifact storage

All artifact access goes through one `ArtifactStore` interface with immutable
`put`, verified `get`, and existence operations. Artifact metadata stays in
PostgreSQL; artifact bytes do not.

### Development

Use a filesystem store rooted at:

```text
<repository>/.noxyn/artifacts
```

The directory is gitignored. Writes go to a temporary file, are hashed, and
are atomically renamed into a content-addressed path. An existing object with
different bytes is an error.

### Production

Use one private Cloudflare R2 bucket through its S3-compatible API:

```text
noxyn-solari-artifacts-production
```

Object keys are content addressed and workspace partitioned:

```text
workspaces/<workspace-id>/sha256/<first-two>/<full-sha256>
```

The API and worker receive scoped R2 credentials from their hosting secret
stores. The bucket has no public access. Downloads pass through an authorized
API response or a short-lived signed URL created only after workspace
authorization. Every read verifies recorded byte length and SHA-256. Logs,
stdout, and stderr are redacted and bounded before upload.

The interface stays S3-compatible so AWS S3 can replace R2 without changing
domain code. Production must never fall back to ephemeral local disk.

## 9. Solari SDK package identities

The canonical Sandbox SDK artifacts for the first configuration are:

| Language | Registry identity | Exact version | Import identity |
|---|---|---:|---|
| Python | PyPI `solari-sandbox` | `0.2.0` | `solari_sandbox` |
| TypeScript | npm `@solarisdk/sandbox` | `0.1.2` | `@solarisdk/sandbox` |
| Go | Go module `github.com/solari-sdk/solari-sandbox-go` | `v0.1.2` | package `solari` |

The TypeScript cookbook currently depends on the umbrella package
`@solarisdk/sdk@0.1.2`, which re-exports Sandbox. Preserve that as the example's
dependency evidence, but use `@solarisdk/sandbox@0.1.2` as the canonical
TypeScript SDK matrix column. Do not rewrite the example merely to make these
identities identical.

Registry resolution checked on 2026-09-02:

- npm publishes both `@solarisdk/sdk@0.1.2` and
  `@solarisdk/sandbox@0.1.2`.
- PyPI publishes `solari-sandbox==0.2.0`.
- The Go module proxy publishes
  `github.com/solari-sdk/solari-sandbox-go@v0.1.2`, backed by Git commit
  `15ae65c3177f4eeb270e000f5065787abe581e0f`.

Every run records the exact package identity, resolved artifact checksum,
source revision, source SHA-256, and retrieval timestamp. No `^`, `~`, `>=`,
`latest`, branch, or untagged revision is allowed in verification evidence.

## 10. Controlled API-evolution fixture

The controlled scenario is named `sandbox-create-evolution`. It is always
displayed as a fixture and never as evidence of a current Solari defect.

The fixture has two immutable contract snapshots:

| Fixture artifact | Version | `sandbox.create` memory field |
|---|---:|---|
| `contract-before.json` | `1.0.0` | generic stale name `memory` |
| `contract-after.json` | `2.0.0` | canonical wire name `memMb` |

The after-contract maps one semantic capability to real SDK spellings:

```text
canonical capability: sandbox.create.memory_mb
wire JSON:             memMb
Python 0.2.0:          mem_mb
TypeScript 0.1.2:      memMb
Go v0.1.2:             MemMb
```

The controlled runtime package vector is fixed:

```text
fixture package vector: sandbox-create-evolution-packages/1.0.0
Python:                 solari-sandbox==0.2.0
TypeScript SDK:         @solarisdk/sandbox@0.1.2
TypeScript example:     @solarisdk/sdk@0.1.2
Go:                     github.com/solari-sdk/solari-sandbox-go@v0.1.2
```

The stale Python and documentation fixture artifacts call
`sandbox.create(..., memory=2048)`. Static comparison must mark them
`SUSPECTED`. A Python harness using the pinned package must reproduce the
unexpected keyword failure after infrastructure passes. The proposal changes
only the source-bound occurrence to `mem_mb=2048`; a separate fresh sandbox
must pass before the finding becomes `FIX_VERIFIED`.

TypeScript and Go aligned fixture artifacts use `memMb` and `MemMb`
respectively. They demonstrate cross-language equivalence and must not be
reported as drift because their casing differs.

Checked-in fixture files, downloaded package artifacts, execution plans, and
expected deterministic replay evidence are content-hashed. CI uses replay
evidence and does not require `SOLARI_API_KEY`; opt-in live verification uses
the same package vector.

## 11. Hosting targets

Use these production targets:

| Component | Hosting target | Deployment unit |
|---|---|---|
| Console | Vercel | `apps/console`, Next.js deployment |
| API | Railway | containerized `services/api` service |
| Worker | Railway | containerized worker service from the same Python workspace/image family |
| Database | Railway PostgreSQL | private managed PostgreSQL instance |
| Artifacts | Cloudflare R2 | private S3-compatible bucket |

The API and worker share no local disk and communicate through PostgreSQL and
R2. They are separate processes so worker load cannot consume API request
capacity. Railway private networking is used between API, worker, and database.

Production configuration is environment-based:

```text
Console
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  CLERK_SECRET_KEY
  NOXYN_API_BASE_URL

API
  DATABASE_URL
  CLERK_SECRET_KEY / Clerk issuer and audience configuration
  R2 endpoint, bucket, access key, secret key

Worker
  DATABASE_URL
  SOLARI_API_KEY
  R2 endpoint, bucket, access key, secret key
```

`SOLARI_API_KEY` is worker-only. Vercel never receives it. Deployment runs
database migrations as an explicit release command before new API/worker code
serves traffic. One worker replica ships first; the lease protocol permits
additional replicas without a queue redesign.

Preview environments may use separate Clerk development credentials and an
isolated database, but they must not share the production artifact bucket
write credentials.

## 12. Reuse boundary from `../noxyn`

Reuse or adapt these proven patterns:

- pnpm/uv monorepo organization and exact lock discipline.
- Clerk identity adapter and FastAPI authorization boundary.
- FastAPI OpenAPI export plus generated TypeScript client workflow.
- SQLAlchemy session, migration, and repository patterns.
- Artifact interface, hashing, redaction, and immutable evidence conventions.
- Deterministic extractors, normalization, matrix, and proposal concepts.
- Protected console layout and error/loading-state patterns.

Do not copy:

- Temporal workflow integration.
- Fargate execution infrastructure.
- Organization/team data models.
- GitHub App, pull-request, publication, or delivery workflows.
- Marketing/public-audit applications and their migrations.
- The full historical migration chain.

Reuse is selective source adaptation, not a wholesale repository copy.

## 13. Scaffold acceptance gate

All implementation decisions required by the scaffold are closed:

- [x] Next.js 16.3+, React 19, and Tailwind 4 versions selected.
- [x] Clerk authentication flow and authorization boundary selected.
- [x] FastAPI contract authority and TypeScript generation toolchain selected.
- [x] PostgreSQL access and migration strategy selected.
- [x] Local development artifact path and immutability behavior selected.
- [x] Durable production object store and access policy selected.
- [x] PostgreSQL-backed queue claim, lease, retry, and cancellation behavior selected.
- [x] Python, TypeScript, and Go package identities and exact versions selected.
- [x] Controlled API-evolution fixture versions and parameter mapping selected.
- [x] Console, API, worker, database, and artifact hosting targets selected.
- [x] Deferred product and infrastructure scope explicitly excluded.

```text
All implementation decisions are recorded.
No unresolved choice blocks the repository scaffold.
```
