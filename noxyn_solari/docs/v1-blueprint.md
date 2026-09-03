Yes. I’d lock **Noxyn-Solari V1** to exactly this scope:

> **One startup → one product → three SDK languages → five source/evidence classes.**

The goal is not to rebuild all of Noxyn. It is to make one narrow workflow extremely trustworthy and demoable.

# 1. Product definition

**Noxyn-Solari** answers:

> **Does Solari Sandbox tell developers the same thing everywhere, and does that code actually work?**

The entire system is:

```text
                    SOLARI / SANDBOX

                         Contract
                            │
                            ▼
                  Canonical capabilities
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
       Python          TypeScript            Go
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                    Docs + Examples
                            │
                            ▼
                    Static comparison
                            │
                    suspected drift
                            │
                            ▼
                 Solari runtime verification
                            │
                    ┌───────┴───────┐
                    ▼               ▼
                  PASS          REPRODUCED
                                    │
                                    ▼
                              Fix proposal
                                    │
                                    ▼
                              Re-verification
```

---

# 2. Locked source model

```text
Solari
└── Sandbox
    │
    ├── Contract
    │   └── API Reference
    │
    ├── Official Documentation
    │   ├── Product guides
    │   └── SDK references
    │       ├── Python
    │       ├── TypeScript
    │       └── Go
    │
    ├── Published SDK Artifacts
    │   ├── Python → PyPI: solari-sandbox
    │   ├── TypeScript → npm: @solarisdk/sandbox
    │   └── Go → Go module: solari-sandbox-go
    │
    ├── Examples
    │   └── solari-cookbook
    │
    └── Verification
        └── Solari Sandbox runtime
            ├── Python
            ├── TypeScript
            └── Go
```

Don't add Browser, VM, Rust, C++, changelog, source repos, GitHub integrations, auth, organizations, etc. yet.

---

# 3. Core unit: Capability

Do **not** compare whole documents or whole packages.

Normalize everything into canonical Sandbox capabilities.

For example:

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

Each capability becomes one row.

Conceptually:

```text
Capability
────────────────────────────
id              commands.run
product         sandbox

Contract
  supported     yes
  evidence      API reference location

Python
  supported     yes
  sdk_name      Commands.run
  evidence      PyPI artifact

TypeScript
  supported     yes
  sdk_name      commands.run
  evidence      npm declaration

Go
  supported     yes
  sdk_name      Commands.Run
  evidence      Go module

Docs
  claims        [...]

Examples
  usages        [...]

Runtime
  python        ?
  typescript    ?
  go            ?
```

This semantic layer is essential because:

```text
memMb
mem_mb
MemMB
```

can represent the same thing.

Literal-name comparison would generate garbage findings.

---

# 4. Pipeline

Build one deterministic pipeline:

```text
DISCOVER
   ↓
SNAPSHOT
   ↓
EXTRACT
   ↓
NORMALIZE
   ↓
MAP
   ↓
COMPARE
   ↓
VERIFY
   ↓
REPORT
```

## Stage 1 — Discover

For V1, discovery should actually be mostly **configured**, not intelligent.

Have a manifest:

```yaml
startup: solari
product: sandbox

contract:
  - <api-reference>

documentation:
  product_guides:
    - <sandboxes>
    - <snapshots>
    - <templates>
  sdk_references:
    python: ...
    typescript: ...
    go: ...

packages:
  python: solari-sandbox
  typescript: "@solarisdk/sandbox"
  go: github.com/solari-sdk/solari-sandbox-go

examples:
  repo: https://github.com/solari-sdk/solari-cookbook
```

Don't waste contest time building automatic company discovery.

---

# 5. Snapshot everything

Every run freezes what was inspected.

For every source retain:

```text
source ID
source type
URL/package identifier
version
retrieved_at
content hash
raw artifact
```

Example:

```text
npm:@solarisdk/sandbox
version: 0.x.y
sha256: abc...

pypi:solari-sandbox
version: 0.x.y
sha256: def...

go:solari-sandbox-go
version: v0.x.y
sha256: ghi...
```

