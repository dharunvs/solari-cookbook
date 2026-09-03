# Noxyn-Solari MVP Web Experience

| Field | Value |
|---|---|
| Status | Finalized MVP UX baseline |
| Scope | Registration through configuration, verification, and return visits |
| Related architecture | `finalized-mvp.md` |
| Last updated | 2026-09-01 |

## 1. Experience goal

A new user should reach a meaningful, verified result without needing to
understand Noxyn's internal pipeline.

```text
CREATE ACCOUNT
      ↓
REVIEW SOLARI CONFIGURATION
      ↓
RUN VERIFICATION
      ↓
SEE WHAT IS ACTUALLY BROKEN
      ↓
REVIEW A PROPOSED FIX
      ↓
VERIFY THE FIX IN A FRESH SANDBOX
      ↓
RETURN TO A DURABLE RESULT
```

The product lifecycle remains visible throughout the UI:

```text
SUSPECTED → REPRODUCED → FIX PROPOSED → FIX VERIFIED
```

The UI must also distinguish these outcomes:

```text
Infrastructure PASS + Subject FAIL     = reproduced product drift
Infrastructure FAIL + Subject NOT RUN  = unverified, not broken
```

## 2. Lean information architecture

The MVP exposes the product hierarchy directly:

```text
Private workspace
└── Project: Solari
    └── Product: Sandbox
        ├── configuration versions
        ├── verification runs
        ├── findings
        └── verified proposals
```

Routes are scoped through project and product. Wizard steps, drawers, and
loading/result states do not become additional top-level products.

```text
Public/authentication
├── /sign-in
└── /sign-up

First-time setup
└── /onboarding?step=workspace|project|product|sources|packages|readiness|review

Authenticated product
├── /projects/{projectId}
├── /projects/{projectId}/products/{productId}/runs
├── /projects/{projectId}/products/{productId}/runs/{runId}
│   ├── /executions/{executionId}
│   └── /findings/{findingId}
└── /projects/{projectId}/products/{productId}/configuration
```

Authenticated navigation is deliberately small:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ NOXYN   Solari / Sandbox     Runs   Configuration      [ User ▾ ]   │
└──────────────────────────────────────────────────────────────────────┘
```

There is no organization switcher, team management, runtime-environment
builder, or general repository-discovery UI. Every user gets one private
workspace, configures Solari as a project, and adds Sandbox as that project's
first product. Browser and Desktop remain future products, not MVP features.

## 3. Complete user journey

### 3.1 First-time user

```text
Open application
       │
       ▼
Session exists? ── no ──► Sign in
       │                    │
       │               New user?
       │                    │ yes
       │                    ▼
       │                 Sign up
       │                    │
       │                    ▼
       │              Verify email
       │                    │
       └──────────────┬─────┘
                      ▼
             Create private workspace
                      │
                      ▼
              Create Solari project
                      │
                      ▼
             Add Sandbox product
                      │
                      ▼
          Review official Solari sources
                      │
                      ▼
        Choose SDK versions and languages
                      │
                      ▼
       Check Noxyn and Solari readiness
                      │
                      ▼
           Review and save configuration
                      │
                      ▼
             Solari project overview
                      │
                      ▼
                Open Sandbox
                      │
                      ▼
              Start first verification
                      │
                      ▼
              Watch live run progress
                      │
                      ▼
             Review capability results
                      │
               ┌──────┴──────┐
               ▼             ▼
          Everything      Drift reproduced
           aligned             │
               │               ▼
               │        Review proposed fix
               │               │
               │               ▼
               │       Verify in new sandbox
               │               │
               └───────┬───────┘
                       ▼
                Final run summary
```

### 3.2 Returning user

```text
Open application
       │
       ▼
Valid session
       │
       ▼
Solari project overview
       │
       └── Open Sandbox
               │
               ├── Open latest run
               ├── Open historical run
               ├── Start another run
               └── Edit future-run configuration
```

### 3.3 Entry routing

```text
Request /
   │
   ├── no session ─────────────────────────► /sign-in
   │
   └── authenticated
          │
          ├── onboarding incomplete ───────► /onboarding
          │
          └── onboarding complete ─────────► /projects/{projectId}
```

## 4. Global application shell

```text
┌──────────────────────────────────────────────────────────────────────┐
│ NOXYN   Solari / Sandbox     Runs   Configuration      [ DV ▾ ]     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Breadcrumb / page title                             Primary action   │
│ Supporting sentence                                                 │
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │                                                                  │ │
│ │                       PAGE CONTENT                               │ │
│ │                                                                  │ │
│ └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

User menu:

```text
┌──────────────────────────┐
│ dharun@example.com       │
│ Project: Solari          │
│ Product: Sandbox         │
├──────────────────────────┤
│ Configuration            │
│ Sign out                 │
└──────────────────────────┘
```

The project/product breadcrumb gives context. Neither is a switcher in the MVP.

## 5. Authentication

Clerk owns credentials, verification, password reset, and session security.
Noxyn owns the containing page, protected routing, and workspace provisioning.

### A1 — Sign in

Route: `/sign-in`

