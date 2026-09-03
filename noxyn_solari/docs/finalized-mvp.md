# Noxyn-Solari Finalized MVP

| Field                       | Value                                               |
| --------------------------- | --------------------------------------------------- |
| Status                      | Proposed implementation baseline                    |
| Product                     | Noxyn-Solari                                        |
| Scope                       | Authenticated Solari Sandbox ecosystem verification |
| Primary repository          | `solari-cookbook`                                   |
| Source/reference repository | `../noxyn`                                          |
| Last updated                | 2026-09-01                                          |

The complete registration-to-result screen lifecycle and text wireframes live
in [`mvp-ux-lifecycle.md`](./mvp-ux-lifecycle.md).

## 1. Purpose

Noxyn-Solari answers one product question:

> Does Solari Sandbox tell developers the same thing across its contract,
> published SDKs, documentation, and cookbook examples—and does the code users
> receive actually work in clean environments?

Noxyn owns understanding, comparison, findings, proposals, and final product
state. Solari Sandboxes provide disposable execution environments used to prove
or disprove suspected drift.

The governing product principle is:

> **Noxyn finds the drift. Solari proves it.**

This is an authenticated MVP, not a one-off demonstration script. It includes
durable user workspaces, background verification jobs, immutable evidence,
run history, and a protected application UI. It deliberately avoids the full
scope and operational complexity of the existing Noxyn platform.

## 2. Locked MVP scope

### 2.1 Included

- Clerk-backed authentication.
- One automatically provisioned workspace per authenticated user.
- One configured project: Solari.
- Sandbox added as Solari's first and only implemented MVP product.
- Workspace-scoped projects, products, and verification history.
- A configured, versioned source manifest.
- Canonical capability normalization.
- Static comparison of the contract, SDKs, docs, and examples.
- Published Python package inspection and execution.
- Published TypeScript package inspection and execution.
- Go represented in the schema from the beginning and implemented after the
  Python/TypeScript vertical slice, before V1 is declared complete.
- Fresh Solari Sandbox execution per language and verification phase.
- Infrastructure-versus-subject result separation.
- Persistent, content-hashed evidence.
- Conservative fix proposals for cookbook and documentation artifacts.
- Fresh-sandbox verification of proposed fixes.
- A protected console showing runs, matrix results, execution evidence, and
  proposal verification.
- A controlled, explicitly labelled API-evolution scenario.
- A configured current-Solari scan after the controlled path is reliable.

### 2.2 Deferred

- Browser and Desktop products.
- Rust and C++.
- Automatic company or source discovery.
- Arbitrary customer APIs.
- GitHub App installation and private repositories.
- Team invitations and multi-role membership.
- Multiple organizations per user.
- Automatic merges, package publication, or deployment.
- Temporal Cloud.
- AWS/Fargate execution.
- S3/KMS as a local-development requirement.
- Codex or another model as factual authority.
- General SDK generation.
- Public marketing, lead capture, email delivery, booking, and analytics.
- Recurring schedules and release operations.

### 2.3 Language delivery order

```text
Python vertical slice
        |
        v
TypeScript vertical slice
        |
        v
Cross-language report
        |
        v
Go extraction + execution
        |
        v
V1 complete
```

Python and TypeScript validate the complete architecture first because the
existing Noxyn implementation deeply supports those languages and the cookbook
already contains executable examples for both. Go must use the same contracts
and executor boundary; it must not introduce a second pipeline.

## 3. Product model

### 3.1 Ownership hierarchy

```text
Workspace
└── Project: Solari
    └── Product: Sandbox
        ├── configuration versions
        ├── source manifests
        ├── verification runs
        ├── findings
        └── proposals
```

Solari is the API ecosystem being managed. Sandbox is a product within that
ecosystem. Browser and Desktop may later become sibling products without
changing Sandbox configuration or historical runs.

### 3.2 Source model

```text
Solari
└── Sandbox
    ├── Contract
    │   └── configured API reference/capability snapshot
    ├── Official documentation
    │   ├── product guides
    │   └── language SDK references
    ├── Published SDK artifacts
    │   ├── Python: solari-sandbox
    │   ├── TypeScript: @solarisdk/sandbox
    │   └── Go: github.com/solari-sdk/solari-sandbox-go
    ├── Runnable consumer examples
    │   └── solari-cookbook
    └── Runtime evidence
        └── fresh Solari Sandboxes
```

Discovery is configured through a reviewed JSON manifest. The MVP does not
guess which websites, packages, or repositories belong to Solari.

### 3.3 Core unit: capability

The comparison unit is a semantic capability, not a whole package or page.

Examples:

```text
sandbox.create
sandbox.get
sandbox.list
sandbox.kill
commands.run
commands.start
files.read
files.write
files.search
code.run
git.clone
git.checkout
sandbox.snapshot
sandbox.preview_url
```

Language-specific spellings map to one capability:

```text
Canonical field     TypeScript     Python       Go
------------------------------------------------------
memory_mb           memMb          mem_mb       MemMB
preview_url         previewUrl     preview_url  PreviewURL
commands.run        commands.run   commands.run Commands.Run
```

Literal spelling differences are not findings when a reviewed deterministic
mapping declares them equivalent.

### 3.3 State dimensions

Do not overload one status with unrelated meanings.

Static matrix state:

```text
ALIGNED | SUSPECTED | NOT_EXPECTED | UNVERIFIED
```

Execution infrastructure state:

```text
PASS | FAIL
```

Executed subject state:

```text
PASS | FAIL | NOT_RUN
```

Finding lifecycle:

```text
SUSPECTED
REPRODUCED
FIX_PROPOSED
FIX_VERIFIED
DISMISSED
UNVERIFIED
```

