# Controlled fixtures

This directory contains immutable, content-hashed API-evolution fixtures.
Fixture results must always be labelled as controlled scenarios and never as
evidence of a current Solari defect.

`sandbox-create-evolution/runtime-python/main.py` is the executable Phase 5
consumer. Its intentional `memory` argument mismatch is the only subject
failure. The matching `replay/python-memory-failure.json` is deterministic CI
evidence bound to the source SHA-256 and `solari-sandbox==0.2.0`; it must never
be described as a live Solari execution.

`sandbox-create-evolution/runtime-typescript/main.mjs` is the aligned Phase 6
consumer. It uses the published `@solarisdk/sandbox@0.1.2` runtime contract,
including the required `baseUrl` constructor option and `memMb` create field.
Its checked-in passing replay is independently bound to that source SHA-256.

Phase 7 adds a second executable subject by extracting the one Python fence
from `stale-python-example/README.md`. Both reproduced Python surfaces receive
the same reviewed `memory` to `mem_mb` rename, and each proposed byte sequence
has an independent passing `FIX_VERIFY` replay. These proposal artifacts never
modify the checked-out fixture files.