```text
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  NOXYN / SOLARI                                                      │
│                                                                      │
│  Verify the code developers actually use.                            │
│  Compare Solari's API, SDKs, docs, and examples—then execute         │
│  suspected drift in clean Solari Sandboxes.                          │
│                                                                      │
│                         ┌──────────────────────────────────────┐     │
│                         │ Sign in to Noxyn                    │     │
│                         │                                    │     │
│                         │ Email                              │     │
│                         │ [_______________________________]  │     │
│                         │ [ Continue ]                       │     │
│                         │                                    │     │
│                         │ ───────────── or ─────────────     │     │
│                         │ [ Continue with Google ]           │     │
│                         │                                    │     │
│                         │ New here? Create account           │     │
│                         └──────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

Actions: authenticate, go to sign-up, or resume a safe protected return route.

### A2 — Create account

Route: `/sign-up`

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         ┌──────────────────────────────────────┐     │
│                         │ Create your Noxyn account           │     │
│                         │                                    │     │
│                         │ First name                         │     │
│                         │ [_______________________________]  │     │
│                         │ Work email                        │     │
│                         │ [_______________________________]  │     │
│                         │ Password                          │     │
│                         │ [_______________________________]  │     │
│                         │                                    │     │
│                         │ [ Create account ]                 │     │
│                         │                                    │     │
│                         │ Have an account? Sign in           │     │
│                         └──────────────────────────────────────┘     │
│  By continuing, you agree to the Terms and Privacy Policy.           │
└──────────────────────────────────────────────────────────────────────┘
```

The exact fields can follow Clerk configuration. Noxyn does not create a
second credential database.

### A3 — Verify email

Clerk-controlled state within `/sign-up`:

```text
┌──────────────────────────────────────────┐
│ Verify your email                        │
│                                          │
│ We sent a code to d•••••@example.com     │
│                                          │
│ [ _ ] [ _ ] [ _ ] [ _ ] [ _ ] [ _ ]   │
│                                          │
│ [ Verify ]                               │
│ Didn't receive it? Resend code           │
└──────────────────────────────────────────┘
```

Success redirects to `/onboarding`. The first authenticated API request
provisions the user's private workspace idempotently.

### A4 — Authentication errors

```text
Invalid credentials
┌──────────────────────────────────────────┐
│ We couldn't sign you in.                 │
│ Check your details and try again.        │
│                              [ Retry ]   │
└──────────────────────────────────────────┘

Expired verification code
┌──────────────────────────────────────────┐
│ That code has expired.                   │
│                      [ Send a new code ] │
└──────────────────────────────────────────┘
```

Errors must not expose whether an unrelated email address has an account.

## 6. First-time configuration wizard

Onboarding is seven persisted steps on one route:

```text
Workspace → Project → Product → Sources → Packages → Readiness → Review
    1          2         3         4          5           6          7
```

The official Solari setup is prefilled. Users review a small number of safe
choices instead of constructing a general ingestion system.

### O1 — Workspace

Route: `/onboarding?step=workspace`

```text
┌──────────────────────────────────────────────────────────────────────┐
│  Set up Solari verification                         Step 1 of 7      │
│  ● Workspace  ○ Project  ○ Product  ○ Sources                       │
│  ○ Packages   ○ Readiness  ○ Review                                  │
│                                                                      │
│  Welcome, Dharun.                                                    │
│  Noxyn will create a private workspace for your verification runs.   │
│                                                                      │
│  Workspace name                                                     │
│  [ Dharun's workspace___________________________________________ ]  │
│  Only you can access this workspace in the MVP.                      │
│                                                                      │
│                                                 [ Continue ]         │
└──────────────────────────────────────────────────────────────────────┘
```

No organization selection or team invitation is shown.

### O2 — Create the Solari project

Route: `/onboarding?step=project`

```text
┌──────────────────────────────────────────────────────────────────────┐
│  Create a project                                    Step 2 of 7     │
│  ✓ Workspace  ● Project  ○ Product  ○ Sources                       │
│  ○ Packages   ○ Readiness  ○ Review                                  │
│                                                                      │
│  Projects group related products under one API ecosystem.            │
│                                                                      │
│  Project name                                                        │
│  [ Solari_______________________________________________________ ]  │
│                                                                      │
│  Project slug                                                        │
│  [ solari_______________________________________________________ ]  │
│  Used in URLs and immutable project identity.                        │
│                                                                      │
│  Description                                                         │
│  [ Official Solari developer platform ecosystem________________ ]  │
│                                                                      │
│                                      [ Back ] [ Create project ]     │
└──────────────────────────────────────────────────────────────────────┘
```

This creates the `Solari` project inside the authenticated user's workspace.
The project is a container; it does not directly own Sandbox SDK versions or
verification runs.

### O3 — Add Sandbox as the first product

Route: `/onboarding?step=product`

```text
┌──────────────────────────────────────────────────────────────────────┐
│  Add your first product                              Step 3 of 7     │
│  ✓ Workspace  ✓ Project  ● Product  ○ Sources                       │
│  ○ Packages   ○ Readiness  ○ Review                                  │
│                                                                      │
│  Project: Solari                                                     │
│                                                                      │
│  ┌──────────────────────┐ ┌──────────────────────┐                   │
│  │ SANDBOX              │ │ BROWSER              │                   │
│  │                      │ │                      │                   │
│  │ Disposable code     │ │ Browser automation   │                   │
│  │ execution and       │ │                      │                   │
│  │ verification        │ │ Available later      │                   │
│  │                      │ │                      │                   │
│  │ (●) Add Sandbox     │ │ ( ) Not in MVP       │                   │
│  └──────────────────────┘ └──────────────────────┘                   │
│                                                                      │
│  ┌──────────────────────┐                                           │
│  │ DESKTOP              │                                           │
│  │ Desktop environments │                                           │
│  │ Available later      │                                           │
│  │ ( ) Not in MVP       │                                           │
│  └──────────────────────┘                                           │
│                                                                      │
│  Product name                                                        │
│  [ Sandbox______________________________________________________ ]  │
│                                                                      │
│                                  [ Back ] [ Add Sandbox product ]    │
└──────────────────────────────────────────────────────────────────────┘
```

