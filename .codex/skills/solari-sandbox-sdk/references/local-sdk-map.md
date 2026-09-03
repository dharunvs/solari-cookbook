# Local Solari Sandbox SDK map

This reference records what the repository currently contains. It is not a
claim that every example matches the latest published SDK.

## TypeScript

Current package identity in Sandbox examples:

```text
@solarisdk/sdk ^0.1.2
```

Relevant artifacts:

- `examples/sandbox-quickstart-ts/index.ts`
- `examples/sandbox-quickstart-ts/package.json`
- `examples/sandbox-port-preview-ts/index.ts`
- `examples/sandbox-port-preview-ts/package.json`

Capabilities currently demonstrated:

```text
new SolariClient({ apiKey })
client.sandboxes.create({ template, timeoutMs })
sandbox.connect()
sandbox.commands.run(executable, { args })
sandbox.files.write(path, content)
sandbox.files.readText(path)
sandbox.files.list(path)
sandbox.previewUrl(port)
sandbox.kill()
```

Repository cautions:

- Commands are documented as executable plus argv, not shell-interpreted
  command strings.
- Starting a background server currently uses an explicit reviewed `sh -c`.
- The root README says the TypeScript client should be closed to avoid a
  lingering loopback proxy, while the Sandbox examples currently show only
  sandbox cleanup. Verify this against the exact installed package before
  treating either behavior as authoritative.

## Python

Current package identity:

```text
solari-sandbox >=0.2.0
```

Relevant artifacts:

- `examples/sandbox-code-interpreter-py/main.py`
- `examples/sandbox-code-interpreter-py/requirements.txt`

Capabilities currently demonstrated:

```text
SandboxClient(api_key, base_url)
client.create(template, timeout_ms)
sandbox.connect()
sandbox.create_code_context("python")
sandbox.run_code(code, context_id=...)
sandbox.kill()
```

Repository cautions:

- The standalone Python client currently receives an explicit API base URL.
- Code execution output is shown as a result-item list rather than a single
  top-level stdout value.
- The example uses an async client context and still kills the remote Sandbox
  explicitly in `finally`.

## Go

The MVP specification requires Go before V1 completion, but this cookbook does
not currently contain a runnable Go Sandbox example or pinned Go module.

Do not derive Go names mechanically from Python or TypeScript. Obtain and pin
the approved Go module and inspect its actual exported API before implementing
or claiming parity.

## Runtime endpoints and secrets

The current examples refer to:

```text
API base URL: https://api.getsolari.com
Secret name:  SOLARI_API_KEY
```

Treat both as configuration. The secret belongs only in a reviewed server or
worker environment and must never appear in browser state, logs, persisted
commands, or evidence artifacts.

## Evidence reminder

When an example and a published package disagree, preserve both identities:

```text
source path + source revision + source SHA-256
package name + exact package version
execution attempt + infrastructure state + subject state
```

That disagreement is the Noxyn product signal; do not erase it by updating the
fixture or expected result during verification.
