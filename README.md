# Solari Cookbook

Short, runnable examples for [Solari](https://getsolari.com) — cloud browsers,
sandboxes, and desktops behind one API key.

Every example in this repo is a complete program you can run in under a minute.
They are deliberately small: one idea each, no framework, no scaffolding to read
past. Copy one into your project and change the parts you care about.

## Examples

### Cloud browser

| Example | Language | What it shows |
| --- | --- | --- |
| [browser-quickstart-ts](examples/browser-quickstart-ts) | TypeScript | Launch a browser, open a page, read it |
| [browser-quickstart-py](examples/browser-quickstart-py) | Python | Launch a browser, open a page, read it |
| [browser-stealth-proxy-ts](examples/browser-stealth-proxy-ts) | TypeScript | Stealth mode + residential proxy egress |
| [browser-profiles-ts](examples/browser-profiles-ts) | TypeScript | Log in once, reuse the session forever |
| [browser-session-recording-py](examples/browser-session-recording-py) | Python | Record a session, download the replay |

### Sandbox

| Example | Language | What it shows |
| --- | --- | --- |
| [sandbox-quickstart-ts](examples/sandbox-quickstart-ts) | TypeScript | Run a command, write and read files |
| [sandbox-code-interpreter-py](examples/sandbox-code-interpreter-py) | Python | Stateful Python kernel for agent loops |
| [sandbox-port-preview-ts](examples/sandbox-port-preview-ts) | TypeScript | Expose a server in the VM on a public URL |

### Desktop

| Example | Language | What it shows |
| --- | --- | --- |
| [desktop-computer-use-py](examples/desktop-computer-use-py) | Python | Screenshot, click, and type on a Linux GUI |

## Running an example

Each directory is self-contained.

```bash
git clone https://github.com/solari-sdk/solari-cookbook.git
cd solari-cookbook/examples/browser-quickstart-ts

npm install                          # or: pip install -r requirements.txt
export SOLARI_API_KEY=slr_live_...   # grab one at console.getsolari.com
npm start                            # or: python main.py
```

One `slr_live_` key works across browsers, sandboxes, and desktops, and every
product bills to the same balance.

## Which product do I want?

- **Cloud browser** — you need a *web page*: scraping, testing, filling forms,
  anything Playwright or Puppeteer would do locally. Adds stealth, managed
  proxies, captcha solving, profiles, and session recording.
- **Sandbox** — you need to *run code*: an LLM's Python, an untrusted build, a
  data job. A headless microVM that boots from a snapshot in about a second.
- **Desktop** — you need a *screen*: computer-use agents, GUI apps, anything
  that has to be clicked. A sandbox plus X11 and a live VNC stream.

## Gotchas the examples encode

Things that cost you an afternoon if you meet them cold:

- **TypeScript: call `await solari.close()`.** The browser client keeps a
  loopback proxy open for connection retries. Skip the close and your script
  prints its output and then hangs forever instead of exiting.
- **Recording is per session, not per account.** Pass `recording: true` when you
  create the session; without it the replay endpoint 404s forever. The upload is
  async after release, so poll for ~30s before giving up.
- **Sandbox commands are not shell-interpreted.** `run("ls -la")` looks for a
  binary named `ls -la`. Put argv in `args`, or run `sh -c` explicitly.
- **`kill()`, not `close()`, ends a VM.** `close()` drops your local control
  channel; the VM keeps running until its idle timeout.
- **`timeoutMs` is a rolling idle window**, not a hard deadline — it resets on
  every use.

## Links

- Docs — [docs.getsolari.com](https://docs.getsolari.com)
- Console — [console.getsolari.com](https://console.getsolari.com)
- Changelog — [changelog.getsolari.com](https://changelog.getsolari.com)
- Questions — [hello@getsolari.com](mailto:hello@getsolari.com)

## Contributing

New examples are welcome. Keep them small, make them run end-to-end against the
real API, and put anything surprising in a comment right where it bites.

MIT licensed.

## Noxyn-Solari application development

This repository also contains the Noxyn-Solari MVP application foundation.
Noxyn analyzes Solari's Sandbox API ecosystem and uses fresh Solari Sandboxes
as its execution and verification layer.

Requirements:

- Node.js 22 with Corepack
- pnpm 9.15.0
- Python 3.12 and uv 0.11.19
- Docker with Compose

Start the local foundation:

```bash
nvm use
corepack enable
cp .env.example .env
pnpm install --frozen-lockfile
uv sync --all-packages --frozen
pnpm db:up
pnpm db:migrate
pnpm dev
```

For Clerk, create `apps/console/.env.local` from
`apps/console/.env.example` and add the two keys from your Clerk dashboard.
Do not place Clerk keys in the repository-root `.env.local`; the console file
is the one local source of truth. In development, the API reads that console
file after any root file so it verifies the same Clerk instance. Neither key is
sent to the browser except the intentionally public `NEXT_PUBLIC_` key.

The console runs at `http://localhost:3000`, and the API health endpoint is
`http://127.0.0.1:8000/health`. Keep `localhost` as the browser origin during a
session; `localhost` and `127.0.0.1` have separate Clerk cookies. The worker
writes a durable heartbeat to PostgreSQL and processes leased readiness jobs.

After onboarding, open **Sandbox runs** and start a verification. The default
`NOXYN_EXECUTOR_MODE=replay` deterministically reproduces the controlled Python
fixture in local development and CI. Replay evidence is prominently labelled
and cryptographically bound to the exact package version and source hash; it is
never presented as a live Solari execution. Local artifact bodies are written
below `.artifacts/noxyn` and are ignored by Git.

To execute the same bounded harness inside a fresh Solari Sandbox, set these
worker-only variables and restart the worker:

```bash
NOXYN_EXECUTOR_MODE=live
SOLARI_API_KEY=slr_live_...
SOLARI_API_BASE_URL=https://api.getsolari.com
```

The API key is passed to the sandbox command environment only. It is never
written to the fixture, browser bundle, logs, database, or artifacts. Live
execution is timeout-bound, output-limited and redacted, and the verification
sandbox is killed in a `finally` path.

The paid live integration test has an additional deliberate gate:

```bash
NOXYN_RUN_LIVE_TESTS=true uv run --all-packages pytest -m live
```

For the real authentication lifecycle, configure Clerk in the console
environment (`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`). The API
uses Clerk's official backend SDK with the same secret; no additional JWT
variables are required. The local browser journey is deterministic and
explicitly test-only:

```bash
pnpm test:e2e
```

It enables `NOXYN_E2E_AUTH_BYPASS` only for the spawned local processes; the
bypass cannot activate when `APP_ENV=production`.

Run the same validation used by CI:

```bash
pnpm verify
```

Regenerate the FastAPI OpenAPI document and TypeScript client after changing
an API route or schema:

```bash
pnpm openapi:generate
```