Only Sandbox is actionable. Browser and Desktop clarify the project/product
model but remain disabled and are not persisted as placeholder products.

After continuing, the hierarchy is:

```text
Dharun's workspace
└── Solari
    └── Sandbox
```

### O4 — Configure Sandbox sources

Route: `/onboarding?step=sources`

```text
┌──────────────────────────────────────────────────────────────────────┐
│  Configure Sandbox sources                          Step 4 of 7      │
│  ✓ Workspace  ✓ Project  ✓ Product  ● Sources                       │
│  ○ Packages   ○ Readiness  ○ Review                                  │
│                                                                      │
│  Project: Solari / Product: Sandbox                                  │
│                                                                      │
│  Source preset                                                       │
│  (●) Official Solari Sandbox                                        │
│                                                                      │
│  ┌───────────────────┬──────────────────────────┬───────────┐        │
│  │ Surface           │ Identity                 │ Status    │        │
│  ├───────────────────┼──────────────────────────┼───────────┤        │
│  │ API contract      │ Approved manifest entry  │ Ready     │        │
│  │ Python SDK        │ PyPI + official source   │ Ready     │        │
│  │ TypeScript SDK    │ npm + official source    │ Ready     │        │
│  │ Go SDK            │ Go module + source       │ Ready     │        │
│  │ Documentation     │ Official docs snapshot   │ Ready     │        │
│  │ Cookbook examples │ solari-cookbook          │ Ready     │        │
│  └───────────────────┴──────────────────────────┴───────────┘        │
│                                                                      │
│  Manifest revision  solari-sandbox-v1                    [ Details ] │
│  Every run records exact revisions and hashes.                       │
│                                                                      │
│                                   [ Back ] [ Continue ]              │
└──────────────────────────────────────────────────────────────────────┘
```

Details drawer:

```text
┌──────────────────────── Source details ──────────────────────────────┐
│ Cookbook                                                             │
│ Repository   github.com/solari-sdk/solari-cookbook                   │
│ Ref          pinned commit / configured current ref                  │
│ Scan roots   approved example directories                            │
│ Access       public, read-only                                       │
│                                                       [ Close ]      │
└──────────────────────────────────────────────────────────────────────┘
```

URLs, repository identities, and allowed roots come from the reviewed server
manifest. Arbitrary free-text source input is deferred.

### O5 — Sandbox packages and languages

Route: `/onboarding?step=packages`

```text
┌──────────────────────────────────────────────────────────────────────┐
│  Choose Sandbox verification targets                Step 5 of 7      │
│  ✓ Workspace  ✓ Project  ✓ Product  ✓ Sources                       │
│  ● Packages   ○ Readiness  ○ Review                                  │
│                                                                      │
│  Default scenario                                                    │
│  (●) Controlled API-evolution scenario                              │
│      Reproducible learning run; clearly labelled as a fixture.       │
│  ( ) Current configured Solari ecosystem                            │
│      Inspect approved current/pinned revisions.                      │
│                                                                      │
│  Languages                                                           │
│  [✓] Python       solari-sandbox            [ PINNED ▾ ]             │
│  [✓] TypeScript   @solarisdk/sandbox        [ PINNED ▾ ]             │
│  [✓] Go           solari-sandbox-go         [ PINNED ▾ ]             │
│                                                                      │
│  [✓] Execute suspected runnable artifacts in fresh sandboxes         │
│      Required for REPRODUCED and FIX VERIFIED.                       │
│                                                                      │
│                                   [ Back ] [ Continue ]              │
└──────────────────────────────────────────────────────────────────────┘
```

Package choices are approved registry versions, not arbitrary install commands.
Go may say `Coming next` during implementation, but must work before V1 is
declared complete.

### O6 — Readiness

Route: `/onboarding?step=readiness`

```text
┌──────────────────────────────────────────────────────────────────────┐
│  Check Sandbox readiness                             Step 6 of 7     │
│  ✓ Workspace  ✓ Project  ✓ Product  ✓ Sources                       │
│  ✓ Packages   ● Readiness  ○ Review                                  │
│                                                                      │
│  ✓ Authentication session                           Connected        │
│  ✓ Noxyn API                                        Connected        │
│  ✓ Evidence database                                Ready            │
│  ✓ Artifact storage                                 Ready            │
│  ◌ Solari Sandbox executor                          Checking…        │
│  ✓ Python registry                                  Reachable         │
│  ✓ npm registry                                     Reachable         │
│  ✓ Go module source                                 Reachable         │
│                                                                      │
│  Solari credentials are managed by this deployment.                  │
│  They are never requested or shown in the browser.                   │
│                                                                      │
│                                     [ Back ] [ Check again ]         │
└──────────────────────────────────────────────────────────────────────┘
```

Ready:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ ✓ Ready to verify                                                    │
│ All required services responded successfully.                        │
│                                           [ Continue to review ]     │
└──────────────────────────────────────────────────────────────────────┘
```

Executor unavailable:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Runtime verification is temporarily unavailable                     │
│ Static comparison can run, but runtime results will be UNVERIFIED.   │
│ No configuration has been lost.                                     │
│            [ Check again ] [ Continue with static analysis only ]    │
└──────────────────────────────────────────────────────────────────────┘
```