This matches the evidence-oriented design your current Noxyn already uses: immutable source snapshots, hashes, provenance, and evidence-backed matrix cells. 

---

# 6. Extract each source differently

## Contract extractor

Input:

```text
Solari API reference
```

Output:

```text
canonical operation
HTTP method/path
request fields
response fields
required/optional
types
errors
```

Example:

```text
sandbox.create

POST /sandboxes

request:
  template: string?
  cpu: number?
  memMb: number?

response:
  id: string
  ...
```

This becomes the authority.

---

## Python package extractor

Download the exact PyPI artifact.

Extract:

```text
package version
modules
exports
classes
methods
function signatures
type annotations
models
enums
```

Use static parsing where possible.

Runtime reflection can supplement:

```python
inspect.signature(...)
```

but shouldn't be your only evidence.

---

## TypeScript package extractor

Use the published npm artifact.

Prefer:

```text
package.json
exports
.d.ts files
public interfaces
classes
methods
function signatures
types
enums
```

The `.d.ts` surface should be the primary static SDK evidence.

Compiled JS is secondary.

---

## Go extractor

Download the published Go module.

Parse:

```text
exported types
structs
interfaces
functions
methods
parameters
return types
constants
```

For V1 you don't need an additional GitHub-source concept.

---

# 7. Documentation extraction

Treat docs as claims about capabilities.

For every relevant section/code block:

```text
source page
heading
language
code block
referenced capability
line/location
content hash
```

Example:

```text
Page:
Sandboxes → Commands

Language:
Python

Capability:
commands.run

Claim:
sbx.commands.run(...)
```

Separate:

```text
Product guide
```

from:

```text
SDK reference
```

because disagreement between those two is itself interesting.

---

# 8. Examples extraction

Cookbook should be treated as **runnable consumer code**, not ordinary documentation.

For each example:

```text
example ID
language
path
dependencies
capabilities used
entry command
source hash
```

Example:

```text
sandbox-code-interpreter-py

language: python
entrypoint: main.py

capabilities:
  sandbox.create
  code.run
  sandbox.kill
```

This gives Noxyn an execution target automatically.

---

# 9. Static comparison

Now create your first useful matrix.

```text
                    CONTRACT   PYTHON   TS    GO    DOCS   EXAMPLES

sandbox.create         ✓         ✓      ✓     ✓      ✓        ✓
commands.run           ✓         ✓      ✓     ✓      ⚠        ✓
files.write            ✓         ✓      ✓     ✓      ✓        —
snapshot               ✓         ✓      ✓     N/E    ✓        ✓
```

Use only a small number of states:

```text
ALIGNED
SUSPECTED
NOT_EXPECTED
UNVERIFIED
```

Don't call something broken yet.

Static analysis only gives:

> **SUSPECTED**

Your current Noxyn already has the useful distinction between `present`, `missing`, `conflict`, `unverified`, and `not_expected`; keep that philosophy rather than forcing every blank cell into a failure. 

---

# 10. Solari runtime verification

This is the new heart of Noxyn-Solari.

For each suspected runnable artifact:

```text
Noxyn controller
      ↓
create clean Solari Sandbox
      ↓
install exact published SDK
      ↓
materialize minimal test
      ↓
execute
      ↓
capture evidence
      ↓
cleanup
```

Use separate consumers:

```text
Python verification
   → fresh sandbox

TypeScript verification
   → fresh sandbox

Go verification
   → fresh sandbox
```

For V1, one sandbox **per language per verification run** is lean enough.

You don't need one sandbox for every individual method yet.

---

# 11. Testing Solari from inside Solari

There are effectively two sandboxes involved when testing `sandbox.create`.

```text
Noxyn
  │
  ▼
Verification Sandbox
  │
  │ contains:
  │ Python / npm / Go SDK
  │
  ▼
Solari API
  │
  ▼
Subject Sandbox
```

Example:

```text
Verification sandbox
     ↓
pip install solari-sandbox
     ↓
python test_create.py
     ↓
Solari SDK creates sbx_test_...
     ↓
assert expected response
     ↓
kill sbx_test_...
```