Verification run state:

```text
QUEUED
→ SNAPSHOTTING
→ ANALYZING
→ VERIFYING
→ PROPOSING
→ REVERIFYING
→ COMPLETED

Any active state → CANCEL_REQUESTED → CANCELLED
Any active state → FAILED
```

`FIX_PROPOSED` is used instead of `FIXED` because Noxyn does not merge or
publish changes.

## 4. System architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                       Next.js Console                               │
│  Sign in | Runs | Matrix | Execution evidence | Proposal result    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ generated REST client
                               v
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI API                                 │
│ AuthN/AuthZ | Projects | Products | Config | Runs | Findings       │
└───────────────┬──────────────────────────────┬──────────────────────┘
                │                              │
                v                              v
┌───────────────────────────┐      ┌──────────────────────────────────┐
│ PostgreSQL                │      │ Immutable Artifact Store         │
│ ownership, state, jobs,   │      │ local filesystem first; hashes, │
│ references, idempotency   │      │ snapshots, logs, reports        │
└───────────────┬───────────┘      └────────────────┬─────────────────┘
                │                                   │
                └─────────────────┬─────────────────┘
                                  v
┌─────────────────────────────────────────────────────────────────────┐
│                    Noxyn Verification Worker                        │
│ snapshot → extract → normalize → compare → select execution units   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ VerificationExecutor
                               v
┌─────────────────────────────────────────────────────────────────────┐
│                    SolariSandboxExecutor                            │
│ create → materialize → install → execute → collect → kill          │
└──────────────────────────────┬──────────────────────────────────────┘
                               v
┌─────────────────────────────────────────────────────────────────────┐
│                     Solari Sandboxes                                │
│ Python consumer | TypeScript consumer | Go consumer | re-verifiers │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.1 Responsibility boundary

| Concern                    |             Noxyn | Solari Sandbox |
| -------------------------- | ----------------: | -------------: |
| Source configuration       |               Yes |             No |
| Contract normalization     |               Yes |             No |
| Capability mapping         |               Yes |             No |
| Static comparison          |               Yes |             No |
| Finding lifecycle          |               Yes |             No |
| Patch proposal             |               Yes |             No |
| Clean machine provisioning |                No |            Yes |
| Package installation       |          Plans it |    Executes it |
| Test command execution     |          Plans it |    Executes it |
| stdout/stderr capture      | Interprets/stores |       Produces |
| Evidence acceptance        |               Yes |             No |
| Product status             |               Yes |             No |

## 5. Reuse from `../noxyn`

The implementation should transplant a coherent product slice and adapt pure
analysis code. It should not copy the entire repository or create a second copy
of Noxyn's full SaaS architecture.

### 5.1 Reuse directly or with small adaptation

| Existing area            | Reuse                                                                                          |
| ------------------------ | ---------------------------------------------------------------------------------------------- |
| Clerk identity boundary  | Token verification, session-to-principal mapping, protected-route policy                       |
| FastAPI structure        | Application factory, validation boundary, dependency injection                                 |
| Generated client pattern | FastAPI OpenAPI as API authority and generated TypeScript consumer                             |
| Persistence patterns     | Workspace scoping, UUID identities, idempotency, job leases, immutable terminal facts          |
| Artifact-store interface | Immutable writes, hashes, byte length, verified reads                                          |
| Contract hashing         | Canonical JSON, SHA-256, stable evidence identities                                            |
| Contract comparison      | Directional before/after change classification                                                 |
| Static extractors        | Python calls/signatures, TypeScript declarations, documentation identifiers                    |
| Matrix concepts          | Evidence-backed cells, explicit unverified/not-expected states                                 |
| Proposal safety          | Exact source binding, ambiguity rejection, before/after hashes, unrelated-content preservation |
| Worker semantics         | Durable claim, lease, retry, completion, and recovery patterns                                 |
| UI design patterns       | Matrix table, status filters, evidence drawer, protected console shell                         |

### 5.2 Reuse as design guidance, not copied implementation

- Full contract-engine models: simplify them for one implemented product type
  and capability vocabulary.
- General ecosystem discovery: replace with one configured source manifest.
- Production remediation receipt hierarchy: retain evidence integrity but omit
  Fargate/KMS-specific attestations that Solari does not provide.
- Tenant model: retain workspace isolation without enterprise membership and
  invitation flows.
- Runtime verification UI: preserve its safety philosophy, but package/example
  verification is a separate feature from customer staging-API conformance.

### 5.3 Do not transplant

- Public acquisition product and marketing website.
- Resend, Cal.com, PostHog, and public-email workflows.
- GitHub App and connected private-source system.
- Temporal workflows.
- AWS/Fargate launcher and benchmark system.
- Release-candidate delivery and recurring operations.
- Full historical migration chain.
- Full documentation governance corpus.
- Existing design-research assets.

## 6. Repository structure

```text
solari-cookbook/
├── apps/
│   └── console/                    # protected Next.js product
├── services/
│   └── api/
│       ├── migrations/             # fresh minimal chain
│       └── src/noxyn_solari/
│           ├── auth/
│           ├── projects/
│           ├── products/
│           ├── configurations/
│           ├── runs/
│           ├── sources/
│           ├── capabilities/
│           ├── comparison/
│           ├── artifacts/
│           ├── verification/
│           ├── remediation/
│           └── routes/
├── workers/
│   └── src/noxyn_solari_worker/
├── packages/
│   └── generated-client/
├── noxyn_solari/
│   ├── docs/
│   ├── manifests/
│   └── fixtures/
│       └── sandbox-create-evolution/
└── examples/                       # original Solari cookbook examples
```