The recommended controlled-run path is `Check again`. Continuing must preserve
`UNVERIFIED`; it must never turn the outage into a subject failure.

### O7 — Review and save

Route: `/onboarding?step=review`

```text
┌──────────────────────────────────────────────────────────────────────┐
│  Review configuration                                Step 7 of 7     │
│  ✓ Workspace  ✓ Project  ✓ Product  ✓ Sources                       │
│  ✓ Packages   ✓ Readiness  ● Review                                  │
│                                                                      │
│  Workspace        Dharun's workspace                                 │
│  Project          Solari                                             │
│  Product          Sandbox                                            │
│  Scenario         Controlled API evolution                           │
│  Sources          6 configured                                       │
│  Languages        Python, TypeScript, Go                             │
│  Runtime          Fresh Solari Sandboxes                             │
│  Executor         Ready                                              │
│                                                                      │
│  First run plan                                                      │
│  1. Snapshot and hash configured sources.                            │
│  2. Compare API, SDK, docs, and cookbook capabilities.                │
│  3. Execute suspicious runnable examples in fresh sandboxes.          │
│  4. Preserve evidence; never merge or publish a proposal.             │
│                                                                      │
│  Estimated runtime     2–5 minutes                                   │
│  Estimated sandboxes  Up to 3, plus fresh fix verification           │
│                                                                      │
│                   [ Back ] [ Save and open project ]                 │
└──────────────────────────────────────────────────────────────────────┘
```

Saving creates Sandbox configuration version 1, completes onboarding, and
opens the Solari project overview. It does not start sandbox work without a
separate final user action.

## 7. Project overview and runs

### P1 — Solari project overview

Route: `/projects/{projectId}`

```text
┌──────────────────────────────────────────────────────────────────────┐
│ NOXYN                     Project: Solari              [ DV ▾ ]     │
├──────────────────────────────────────────────────────────────────────┤
│ Solari                                                               │
│ Official Solari developer platform ecosystem                         │
│                                                                      │
│ Products                                                   1 active  │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ SANDBOX                                             CONFIGURED ✓ │ │
│ │ Disposable execution and API-ecosystem verification              │ │
│ │                                                                  │ │
│ │ Configuration v1 · 6 sources · Python, TypeScript, Go            │ │
│ │ Runs 0 · Last verified Never                                     │ │
│ │                                               [ Open Sandbox → ] │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ Future Solari products                                               │
│ Browser — not available in MVP · Desktop — not available in MVP      │
└──────────────────────────────────────────────────────────────────────┘
```

This screen proves that Sandbox belongs to Solari rather than being the
project itself. The future-product row is informational and has no dead action.

### R1 — First-run empty state

Route: `/projects/{projectId}/products/{productId}/runs`

```text
┌──────────────────────────────────────────────────────────────────────┐
│ NOXYN   Solari / Sandbox     Runs   Configuration      [ DV ▾ ]     │
├──────────────────────────────────────────────────────────────────────┤
│ Verification runs                                  [ Start run ]    │
│ Prove whether Solari's SDKs, docs, and examples work together.       │
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │                     No runs yet                                  │ │
│ │                                                                  │ │
│ │ Your configuration is ready. Start with the controlled scenario  │ │
│ │ to see the detected → reproduced → verified lifecycle.           │ │
│ │                                                                  │ │
│ │                    [ Start first run ]                            │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ Configuration v1 · 6 sources · Python, TypeScript, Go                │
└──────────────────────────────────────────────────────────────────────┘
```

### R2 — Start-run drawer

```text
┌────────────────────────── Start verification ────────────────────────┐
│ Scenario                                                             │
│ (●) Controlled API evolution                                       │
│     Reproducible fixture; labelled throughout the run.               │
│ ( ) Current configured Solari ecosystem                             │
│     Uses approved current/pinned revisions.                          │
│                                                                      │
│ Languages                                                            │
│ [✓] Python   [✓] TypeScript   [✓] Go                                │
│                                                                      │
│ [✓] Reproduce suspected drift in fresh Solari Sandboxes              │
│                                                                      │
│ Configuration   v1                                                   │
│ Expected time   2–5 minutes                                          │
│ Sandbox use     Up to 3; fixes use separate new sandboxes            │
│                                                                      │
│ A run cannot edit, merge, publish, or deploy source code.            │
│                         [ Cancel ] [ Start verification ]             │
└──────────────────────────────────────────────────────────────────────┘
```

Confirming durably creates the run and redirects to the product-scoped
`/projects/{projectId}/products/{productId}/runs/{runId}` route.

### R3 — Returning-user dashboard

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Verification runs                                  [ Start run ]    │
│                                                                      │
│ Latest                                                               │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Controlled API evolution                       FIXES VERIFIED ✓  │ │
│ │ Run 01J… · Configuration v1 · 2m 18s                            │ │
│ │ 14 capabilities · 2 reproduced · 2 fix verified                 │ │
│ │                                              [ Open run → ]      │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ History                                                              │
│ ┌──────────────┬──────────────┬────────────┬────────────┬──────────┐ │
│ │ Started      │ Scenario     │ State      │ Findings   │ Runtime  │ │
│ ├──────────────┼──────────────┼────────────┼────────────┼──────────┤ │
│ │ Today 10:24  │ Controlled   │ Completed  │ 2 verified │ 5 pass   │ │
│ │ Yesterday    │ Current      │ Unverified │ 1 suspect  │ 1 infra  │ │
│ └──────────────┴──────────────┴────────────┴────────────┴──────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

