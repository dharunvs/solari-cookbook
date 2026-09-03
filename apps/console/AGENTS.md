# Console guidance

These rules apply to the authenticated Next.js console.

- Read the root `AGENTS.md`, `DESIGN.md`, and
  `noxyn_solari/docs/mvp-ux-lifecycle.md` before implementing screens.
- Preserve the route hierarchy
  `/projects/{projectId}/products/{productId}/...`.
- Use Server Components by default. Add client boundaries only for actual
  interaction, browser APIs, or live polling.
- Read version-matched Next.js documentation from `node_modules/next/dist/docs/`
  before using framework APIs.
- Consume the generated API client. Do not query PostgreSQL or duplicate API
  schemas in frontend code.
- Clerk establishes the session; authorization outcomes still come from the
  API. Never render protected cached data after a 401 or 403.
- Keep `SOLARI_API_KEY` and all worker credentials out of client bundles,
  Server Actions, form fields, browser storage, and rendered errors.
- Follow `DESIGN.md` tokens, the Tailwind v4 docs skill, and the Vercel React
  and web-design review skills. Adapt the marketing-oriented design reference
  into a compact, evidence-first application console.
- Use semantic controls, visible focus, keyboard-accessible drawers/dialogs,
  status text in addition to color, and `prefers-reduced-motion`.
- Provide loading, empty, running, completed, cancelled, unauthorized,
  infrastructure-failure, and recoverable-error states defined by the UX spec.
- On narrow screens, convert the capability matrix to cards rather than forcing
  an unreadable table.
- Browser tests must use durable API state and stable accessible selectors, not
  arbitrary time sleeps or styling classes.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