## 7. Authentication and authorization

### 7.1 MVP identity model

- Clerk owns authentication credentials and sign-in methods.
- Noxyn verifies Clerk tokens server-side.
- The first authenticated request provisions one workspace for the Clerk user.
- The workspace owns the Solari project. The project owns its Sandbox product;
  the product owns configurations and verification runs.
- Findings, proposals, executions, and artifact references remain reachable
  only through that workspace-scoped ownership chain.
- Every API query includes the authenticated workspace scope.
- Client-supplied workspace or owner IDs are never authority.

### 7.2 Authentication flow

```text
Visitor
  │
  ├── open protected route
  │       │
  │       └── no session ───────────────► /sign-in
  │
  └── Clerk sign-in
          │
          ▼
     Clerk session token
          │
          ▼
     Next.js server boundary
          │
          ▼
     FastAPI verifies token
          │
          ├── invalid/expired ───────────► 401
          │
          └── valid
                │
                ▼
          resolve/provision workspace
                │
                ├── setup incomplete ─────────────► /onboarding
                │
                └── setup complete
                        │
                        ▼
                 /projects/{projectId}
```

### 7.3 Onboarding ownership flow

```text
verified Clerk identity
        │
        ▼
provision/name workspace
        │
        ▼
create Project(name="Solari", slug="solari")
        │
        ▼
create Product(type="sandbox", name="Sandbox")
        │
        ▼
create Sandbox Configuration v1
        │
        ▼
mark onboarding complete
```

Each step is idempotent and workspace-scoped. Partially completed choices are
stored in the onboarding draft. The final step transaction creates the first
immutable Sandbox configuration and marks onboarding complete; it does not
start a verification run.

### 7.4 Deferred identity features

- Invitations.
- Shared workspaces.
- Admin/Decision-maker/Viewer roles.
- Organization switching.
- Enterprise SSO.

## 8. Persistence model

### 8.1 Minimal tables

```text
workspaces
  id
  clerk_owner_id (unique)
  name
  onboarding_completed_at?
  created_at

onboarding_drafts
  id
  workspace_id (unique)
  current_step
  state_json
  updated_at

projects
  id
  workspace_id
  slug
  name
  description?
  created_at

products
  id
  workspace_id
  project_id
  slug
  name
  product_type = "sandbox"
  created_at

product_configurations
  id
  workspace_id
  product_id
  version
  scenario_default
  manifest_sha256
  settings_json
  created_at

verification_runs
  id
  workspace_id
  product_id
  configuration_id
  scenario
  state
  manifest_sha256
  result_artifact_id?
  created_at
  started_at?
  completed_at?

verification_jobs
  id
  workspace_id
  run_id
  kind
  state
  attempt
  lease_owner?
  lease_expires_at?
  idempotency_key
  error_code?

findings
  id
  workspace_id
  run_id
  capability_id
  source_surface
  lifecycle_state
  evidence_artifact_id

execution_attempts
  id
  workspace_id
  run_id
  finding_id?
  language
  phase
  infrastructure_state
  subject_state
  sandbox_id?
  package_name
  package_version
  command_sha256
  evidence_artifact_id
  started_at
  completed_at?

proposals
  id
  workspace_id
  run_id
  finding_id
  state
  source_sha256
  proposed_sha256
  patch_artifact_id
  verification_attempt_id?

artifacts
  id
  workspace_id
  kind
  object_key
  sha256
  byte_length
  created_at
```

Required ownership constraints:

- Project slug is unique within a workspace.
- Product slug is unique within a project.
- The MVP permits one `sandbox` product per project.
- Onboarding draft data is non-secret, workspace-scoped, and replaced
  transactionally when its step advances.
- Configuration version is unique and monotonic within a product.
- A run's configuration must belong to the same product as the run.
- Project and product IDs from the client are locators, never authorization.

### 8.2 Storage policy

- PostgreSQL stores ownership, state, indexes, and artifact references.
- Artifact bodies live behind an `ArtifactStore` interface.
- Local development uses an immutable filesystem store.
- Every read recomputes or verifies the stored hash.
- Secrets are never artifacts.
- stdout/stderr are redacted and size-limited before storage.

## 9. API surface

```text
GET    /v1/me
PATCH  /v1/me/workspace

GET    /v1/onboarding
PATCH  /v1/onboarding

POST   /v1/projects
GET    /v1/projects
GET    /v1/projects/{project_id}
POST   /v1/projects/{project_id}/products
GET    /v1/projects/{project_id}/products
GET    /v1/products/{product_id}

GET    /v1/products/{product_id}/configuration
POST   /v1/products/{product_id}/configurations

POST   /v1/products/{product_id}/runs
GET    /v1/products/{product_id}/runs
GET    /v1/runs/{run_id}
POST   /v1/runs/{run_id}/cancel
GET    /v1/runs/{run_id}/matrix
GET    /v1/runs/{run_id}/executions

GET    /v1/executions/{execution_id}

GET    /v1/findings/{finding_id}
POST   /v1/findings/{finding_id}/proposals

GET    /v1/proposals/{proposal_id}
POST   /v1/proposals/{proposal_id}/verify
```

All mutation endpoints require:

- A verified session.
- Workspace ownership.
- CSRF protection.
- An idempotency key.
- Server-derived project/product/configuration/run/finding relationships.

## 10. Configured source manifest

Use JSON rather than YAML to avoid another parser dependency.