## 8. Live verification

### V1 — Queued

Route: `/projects/{projectId}/products/{productId}/runs/{runId}`

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Runs / 01J…                                      QUEUED             │
├──────────────────────────────────────────────────────────────────────┤
│ Controlled API evolution                                             │
│ Run created. A verification worker will claim it shortly.            │
│                                                                      │
│  ◌ Waiting for worker                                                │
│                                                                      │
│ Configuration v1 · Created 10:24:03                  [ Cancel run ] │
└──────────────────────────────────────────────────────────────────────┘
```

### V2 — In progress

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Runs / 01J…                                      VERIFYING          │
├──────────────────────────────────────────────────────────────────────┤
│ Controlled API evolution                                             │
│ Started 10:24 · Last update 3 seconds ago                             │
│                                                                      │
│  ✓ Snapshot configured sources                         6 / 6         │
│  ✓ Extract canonical capabilities                       14           │
│  ✓ Compare API, SDKs, docs, and examples            3 suspected     │
│  ● Verify Python                                    running          │
│  ○ Verify TypeScript                               queued           │
│  ○ Verify Go                                       queued           │
│  ○ Build final report                              waiting          │
│                                                                      │
│ Current: installing exact Python package in a fresh sandbox…         │
│ You can leave; the run will continue.                [ Cancel run ] │
└──────────────────────────────────────────────────────────────────────┘
```

The page polls durable state. A refresh or closed tab does not stop the job.

### V3 — Cancellation

```text
┌────────────────────────── Cancel this run? ──────────────────────────┐
│ Noxyn will stop new work, terminate bounded active work, and clean   │
│ up sandboxes. Evidence already produced will remain.                 │
│                         [ Keep running ] [ Cancel run ]               │
└──────────────────────────────────────────────────────────────────────┘
```

```text
CANCEL REQUESTED
       │
       ▼
Stop new work → terminate active work → clean both sandbox levels
       │
       ▼
CANCELLED · partial evidence preserved · cleanup result visible
```

## 9. Completed results

### C1 — Run overview and capability matrix

Route: `/projects/{projectId}/products/{productId}/runs/{runId}`

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Runs / 01J…                             COMPLETED · 2m 18s          │
├──────────────────────────────────────────────────────────────────────┤
│ Controlled API evolution · Fixture · Configuration v1                │
│                                                                      │
│ ┌──────────────┬──────────────┬──────────────┬────────────────────┐  │
│ │ Capabilities │ Suspected    │ Reproduced   │ Fix verified       │  │
│ │ 14           │ 3            │ 2            │ 0                  │  │
│ └──────────────┴──────────────┴──────────────┴────────────────────┘  │
│                                                                      │
│ Attention required                                                   │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ sandbox.create / Python cookbook             REPRODUCED          │ │
│ │ Runtime TypeError against exact package      [ Review → ]        │ │
│ ├──────────────────────────────────────────────────────────────────┤ │
│ │ sandbox.create / TypeScript docs             REPRODUCED          │ │
│ │ Runtime argument mismatch                    [ Review → ]        │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ Capability matrix                                                    │
│ ┌────────────────┬────┬────┬────┬────┬────┬────┬─────────┐          │
│ │ Capability     │ API│ Py │ TS │ Go │Docs│ Ex │ Runtime │          │
│ ├────────────────┼────┼────┼────┼────┼────┼────┼─────────┤          │
│ │ sandbox.create │ ✓  │ ✓  │ ✓  │ ✓  │ !  │ !  │ 2 fail │          │
│ │ commands.run   │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ 3 pass │          │
│ │ files.write    │ ✓  │ ✓  │ ✓  │ ✓  │ ✓  │ —  │ 3 pass │          │
│ └────────────────┴────┴────┴────┴────┴────┴────┴─────────┘          │
│ [ All ] [ Suspected ] [ Reproduced ] [ Verified ]       Search…     │
└──────────────────────────────────────────────────────────────────────┘
```

Proposal work is an explicit user-driven continuation attached to the
completed run; the original execution remains immutable.

### C2 — Capability evidence drawer

```text
┌────────────────────── Capability evidence ───────────────────────────┐
│ sandbox.create / Python cookbook                    REPRODUCED       │
│                                                                      │
│ Source     examples/sandbox-code-interpreter-py/main.py              │
│ Revision   abc123… · SHA-256 91f… · line 23                           │
│ Observed   client.create(old_argument=2048)                          │
│ Expected   client.create(new_argument=2048)                          │
│ Runtime    Infrastructure PASS · Subject FAIL · Exit 1               │
│                                                                      │
│                  [ View execution ] [ Review finding ]               │
└──────────────────────────────────────────────────────────────────────┘
```

### C3 — Execution evidence

Route: `/projects/{projectId}/products/{productId}/runs/{runId}/executions/{executionId}`

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Run 01J… / Python cookbook                         REPRODUCED       │
├──────────────────────────────────────────────────────────────────────┤
│ Infrastructure                         Subject                       │
│ PASS                                   FAIL                          │
│                                                                      │
│ Sandbox          sbx_01…                                             │
│ Package          solari-sandbox==PINNED                              │
│ Source           main.py · SHA-256 91f…                              │
│ Exit / duration  1 / 8.4s                                            │
│ Cleanup          PASS                                                │
│                                                                      │
│ stdout  ┌──────────────────────────────────────────────────────────┐ │
│         │ creating sandbox…                                        │ │
│         └──────────────────────────────────────────────────────────┘ │
│ stderr  ┌──────────────────────────────────────────────────────────┐ │
│         │ TypeError: unexpected keyword argument …                 │ │
│         └──────────────────────────────────────────────────────────┘ │
│                                                                      │
│ Evidence SHA-256 b72…                    [ Back ] [ Review finding ] │
└──────────────────────────────────────────────────────────────────────┘
```