Then finally destroy the **verification sandbox** too.

That recursive story is actually great:

> Noxyn uses Solari Sandboxes to verify the Solari Sandbox SDK.

---

# 12. Runtime result model

This needs to be designed correctly from day one.

Do not model:

```text
exit code != 0
=
verification infrastructure failed
```

You need two separate results.

```text
VerificationExecution

infrastructure:
    PASS | FAIL

subject:
    PASS | FAIL | NOT_RUN
```

Example:

```text
Infrastructure
─────────────────
sandbox created       ✓
package installed     ✓
test executed         ✓
logs collected        ✓
cleanup complete      ✓

Subject
─────────────────
docs example          ✕

Conclusion
─────────────────
BREAKAGE REPRODUCED
```

Versus:

```text
Infrastructure
─────────────────
sandbox creation      ✕

Subject
─────────────────
NOT RUN

Conclusion
─────────────────
INFRASTRUCTURE FAILURE
```

This distinction is non-negotiable.

---

# 13. Runtime evidence

Store:

```text
verification ID
language

Solari sandbox ID
SDK package
SDK version

source being tested
source hash

command
exit code

stdout
stderr

started_at
duration

subject result
infrastructure result

cleanup result
```

Keep hashes/logs available, but don't put all of them on the main screen.

---

# 14. State machine

For every finding:

```text
SUSPECTED
    ↓
REPRODUCED
    ↓
FIX PROPOSED
    ↓
FIX VERIFIED
```

Alternative paths:

```text
SUSPECTED
    ↓
RUNTIME PASSED
    ↓
FALSE POSITIVE / ALIGNED
```

or:

```text
SUSPECTED
    ↓
INFRASTRUCTURE FAILED
    ↓
UNVERIFIED
```

Never convert infrastructure failures into product breakage.

---

# 15. Fix scope for V1

Be conservative.

Noxyn-Solari may propose changes to:

```text
Cookbook examples
documentation snippets
```

very naturally.

For SDK problems where source is unavailable:

```text
Published Python SDK broken
```

Noxyn should produce:

```text
REPRODUCED SDK CONFLICT
+
recommended change
+
runtime evidence
```

not pretend it can patch the private Python SDK repository.

For the contest demo, select a controlled case where at least one affected **example/docs artifact can actually be patched and re-run**.

---

# 16. Fix verification

The rule is simple:

> A proposal is not verified until the corrected consumer code runs in a fresh Solari environment.

```text
failure
   ↓
generate patch
   ↓
apply to isolated copy
   ↓
NEW Solari sandbox
   ↓
install exact SDK
   ↓
execute corrected artifact
   ↓
PASS
   ↓
FIX VERIFIED
```

Do not reuse the previous sandbox for the final proof.

---

# 17. UI: only four important screens

For this lean version I would simplify even further than our earlier UX.

## Screen 1 — Runs

```text
Noxyn-Solari

Solari / Sandbox

Latest verification

1 capability changed
3 suspected
2 reproduced
2 verified proposals

[ Open verification ]
```

---

## Screen 2 — Matrix

This is the primary screen.

```text
Solari / Sandbox

                 Contract Python TS  Go  Docs Examples Runtime

sandbox.create      ✓       ✓    ✓   ✓    ✓      ✕       ✕
commands.run        ✓       ✓    ✓   ✓    ✓      ✓       ✓
files.write         ✓       ✓    ✓   ✓    ✓      —       ✓
```

Click any cell for evidence.

---

## Screen 3 — Verification

```text
Runtime verification

Python cookbook                   REPRODUCED

Sandbox
sbx_01...

Package
solari-sandbox==x.y.z

Command
python main.py

Exit
1

TypeError: ...

[ Evidence ]
```

And show running states when applicable.

---

## Screen 4 — Proposal / Result

```text
Python cookbook

REPRODUCED
      ↓
FIX PROPOSED

- old_call(...)
+ new_call(...)

      ↓

Fresh Solari verification

Exit 0

FIX VERIFIED ✓
```

That's enough for the challenge.

---

# 18. Suggested backend modules