```json
{
  "schemaVersion": "noxyn-solari-manifest/1.0",
  "project": "solari",
  "product": "sandbox",
  "contract": {
    "source": "configured-capability-snapshot",
    "path": "noxyn_solari/fixtures/sandbox-create-evolution/after.json"
  },
  "packages": {
    "python": {
      "name": "solari-sandbox",
      "version": "PINNED_VERSION"
    },
    "typescript": {
      "name": "@solarisdk/sandbox",
      "version": "PINNED_VERSION"
    },
    "go": {
      "name": "github.com/solari-sdk/solari-sandbox-go",
      "version": "PINNED_VERSION"
    }
  },
  "examples": [
    "examples/sandbox-code-interpreter-py",
    "examples/sandbox-quickstart-ts"
  ]
}
```

The manifest itself is hashed and stored with every run.

## 11. Deterministic analysis pipeline

```text
CONFIGURE
    │ configured source manifest
    ▼
SNAPSHOT
    │ exact bytes, package versions, timestamps, hashes
    ▼
EXTRACT
    │ language/source-specific facts
    ▼
NORMALIZE
    │ canonical capability IDs and reviewed naming mappings
    ▼
COMPARE
    │ contract vs Python vs TS vs Go vs docs vs examples
    ▼
FINDINGS
    │ ALIGNED / SUSPECTED / NOT_EXPECTED / UNVERIFIED
    ▼
SELECT
    │ runnable affected artifacts only
    ▼
VERIFY
    │ fresh Solari sandboxes
    ▼
REPORT
    │ immutable evidence-backed run result
```

### 11.1 Deterministic first

Deterministic code owns:

- Exact package versions.
- Content hashing.
- Python signatures and calls.
- TypeScript `.d.ts` declarations and calls.
- Go exported symbols.
- Documentation code-block extraction.
- Cookbook dependency and entry-command extraction.
- Exit codes and logs.
- State derivation.

Semantic model assistance is deferred until deterministic mapping cannot cover
a necessary capability. Model output, if later added, is a proposal that must be
validated against exact source evidence.

## 12. Verification contracts

### 12.1 Execution request

```text
VerificationRequest
  id
  run_id
  language
  phase: reproduce | verify_fix
  source_artifact_id
  source_sha256
  package_name
  package_version
  entry_command: argv[]
  working_directory
  environment_allowlist
  timeout_seconds
  max_output_bytes
  template
  expected_capabilities[]
```

The command is argv, not an implicit shell string.

### 12.2 Execution result

```text
VerificationExecution
  request_id
  sandbox_id?
  language
  package_name
  package_version
  infrastructure_state: PASS | FAIL
  infrastructure_step:
      create
      connect
      materialize
      install
      execute
      collect
      cleanup
  subject_state: PASS | FAIL | NOT_RUN
  exit_code?
  stdout_redacted
  stderr_redacted
  output_truncated
  cleanup_state: PASS | FAIL | NOT_REQUIRED
  started_at
  completed_at
  evidence_sha256
```

### 12.3 Classification rules

```text
Sandbox create fails
  infrastructure = FAIL
  subject = NOT_RUN
  finding remains UNVERIFIED

Package install fails because registry is unreachable
  infrastructure = FAIL
  subject = NOT_RUN
  finding remains UNVERIFIED

Package installs; example exits 1
  infrastructure = PASS
  subject = FAIL
  finding becomes REPRODUCED

Package installs; example exits 0
  infrastructure = PASS
  subject = PASS
  suspected finding is dismissed/aligned

Corrected example exits 0 in a new sandbox
  infrastructure = PASS
  subject = PASS
  proposal becomes FIX_VERIFIED
```

## 13. Solari executor

```text
Noxyn worker
    │
    ├── validate request and input hash
    │
    ├── create Solari verification sandbox
    │
    ├── connect
    │
    ├── materialize trusted harness
    │
    ├── install exact package version
    │
    ├── execute bounded argv
    │
    ├── collect/redact/limit evidence
    │
    └── finally: kill verification sandbox
```

### 13.1 Testing Solari from inside Solari

Capabilities such as `sandbox.create` require two session levels:

```text
Noxyn worker
    │
    ▼
Verification sandbox
    │ installs published SDK
    │ receives dedicated API key through an allowed environment variable
    │
    ▼
Subject sandbox
    │ SDK capability is exercised here
    │
    ├── assertions
    └── finally: kill subject sandbox

Noxyn worker
    └── finally: kill verification sandbox
```

The subject harness must use `try/finally`. The controller also treats failure
to clean up either sandbox as a distinct cleanup failure.

### 13.2 Credential policy

- `SOLARI_API_KEY` exists only in the API/worker secret environment.
- It is passed only to reviewed verification harnesses.
- Arbitrary repositories do not receive it in this MVP.
- The value is never written into command text, files, logs, artifacts, or
  responses.
- Redaction scans all captured stdout/stderr before persistence.
- Development uses a dedicated key rather than a personal general-purpose key.

## 14. Background job flow

```text
User clicks Start run
        │
        ▼
API validates session + project/product ownership
        │
        ▼
transaction:
  create verification_run
  create verification_job
        │
        ▼
HTTP 202 + run ID
        │
        ▼
worker claims job with lease
        │
        ├── heartbeat/renew lease
        ├── write stage state
        ├── persist evidence incrementally
        └── complete or fail atomically
        │
        ▼
UI polls run state
        │
        ▼
terminal matrix/report
```

### 14.1 Retry policy

- Sandbox provisioning/connectivity failures may retry within a small fixed
  ceiling.
- Registry transport failures may retry if no subject command ran.
- A subject failure is evidence and is never automatically retried as if it were
  infrastructure noise.
- Fix verification is a new execution attempt in a new sandbox.
- An expired worker lease can be reclaimed safely.
- Completion is idempotent and cannot overwrite another terminal result.

## 15. End-to-end product flows

### Flow A — Sign in, create project, and add product