### C4 — Infrastructure failure

Same execution route, different truthful result:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Run 01J… / TypeScript docs                         UNVERIFIED       │
├──────────────────────────────────────────────────────────────────────┤
│ Infrastructure FAIL                   Subject NOT RUN                │
│                                                                      │
│ Failed stage   Create verification sandbox                           │
│ Safe error     Solari capacity temporarily unavailable               │
│ Attempts       2 of 2                                                │
│                                                                      │
│ No conclusion was produced about the documentation.                  │
│                         [ Back to run ] [ Retry execution ]           │
└──────────────────────────────────────────────────────────────────────┘
```

Retry creates a new attempt instead of overwriting the failed evidence.

## 10. Finding and fix verification

### F1 — Reproduced finding

Route: `/projects/{projectId}/products/{productId}/runs/{runId}/findings/{findingId}`

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Run 01J… / Finding                                   REPRODUCED      │
├──────────────────────────────────────────────────────────────────────┤
│ sandbox.create / Python cookbook                                     │
│                                                                      │
│ SUSPECTED ──► REPRODUCED ──○ FIX PROPOSED ──○ FIX VERIFIED          │
│                                                                      │
│ Why suspected                                                        │
│ The cookbook argument disagrees with the canonical capability.       │
│                                                                      │
│ How proved                                                           │
│ Fresh sandbox · exact package · source SHA 91f… · exit 1              │
│ [ Open execution evidence ]                                          │
│                                                                      │
│ Affected artifact                                                    │
│ examples/sandbox-code-interpreter-py/main.py:23                      │
│                                                                      │
│ A proposal will not edit the repository, open a PR, or merge code.   │
│                          [ Generate proposal ]                       │
└──────────────────────────────────────────────────────────────────────┘
```

### F2 — Proposal generation

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Creating a source-bound proposal…                                    │
│ ✓ Confirm current source hash                                        │
│ ● Build minimal deterministic patch                                  │
│ ○ Validate changed artifact                                          │
│                                                                      │
│ This does not modify your checkout.                                  │
└──────────────────────────────────────────────────────────────────────┘
```

### F3 — Review proposal

The finding route now has state `FIX_PROPOSED`.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Run 01J… / Finding                                FIX PROPOSED      │
├──────────────────────────────────────────────────────────────────────┤
│ SUSPECTED ──► REPRODUCED ──► FIX PROPOSED ──○ FIX VERIFIED          │
│                                                                      │
│ Proposed change                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ - await client.create(old_argument=2048)                         │ │
│ │ + await client.create(new_argument=2048)                         │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ Original SHA-256   91f…        Proposed SHA-256  7ab…                 │
│ Changed files      1           Changed lines      2                   │
│                                                                      │
│ Verification uses the same package in a NEW Solari sandbox.          │
│                 [ Dismiss ] [ Verify proposed fix ]                  │
└──────────────────────────────────────────────────────────────────────┘
```

Dismissal retains evidence and may collect a short reason.

### F4 — Fresh fix verification

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Verifying proposed fix                                               │
│ Original execution   sbx_01… · exit 1                                │
│ New verification     fresh sandbox                                   │
│                                                                      │
│ ✓ Validate source binding                                            │
│ ✓ Create new Solari sandbox                                          │
│ ✓ Install exact package                                              │
│ ● Apply proposed bytes and execute                                   │
│ ○ Capture evidence and clean up                                      │
│                                                                      │
│ You can leave; verification will continue.                           │
└──────────────────────────────────────────────────────────────────────┘
```

### F5 — Fix verified

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Run 01J… / Finding                               FIX VERIFIED ✓     │
├──────────────────────────────────────────────────────────────────────┤
│ SUSPECTED ──► REPRODUCED ──► FIX PROPOSED ──► FIX VERIFIED          │
│                                                                      │
│ Before                                After                          │
│ Infrastructure PASS                   Infrastructure PASS            │
│ Subject FAIL · exit 1                 Subject PASS · exit 0          │
│ Sandbox sbx_01…                       Fresh sandbox sbx_02…           │
│ Cleanup PASS                          Cleanup PASS                    │
│                                                                      │
│ Evidence: before b72… · proposal 7ab… · verification d31…            │
│                                                                      │
│ Noxyn verified this proposal. It did not change the repository.      │
│                  [ Back to run ] [ View verification evidence ]      │
└──────────────────────────────────────────────────────────────────────┘
```