Keep implementation boundaries boring and obvious:

```text
noxyn_solari/
│
├── sources/
│   ├── contract.py
│   ├── docs.py
│   ├── examples.py
│   └── packages/
│       ├── python.py
│       ├── typescript.py
│       └── go.py
│
├── normalize/
│   ├── capabilities.py
│   └── mappings.py
│
├── compare/
│   ├── engine.py
│   └── findings.py
│
├── verification/
│   ├── executor.py
│   ├── solari.py
│   ├── python.py
│   ├── typescript.py
│   └── go.py
│
├── remediation/
│   ├── propose.py
│   └── verify.py
│
└── models/
    ├── sources.py
    ├── capabilities.py
    ├── evidence.py
    └── runs.py
```

If you're integrating into current Noxyn instead, adapt these concepts to the existing boundaries rather than creating a second architecture.

Your existing Noxyn already separates workers, artifact storage, normalization, evidence, remediation and isolated execution, so Solari should fit into those seams rather than bypassing them. 

---

# 19. Don't use AI for everything

Make this deterministic first:

```text
package extraction
type/signature extraction
exact versions
docs code-block extraction
test execution
exit codes
hashing
```

Use an LLM only for:

```text
semantic capability matching
```

when deterministic mapping cannot decide whether:

```text
Python SandboxClient.create()
```

and:

```text
POST /sandboxes
```

represent the same capability.

That is also consistent with current Noxyn's design: deterministic analysis runs first and Codex only assists unresolved mappings, with deterministic validation afterward. 

---

# 20. One controlled demo

Don't depend on discovering a real Solari bug.

Ship a labelled reproducible scenario:

```text
Scenario:
Sandbox.create evolves
```

Snapshot:

```text
Contract              new behavior
Python SDK             aligned
TypeScript SDK         aligned
Go SDK                 aligned

Product guide          aligned
Python cookbook        stale
Docs snippet           stale
```

Run:

```text
Noxyn static scan

2 SUSPECTED
       ↓

Solari execution

2 REPRODUCED
       ↓

Noxyn proposals

2 FIX PROPOSED
       ↓

fresh Solari environments

2 FIX VERIFIED
```

Separately, allow:

```text
Scan current Solari
```

which checks the live/current ecosystem for genuine drift.

This gives you both:

**reliable demo + genuine product capability.**

---

# 21. Definition of done

I would consider Noxyn-Solari contest-ready when this exact command works:

```bash
SOLARI_API_KEY=... pnpm demo
```

and produces:

```text
✓ Solari sources snapshotted

✓ Contract normalized

✓ Python SDK analyzed
✓ TypeScript SDK analyzed
✓ Go SDK analyzed

✓ Documentation analyzed
✓ Cookbook analyzed

3 suspected inconsistencies

Solari verification:
✓ 1 passed
✕ 2 reproduced

2 proposals generated

Solari re-verification:
✓ 2 / 2 proposals verified

Run complete.
```

And the UI shows the same result.

---

## The blueprint in one diagram

```text
                         SOLARI
                           │
                        SANDBOX
                           │
              ┌────────────┴────────────┐
              │                         │
           SOURCES                 VERIFICATION
              │                         │
    ┌─────────┼────────────┐            │
    │         │            │            │
 Contract    Docs       Examples        │
    │         │            │            │
    │    Published SDKs    │            │
    │     ┌───┼───┐        │            │
    │     Py  TS  Go       │            │
    │         │            │            │
    └─────────┴──────┬─────┘            │
                     ▼                  │
              Normalize into            │
               capabilities             │
                     │                  │
                     ▼                  │
                  Compare               │
                     │                  │
                SUSPECTED               │
                     │                  │
                     └──────────────► Solari Sandbox
                                        │
                                   install SDK
                                   run consumer
                                   capture evidence
                                        │
                             ┌──────────┴─────────┐
                             ▼                    ▼
                           PASS              REPRODUCED
                                                 │
                                            propose fix
                                                 │
                                         fresh sandbox
                                                 │
                                          FIX VERIFIED
```

That is the version I would lock and hand to Codex as the implementation target.