```text
Open Noxyn-Solari
      │
      ▼
No valid session? ── yes ──► Clerk sign-in
      │                          │
      no                         ▼
      │                    verify session
      │                          │
      └──────────────┬───────────┘
                     ▼
           resolve/create workspace
                     │
          onboarding complete?
              ┌──────┴──────┐
              │ yes         │ no
              ▼             ▼
      Solari project    create Solari project
        overview             │
                             ▼
                    add Sandbox product
                             │
                             ▼
                    configure Sandbox
                             │
                             ▼
                    Solari project overview
```

### Flow B — Start controlled verification run

```text
Sandbox runs screen
    │
    ├── choose "Controlled API evolution"
    │
    ├── review pinned package versions
    │
    └── Start verification
            │
            ▼
       queued run created
            │
            ▼
       background pipeline
```

### Flow C — API change to impact discovery

```text
Before capability snapshot
            │
            ├──────────┐
            │          │
            ▼          ▼
After capability   SDK/docs/example snapshots
snapshot                │
            │            │
            └─────┬──────┘
                  ▼
          canonical capability diff
                  │
                  ▼
         affected capability IDs
                  │
                  ▼
    mapped Python / TS / Go / docs / examples
                  │
                  ▼
              SUSPECTED
```

### Flow D — Suspected drift to reproduced breakage

```text
SUSPECTED runnable artifact
          │
          ▼
fresh language-specific Solari sandbox
          │
          ▼
install exact published package
          │
          ▼
execute exact consumer harness
          │
     ┌────┴───────────────┐
     ▼                    ▼
infrastructure PASS   infrastructure FAIL
subject FAIL          subject NOT_RUN
     │                    │
     ▼                    ▼
REPRODUCED            UNVERIFIED
```

### Flow E — Published package and docs verification

```text
Docs/cookbook code block
          │ source hash + capability mapping
          ▼
language verification sandbox
          │
          ├── install exact PyPI/npm/Go version
          ├── materialize code block in harness
          ├── execute
          └── capture evidence
          │
     ┌────┴────┐
     ▼         ▼
   PASS      FAIL
     │         │
  ALIGNED   REPRODUCED
```

### Flow F — Cross-language parity

```text
                 canonical capability
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Python        TypeScript         Go
          │              │              │
     fresh sandbox  fresh sandbox  fresh sandbox
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                   parity result
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
      aligned         conflict         unverified
```

### Flow G — Generate proposal and verify it

```text
REPRODUCED cookbook/docs finding
              │
              ▼
validate exact source hash
              │
              ▼
create focused patch artifact
              │
              ▼
FIX_PROPOSED
              │
              ▼
NEW Solari verification sandbox
              │
              ├── install same exact package
              ├── apply exact proposed bytes
              └── execute corrected consumer
              │
         ┌────┴────┐
         ▼         ▼
       PASS      FAIL
         │         │
         ▼         ▼
FIX_VERIFIED   FIX_PROPOSED remains
```

### Flow H — Evidence inspection

```text
Matrix cell / finding / execution
              │
              ▼
resolve workspace-scoped evidence reference
              │
              ▼
verify artifact hash and byte length
              │
         ┌────┴────┐
         ▼         ▼
       valid     invalid
         │         │
         ▼         ▼
show redacted   fail closed;
evidence        do not show/accept result
```

### Flow I — Failure and recovery

```text
worker stops while job is running
              │
              ▼
lease expires
              │
              ▼
new worker reclaims job
              │
              ├── completed evidence already exists?
              │       ├── yes: reconcile idempotently
              │       └── no: restart safe stage
              │
              ▼
terminal run without duplicate findings/proposals
```

### Flow J — Current configured Solari scan

```text
Runs screen
    │
    ├── choose "Current configured Solari ecosystem"
    │
    ▼
resolve pinned/current manifest versions
    │
    ▼
snapshot current contract/docs/packages/examples
    │
    ▼
run the same deterministic comparison pipeline
    │
    ├── no suspected drift ───────────► COMPLETED / ALIGNED
    │
    ├── suspected runnable drift ─────► Solari verification
    │
    └── unavailable source ───────────► UNVERIFIED, run still truthful
```

The current scan never manufactures a finding to make a run interesting.

### Flow K — User cancellation

```text
User requests cancellation
          │
          ▼
API verifies workspace ownership
          │
          ▼
run becomes CANCEL_REQUESTED
          │
          ▼
worker observes cancellation
          │
          ├── stop launching new execution units
          ├── terminate active bounded command when supported
          ├── kill active subject sandbox
          └── kill active verification sandbox
          │
          ▼
persist partial evidence + cleanup result
          │
          ▼
run becomes CANCELLED
```

Cancellation does not delete evidence already produced.

### Flow L — Session expiry and reauthentication

```text
Protected request
      │
      ▼
session expired/revoked
      │
      ├── API returns 401
      ├── no protected data is rendered
      └── UI redirects to sign in with safe return path
              │
              ▼
         user signs in again
              │
              ▼
         original protected route
```

## 16. Screen map

```text
/sign-in
   │
   ▼
/onboarding
   │
   ├── create/name workspace
   ├── create Solari project
   ├── add Sandbox product
   └── configure Sandbox
   │
   ▼
/projects/{projectId}
   │
   ▼
/projects/{projectId}/products/{productId}/runs
   │
   ├── start run
   └── /runs/{runId}
          ├── /executions/{executionId}
          └── /findings/{findingId}
```

## 17. Screen wireframes

This section is a compact product-state summary. The complete onboarding and
route-scoped wireframes are defined in
[`mvp-ux-lifecycle.md`](./mvp-ux-lifecycle.md).