### F6 — Proposed fix fails

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Proposed fix did not pass                            FIX PROPOSED    │
│ Infrastructure PASS · Subject FAIL · exit 1                          │
│ The finding remains reproduced; it is not marked fixed.              │
│              [ View evidence ] [ Generate revised proposal ]         │
└──────────────────────────────────────────────────────────────────────┘
```

## 11. Final run state

Returning to the run shows verified proposals without rewriting original
execution evidence.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Runs / 01J…                              FIXES VERIFIED ✓           │
├──────────────────────────────────────────────────────────────────────┤
│ Controlled API evolution                                             │
│ 14 capabilities · 3 suspected · 2 reproduced · 2 fix verified        │
│                                                                      │
│ Findings                                                             │
│ ✓ Python cookbook             FIX VERIFIED      [ Open → ]           │
│ ✓ TypeScript documentation    FIX VERIFIED      [ Open → ]           │
│ · One suspected claim passed runtime and was dismissed               │
│                                                                      │
│ All reproduced fixture drift has a sandbox-verified proposal.        │
│ [ View evidence summary ]                         [ Start new run ]   │
└──────────────────────────────────────────────────────────────────────┘
```

`FIXES VERIFIED` means proposals passed. It does not mean changes were merged
or deployed.

## 12. Configuration after onboarding

### S1 — Configuration overview

Route: `/projects/{projectId}/products/{productId}/configuration`

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Configuration                                      Version 1        │
│ Changes affect future runs. Existing runs keep their version.        │
│                                                                      │
│ Workspace                                                            │
│ Dharun's workspace                                      [ Rename ]  │
│                                                                      │
│ Project                                                              │
│ Solari · solari                                     [ View project ] │
│                                                                      │
│ Product                                                              │
│ Sandbox · type: sandbox                                              │
│                                                                      │
│ Official source preset                                               │
│ 6 sources configured                                    [ Review ]  │
│                                                                      │
│ Package targets                                                      │
│ Python PINNED · TypeScript PINNED · Go PINNED           [ Edit ]    │
│                                                                      │
│ Runtime executor                                                     │
│ ● Connected · checked 2 minutes ago                     [ Recheck ] │
│                                                                      │
│ Historical evidence remains bound to Configuration v1.               │
└──────────────────────────────────────────────────────────────────────┘
```

Editing reuses the onboarding source/package/review views and creates a new
immutable version.

### S2 — Save a new version

```text
┌──────────────────────── Save configuration v2? ──────────────────────┐
│ Future runs will use these versions:                                 │
│ Python       1.2.0 → 1.3.0                                           │
│ TypeScript   unchanged                                               │
│ Go           unchanged                                               │
│                                                                      │
│ Existing run evidence will not change.                               │
│                              [ Keep editing ] [ Save version 2 ]     │
└──────────────────────────────────────────────────────────────────────┘
```

## 13. Session, authorization, and common errors

### Session expiration

```text
Protected request → API 401 → hide protected data → sign in
                                                    │
                                                    ▼
                                        return to safe original route
```

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Your session has expired                                             │
│ Sign in again to continue. A running job continues in the background.│
│                                                     [ Sign in ]      │
└──────────────────────────────────────────────────────────────────────┘
```

### Unauthorized resource

```text
┌──────────────────────────────────────────────────────────────────────┐
│ This resource is unavailable                                        │
│ It may not exist or may belong to another workspace.                 │
│                                                    [ Back to runs ]  │
└──────────────────────────────────────────────────────────────────────┘
```

The response does not reveal whether another user's object exists.

### Recoverable API error

```text
┌──────────────────────────────────────────────────────────────────────┐
│ We couldn't load this page                                           │
│ No configuration, run, or evidence state was changed.                │
│                                            [ Back ] [ Try again ]    │
└──────────────────────────────────────────────────────────────────────┘
```

### Required source unavailable

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Run 01J…                                         FAILED             │
│ Noxyn could not snapshot a required configured source.               │
│ Failed source   API contract                                         │
│ Safe reason     Configured revision unavailable                      │
│ No partial comparison was presented as complete.                     │
│                      [ Review configuration ] [ Start new run ]      │
└──────────────────────────────────────────────────────────────────────┘
```

### Current scan finds no drift

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Current Solari scan                              COMPLETED ✓        │
│ No actionable drift was found in configured source revisions.        │
│ 14 capabilities aligned · 0 reproduced · 0 unverified                │
│ Noxyn does not manufacture findings to make a run interesting.       │
│                         [ View matrix ] [ Start another run ]         │
└──────────────────────────────────────────────────────────────────────┘
```

## 14. Responsive behavior

Desktop matrix rows become readable cards on a narrow screen:

```text
┌──────────────────────────────┐
│ sandbox.create              │
│ API          Aligned        │
│ Python       Aligned        │
│ TypeScript   Aligned        │
│ Go           Aligned        │
│ Docs         Suspected      │
│ Examples     Reproduced     │
│ Runtime      2 failed       │
│              [ Evidence → ] │
└──────────────────────────────┘
```

On mobile, navigation collapses, drawers become full-screen sheets, evidence
logs scroll within bounded regions, and destructive actions stay distinct.

## 15. Durable UX state

| Visible state | Durable owner |
|---|---|
| Signed in/out | Clerk session |
| Onboarding completion | Workspace/project/product setup record |
| Project identity | Solari project record |
| Product identity | Sandbox product record |
| Current configuration | Immutable Sandbox configuration version |
| Run queued/running/terminal | Verification run record |
| Stage progress | Run stage and job records |
| Static matrix cell | Stored comparison evidence |
| Infrastructure/subject result | Execution attempt |
| Finding lifecycle | Finding record |
| Proposal bytes and hash | Proposal artifact |
| Fix verification | Separate execution attempt |

