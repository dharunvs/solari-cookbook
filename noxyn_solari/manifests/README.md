# Reviewed manifests

This directory contains versioned, reviewed source manifests for the Solari
project and Sandbox product. The MVP does not accept arbitrary repository or
install-command input.

`sandbox-create-evolution.v1.json` is the static-analysis fixture retained for
Phase 4 evidence. `sandbox-create-evolution.v2.json` retains the Phase 5
Python-only execution contract. `sandbox-create-evolution.v3.json` adds the
aligned TypeScript subject and replay under that same bounded execution
contract. `sandbox-create-evolution.v4.json` adds the exact documentation
code-block subject plus source-bound fix-verification replays.
`sandbox-create-evolution.v5.json` adds the aligned Go runtime subject under
the same executor contract, with a deterministic replay fixture. The worker
uses v5 by default.

`current-configured-solari.v1.json` is the separately labelled current-mode
manifest. Its reviewed source identities and exact revisions are snapshot at
run time; it contains no execution plan, so development and CI remain
independent of live Solari execution.