### Screen 1 — Sign in

```text
┌──────────────────────────────────────────────────────────────────────┐
│ NOXYN / SOLARI                                                       │
│                                                                      │
│                  Verify what developers actually run                │
│                                                                      │
│      Compare Solari Sandbox SDKs, docs, and examples—and prove      │
│      suspected drift in clean Solari environments.                  │
│                                                                      │
│                  ┌────────────────────────────┐                      │
│                  │ Continue with email       │                      │
│                  └────────────────────────────┘                      │
│                                                                      │
│      Protected verification evidence. No public report links.       │
└──────────────────────────────────────────────────────────────────────┘
```

States:

```text
default → Clerk interaction → verifying → redirect
                              └→ invalid/expired → recoverable error
```

### Screen 2 — Runs dashboard

```text
┌──────────────────────────────────────────────────────────────────────┐
│ NOXYN / SOLARI       Runs                         User ▾             │
├──────────────────────────────────────────────────────────────────────┤
│ Solari / Sandbox                                      [ Start run ] │
│                                                                      │
│ Latest verification                                                  │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Controlled API evolution                      COMPLETED          │ │
│ │ Run 01J...  ·  Python 0.x  ·  TypeScript 0.x  ·  Go 0.x        │ │
│ │                                                                  │ │
│ │  3 suspected    2 reproduced    2 fix verified    1 aligned     │ │
│ │                                                                  │ │
│ │ Started 10:24 · Duration 2m 18s             [ Open run → ]      │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ Run history                                                          │
│ ┌──────────────┬──────────────┬────────────┬────────────┬──────────┐ │
│ │ Started      │ Scenario     │ State      │ Findings   │ Runtime  │ │
│ ├──────────────┼──────────────┼────────────┼────────────┼──────────┤ │
│ │ Today 10:24  │ Controlled   │ Completed  │ 2 verified │ 5 pass   │ │
│ │ Yesterday    │ Current scan │ Unverified │ 1 suspect  │ 1 infra  │ │
│ └──────────────┴──────────────┴────────────┴────────────┴──────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

Empty state:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ No verification runs yet                                            │
│                                                                      │
│ Start with the controlled API-evolution scenario, then scan the      │
│ current configured Solari ecosystem using the same pipeline.         │
│                                                     [ Start run ]    │
└──────────────────────────────────────────────────────────────────────┘
```

Start-run panel:

```text
┌──────────────────────── Start verification ─────────────────────────┐
│ Scenario                                                            │
│ (●) Controlled API evolution                                       │
│ ( ) Current configured Solari ecosystem                             │
│                                                                     │
│ Packages                                                            │
│ Python       solari-sandbox==PINNED                                 │
│ TypeScript   @solarisdk/sandbox@PINNED                              │
│ Go           github.com/.../solari-sandbox-go@PINNED                │
│                                                                     │
│ Runtime cost                                                        │
│ Up to 3 language sandboxes for reproduction.                        │
│ Fix verification creates new sandboxes.                             │
│                                                                     │
│                                  [ Cancel ] [ Start verification ]   │
└─────────────────────────────────────────────────────────────────────┘
```

### Screen 3 — Run detail and capability matrix

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Runs / 01J...                             COMPLETED · 2m 18s        │
├──────────────────────────────────────────────────────────────────────┤
│ Controlled API evolution                                             │
│ Contract abc123…  Python 0.x  TypeScript 0.x  Go 0.x                │
│                                                                      │
│  14 capabilities   3 suspected   2 reproduced   2 verified          │
│                                                                      │
│ [ All ] [ Suspected ] [ Reproduced ] [ Verified ]     Search...     │
│                                                                      │
│ ┌────────────────┬────┬────┬────┬────┬────┬────┬─────────┐          │
│ │ Capability     │ API│ Py │ TS │ Go │Docs│ Ex │ Runtime │          │
│ ├────────────────┼────┼────┼────┼────┼────┼────┼─────────┤          │
│ │ sandbox.create │ ✓  │ ✓  │ ✓  │ ✓  │ !  │ !  │ 2 fail │          │
│ │ commands.run   │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ 3 pass │          │
│ │ files.write    │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ —  │ 3 pass │          │
│ │ snapshot       │ ✓  │ ✓  │ ✓  │ ?  │ ✓  │ ✓  │ pending│          │
│ └────────────────┴────┴────┴────┴────┴────┴────┴─────────┘          │
│                                                                      │
│ Pipeline                                                             │
│ Discover ✓ Snapshot ✓ Extract ✓ Compare ✓ Verify ✓ Report ✓         │
└──────────────────────────────────────────────────────────────────────┘
```

Selected-cell evidence drawer:

```text
┌──────────────────────── Evidence ────────────────────────────┐
│ sandbox.create / Python cookbook                             │
│ State: REPRODUCED                                            │
│                                                             │
│ Source                                                      │
│ examples/sandbox-code-interpreter-py/main.py                 │
│ SHA-256  91f...                                              │
│ Locator  main.py:23                                          │
│                                                             │
│ Claim                                                       │
│ SandboxClient.create(template="base", old_argument=...)     │
│                                                             │
│ Runtime                                                     │
│ Python · solari-sandbox==0.x · exit 1                       │
│                                               [ Open run ]   │
└─────────────────────────────────────────────────────────────┘
```

Running state:

```text
┌──────────────────────── Verification progress ──────────────────────┐
│ Snapshot sources                                         complete   │
│ Analyze contract and packages                            complete   │
│ Map capabilities                                          complete   │
│ Python verification                                      running    │
│ TypeScript verification                                  queued     │
│ Go verification                                          queued     │
│                                                                      │
│ Last update 3 seconds ago                                  [ Stop ] │
└──────────────────────────────────────────────────────────────────────┘
```

### Screen 4 — Execution detail

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Run 01J... / Execution 01K...                         REPRODUCED     │
├──────────────────────────────────────────────────────────────────────┤
│ Python cookbook                                                      │
│                                                                      │
│ Infrastructure                         Subject                       │
│ PASS                                   FAIL                          │
│                                                                      │
│ Solari sandbox    sbx_01...                                         │
│ Package           solari-sandbox==0.x                               │
│ Source            main.py · SHA-256 91f...                           │
│ Command           python main.py                                    │
│ Exit              1                                                 │
│ Duration          8.4s                                              │
│ Cleanup           PASS                                              │
│                                                                      │
│ stdout                                                               │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ creating sandbox...                                              │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ stderr                                                               │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ TypeError: create() got an unexpected keyword argument ...       │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ Evidence SHA-256  b72...                         [ View finding → ]  │
└──────────────────────────────────────────────────────────────────────┘
```