The browser must not invent terminal states. Refreshing a page reconstructs the
same state from the API.

## 16. Complete screen transition map

```text
┌────────────┐      new user       ┌────────────┐      ┌────────────┐
│ SIGN IN A1 │────────────────────►│ SIGN UP A2 │─────►│ VERIFY A3  │
└─────┬──────┘                     └────────────┘      └──────┬─────┘
      │ authenticated                                      │
      └──────────────────────┬─────────────────────────────┘
                             ▼
                    ┌─────────────────┐
                    │ SETUP COMPLETE? │
                    └────┬───────┬────┘
                         │ no    │ yes
                         ▼       └───────────────────────────┐
                ┌─────────────────┐                         │
                │ WORKSPACE O1    │                         │
                └────────┬────────┘                         │
                         ▼                                  │
                ┌─────────────────┐                         │
                │ PROJECT O2      │                         │
                └────────┬────────┘                         │
                         ▼                                  │
                ┌─────────────────┐                         │
                │ PRODUCT O3      │                         │
                └────────┬────────┘                         │
                         ▼                                  │
                ┌─────────────────┐                         │
                │ SOURCES O4      │                         │
                └────────┬────────┘                         │
                         ▼                                  │
                ┌─────────────────┐                         │
                │ PACKAGES O5     │                         │
                └────────┬────────┘                         │
                         ▼                                  │
                ┌─────────────────┐                         │
                │ READINESS O6    │                         │
                └────────┬────────┘                         │
                         ▼                                  │
                ┌─────────────────┐                         │
                │ REVIEW O7       │                         │
                └────────┬────────┘                         │
                         ▼                                  │
                    ┌─────────────────┐                     │
                    │ SOLARI P1       │◄────────────────────┘
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ RUNS R1 / R3    │◄────────────────────────┐
                    └────────┬────────┘                         │
                             ▼                                  │
                    ┌─────────────────┐                         │
                    │ START RUN R2    │                         │
                    └────────┬────────┘                         │
                             ▼                                  │
                    ┌─────────────────┐                         │
                    │ LIVE V1 / V2    │                         │
                    └────────┬────────┘                         │
                             ▼                                  │
                    ┌─────────────────┐                         │
                    │ RESULTS C1      │                         │
                    └────┬───────┬────┘                         │
                         │       │                              │
              ┌──────────┘       └──────────┐                   │
              ▼                             ▼                   │
     ┌─────────────────┐          ┌─────────────────┐           │
     │ EVIDENCE C2-C4  │          │ FINDING F1      │           │
     └────────┬────────┘          └────────┬────────┘           │
              │                            ▼                    │
              │                   ┌─────────────────┐           │
              │                   │ PROPOSAL F2/F3  │           │
              │                   └────────┬────────┘           │
              │                            ▼                    │
              │                   ┌─────────────────┐           │
              │                   │ REVERIFY F4     │           │
              │                   └────────┬────────┘           │
              │                            ▼                    │
              │                   ┌─────────────────┐           │
              └──────────────────►│ VERIFIED F5/F6  │           │
                                  └────────┬────────┘           │
                                           ▼                    │
                                  ┌─────────────────┐           │
                                  │ FINAL SUMMARY   │───────────┘
                                  └─────────────────┘
```

Configuration changes stay separate from historical evidence:

```text
SANDBOX RUNS ──► CONFIGURATION S1 ──► EDIT PRODUCT STEPS ──► SAVE v2
  ▲                                              │
  └──────────── future runs use v2 ◄─────────────┘

Historical run on v1 ──► displays configuration v1 forever
```

## 17. Reliability-focused UX rules

1. Never call a finding broken until runtime reproduces it.
2. Never call a proposal fixed until a fresh sandbox verifies it.
3. Never present infrastructure failure as subject failure.
4. Never hide unavailable evidence; display `UNVERIFIED`.
5. Never collect `SOLARI_API_KEY` in a browser form.
6. Never imply a proposal was merged, published, or deployed.
7. Always label the controlled scenario as a fixture.
8. Show exact package versions and hashes beside runtime evidence.
9. Preserve progress across refreshes and session expiration.
10. Bind historical runs to their original configuration.
11. Confirm sandbox-consuming runs and cancellation.
12. Keep one obvious primary action on each screen.

## 18. MVP UX acceptance criteria

The experience is complete when:

1. A new user can register, verify identity, and resume onboarding.
2. A new user explicitly creates the Solari project.
3. The user explicitly adds Sandbox as Solari's first product.
4. A returning user bypasses onboarding and lands on the Solari project or
   most recently used Sandbox runs screen.
5. Users review approved Sandbox sources instead of arbitrary repositories.
6. Users choose approved package versions and supported languages.
7. Readiness reports runtime availability without exposing credentials.
8. Saving onboarding creates an immutable Sandbox configuration version.
9. Starting a run requires an explicit final action.
10. Runs continue across navigation, refresh, or session expiration.
11. Static suspicion, reproduced failure, infrastructure failure, and success
   are visually distinct.
12. Results link to exact sources, packages, sandboxes, and evidence hashes.
13. Proposal generation never implies repository modification.
14. Fix verification always uses a separate fresh sandbox attempt.
15. Final screens distinguish a verified proposal from a merged fix.
16. Configuration changes affect future runs only.
17. Empty, loading, failure, cancellation, no-drift, and unauthorized states
   all provide a clear recovery action.