Infrastructure-failure variant:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Infrastructure: FAIL        Subject: NOT RUN        UNVERIFIED      │
│                                                                      │
│ Failed step       create                                            │
│ Safe error        Solari capacity unavailable                       │
│ Attempts          2 / 2                                             │
│ Product impact    No SDK conclusion was produced                    │
└──────────────────────────────────────────────────────────────────────┘
```

### Screen 5 — Finding and proposal result

```text
┌──────────────────────────────────────────────────────────────────────┐
│ sandbox.create / Python cookbook                    FIX VERIFIED ✓  │
├──────────────────────────────────────────────────────────────────────┤
│ Lifecycle                                                            │
│                                                                      │
│ SUSPECTED ──► REPRODUCED ──► FIX PROPOSED ──► FIX VERIFIED          │
│                                                                      │
│ Evidence                                                             │
│ Contract expects:  new_argument                                     │
│ Cookbook uses:      old_argument                                    │
│ Runtime before:    exit 1                                           │
│                                                                      │
│ Proposed change                                                     │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ - await client.create(old_argument=2048)                         │ │
│ │ + await client.create(new_argument=2048)                         │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ Source binding                                                       │
│ Before SHA-256   91f...                                              │
│ Proposed SHA-256 7ab...                                              │
│                                                                      │
│ Fresh verification                                                   │
│ Sandbox      sbx_02...                                               │
│ Package      solari-sandbox==0.x                                    │
│ Exit         0                                                       │
│ Cleanup      PASS                                                    │
│ Evidence     d31...                                                  │
│                                                                      │
│ Noxyn proposed and verified this patch. It has not merged it.       │
└──────────────────────────────────────────────────────────────────────┘
```

Before a proposal exists:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ sandbox.create / Python cookbook                    REPRODUCED       │
│                                                                      │
│ The failure was reproduced against solari-sandbox==0.x.              │
│ Noxyn can create a focused proposal for this cookbook file.          │
│                                                                      │
│ Proposed scope                                                       │
│ examples/sandbox-code-interpreter-py/main.py                         │
│                                                                      │
│                         [ Generate proposal ]                        │
└──────────────────────────────────────────────────────────────────────┘
```

### Shared protected-screen states

Loading:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Loading protected workspace…                                        │
└──────────────────────────────────────────────────────────────────────┘
```

Authorization failure:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ This resource is unavailable                                        │
│ It may not exist or may belong to another workspace.                 │
│                                                    [ Back to runs ]  │
└──────────────────────────────────────────────────────────────────────┘
```

Recoverable API failure:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ We could not load this verification                                  │
│ No run or evidence state was changed.                                │
│                                           [ Back ] [ Try again ]     │
└──────────────────────────────────────────────────────────────────────┘
```

## 18. Controlled scenario

The controlled scenario must be labelled everywhere as a fixture, not a current
Solari defect.

```text
Scenario: sandbox.create evolves

Contract after change       aligned with new field
Python package              aligned
TypeScript package          aligned
Go package                  aligned or initially unverified
Product guide               aligned
Python cookbook fixture     stale
Documentation fixture       stale
```

Expected run:

```text
Static comparison
  2 SUSPECTED
        │
        ▼
Solari execution
  2 REPRODUCED
        │
        ▼
Noxyn proposals
  2 FIX_PROPOSED
        │
        ▼
fresh Solari execution
  2 FIX_VERIFIED
```

The current scan uses the same pipeline but does not promise that it will find a
real inconsistency.

## 19. Reliability and security requirements

### 19.1 Reliability

- Pin all SDK versions.
- Hash every source and output.
- Use fresh sandboxes for reproduction and fix verification.
- Use argv, explicit working directories, and bounded environments.
- Apply wall-clock and output limits.
- Preserve partial evidence.
- Use `finally` cleanup at subject and verification levels.
- Treat cleanup failure as its own failure.
- Use durable job leases and idempotent terminal writes.
- Provide a checked-in redacted replay fixture so UI and tests do not require
  Solari credits.
- Keep live integration tests behind an explicit flag.

### 19.2 Security

- Verify authentication server-side.
- Scope every query to the authenticated workspace.
- Do not accept workspace ownership from request bodies.
- Keep the Solari key server-side except during reviewed harness injection.
- Never persist secrets.
- Redact captured output before storage.
- Do not execute arbitrary repositories in V1.
- Do not provide merge or publication credentials.
- Reject source-hash changes before applying a proposal.

## 20. Testing strategy

```text
Unit tests
  hashing and canonical serialization
  capability normalization
  Python/TS/Go mapping
  static comparison states
  infrastructure-vs-subject classification
  proposal ambiguity/source binding

Repository tests
  workspace isolation
  protected route authorization
  idempotent run creation
  job lease/reclaim/completion
  artifact immutability and hash verification

Executor tests with fake Solari adapter
  provisioning failure
  install failure
  subject failure
  output truncation
  cleanup failure
  successful reproduction
  successful fresh-sandbox fix verification

Live tests, opt-in
  Python package execution
  TypeScript package execution
  Go package execution
  subject and verification sandbox cleanup

Browser tests
  sign in boundary
  runs list
  progress polling
  matrix filters/evidence drawer
  execution evidence
  proposal lifecycle
```

## 21. Delivery sequence

### Milestone 1 — Product foundation

- Transplant root pnpm/uv conventions.
- Add one Next.js console.
- Add the FastAPI service.
- Add Clerk authentication and protected routes.
- Add generated OpenAPI/client flow.
- Create a user workspace automatically.
- Add minimal workspace, onboarding draft, project, product, and product
  configuration persistence.
- Add the seven-step onboarding shell for Solari project and Sandbox product
  creation.

Exit: a user signs in, creates the Solari project, adds Sandbox, and reaches
the protected project overview.

### Milestone 2 — Durable run foundation

- Extend the minimal PostgreSQL migration with runs, jobs, and artifact
  references.
- Add immutable local artifact storage.
- Add leased background worker.
- Add polling run state.

Exit: an authenticated user starts a durable no-op Sandbox run and sees it
complete under the Solari project.

### Milestone 3 — Static controlled analysis

- Add configured manifest and controlled fixture.
- Add hashing, extraction, capability normalization, and comparison.
- Persist matrix/findings evidence.
- Render the matrix and evidence drawer.

Exit: the controlled scenario deterministically yields the expected suspected
findings without Solari execution.

### Milestone 4 — Python Solari verification

- Implement `VerificationExecutor`.
- Implement `SolariSandboxExecutor`.
- Add Python package installation and harness execution.
- Separate infrastructure and subject results.
- Add execution evidence screen.

Exit: the controlled Python drift is reproduced and safely persisted.

### Milestone 5 — TypeScript and parity

- Add TypeScript package inspection and execution.
- Use separate Python and TypeScript sandboxes.
- Populate runtime matrix cells.
- Add parity reporting.

Exit: one run shows Python/TypeScript static and runtime parity.

### Milestone 6 — Proposals and re-verification

- Add exact source-bound cookbook/docs proposals.
- Add proposal UI.
- Run corrected code in a new sandbox.
- Persist `FIX_VERIFIED` only after a clean pass.

Exit: the controlled lifecycle completes from suspected through fix verified.

### Milestone 7 — Go and current scan

- Add Go static extraction and runtime harness.
- Add the Go matrix column and evidence.
- Add configured current-Solari mode.
- Preserve honest unverified states for unsupported facts.

Exit: all three languages use the same pipeline and V1 is complete.

## 22. Local operation

Target developer flow:

```bash
cp .env.example .env.local
docker compose up -d --wait
pnpm install --frozen-lockfile
uv sync --frozen
pnpm db:migrate
pnpm dev
```

Required secrets/configuration:

```text
Clerk development publishable key
Clerk development secret key
PostgreSQL URL
SOLARI_API_KEY
```

A deterministic replay mode must remain available without `SOLARI_API_KEY` for
UI development and non-live CI.

## 23. MVP definition of done

Noxyn-Solari V1 is complete when:

1. A user can authenticate and receive a private workspace.
2. The user can configure Solari as a project.
3. The user can add Sandbox as Solari's first product.
4. Sandbox configuration is immutable and versioned independently of the
   Solari project.
5. The user can start the controlled Sandbox run and revisit it later.
6. The manifest and every inspected source are snapshotted and hashed.
7. The matrix compares contract, Python, TypeScript, Go, docs, examples, and
   runtime without collapsing unknowns into failures.
8. Each language executes in its own fresh Solari sandbox.
9. Infrastructure failure and subject failure are visibly distinct.
10. The controlled stale artifacts are reproducibly marked `REPRODUCED`.
11. Noxyn creates exact source-bound proposals for the controlled cookbook/docs
   artifacts.
12. Each proposal is verified in a new sandbox before becoming `FIX_VERIFIED`.
13. All evidence is workspace-scoped, immutable, hashed, redacted, and
    inspectable from the UI.
14. Interrupted jobs recover without duplicate terminal facts.
15. Unit, persistence, API, worker, UI, and opt-in live Solari tests pass.
16. The current-Solari mode can complete honestly even when it finds no drift.
17. Noxyn never merges, publishes, or deploys a proposed change.

## 24. Final product flow

```text
AUTHENTICATE
     │
     ▼
CREATE DURABLE RUN
     │
     ▼
SNAPSHOT CONFIGURED SOLARI SOURCES
     │
     ▼
NORMALIZE CAPABILITIES
     │
     ▼
COMPARE CONTRACT / SDKs / DOCS / EXAMPLES
     │
     ▼
SUSPECTED FINDINGS
     │
     ▼
FRESH SOLARI SANDBOXES
     │
     ├── subject passes ──────────────► DISMISSED / ALIGNED
     │
     ├── infrastructure fails ────────► UNVERIFIED
     │
     └── subject fails
             │
             ▼
         REPRODUCED
             │
             ▼
       EXACT PATCH PROPOSAL
             │
             ▼
         FIX_PROPOSED
             │
             ▼
       NEW SOLARI SANDBOX
             │
        ┌────┴────┐
        ▼         ▼
      PASS       FAIL
        │         │
        ▼         ▼
 FIX_VERIFIED  FIX_PROPOSED
               remains
```
