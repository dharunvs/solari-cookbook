import type { components } from "@noxyn/generated-client";
import Link from "next/link";

type Matrix = components["schemas"]["MatrixView"];
type Cell = components["schemas"]["MatrixCellView"];
type Runtime = components["schemas"]["RuntimeCellView"];

const surfaceLabels: Record<string, string> = {
  contract: "Contract",
  python: "Python",
  typescript: "TypeScript",
  go: "Go",
  docs_python: "Python docs",
  docs_typescript: "TS docs",
};

const stateTone: Record<Cell["state"], string> = {
  ALIGNED: "bg-success-soft text-success-deep",
  SUSPECTED: "bg-warning-soft text-warning-deep",
  NOT_EXPECTED: "bg-canvas-soft text-body",
  UNVERIFIED: "bg-error-soft text-error-deep",
};

function State({ state }: { state: Cell["state"] }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-1 text-[0.6875rem] font-semibold tracking-wide ${stateTone[state]}`}
    >
      {state.replace("_", " ")}
    </span>
  );
}

const runtimeTone: Record<Runtime["state"], string> = {
  NOT_RUN: "bg-canvas-soft text-body",
  PASS: "bg-success-soft text-success-deep",
  FAIL: "bg-error-soft text-error-deep",
  UNVERIFIED: "bg-warning-soft text-warning-deep",
};

function runtimeLabel(runtime: Runtime) {
  if (runtime.sourceSurface === "docs_python") return "Python docs runtime";
  return runtime.language === "typescript"
    ? "TypeScript runtime"
    : runtime.language === "go"
      ? "Go runtime"
      : "Python runtime";
}

function runtimeEvidenceLabel(runtime: Runtime) {
  if (!runtime.executionId) return null;
  return `Infrastructure ${runtime.infrastructureState} · Subject ${runtime.subjectState} · ${runtime.backend} · FIXTURE`;
}

export function CapabilityMatrix({
  matrix,
  projectId,
  productId,
  runId,
  selected,
  onSelect,
}: {
  matrix: Matrix;
  projectId: string;
  productId: string;
  runId: string;
  selected: Cell | null;
  onSelect: (cell: Cell | null) => void;
}) {
  const cells = matrix.rows[0]?.cells ?? [];
  const runtimes = matrix.rows[0]?.runtimeCells ?? [];
  const findingHref = selected?.findingId
    ? `/projects/${projectId}/products/${productId}/runs/${runId}/findings/${selected.findingId}`
    : null;
  return (
    <section className="mt-6" aria-labelledby="matrix-heading">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-medium" id="matrix-heading">
            Capability matrix
          </h2>
          <p className="mt-1 text-sm text-body">
            Static comparison and separately classified runtime evidence.
          </p>
        </div>
        <span className="rounded-full border border-hairline bg-canvas px-2.5 py-1 font-mono text-xs text-body">
          FIXTURE
        </span>
      </div>

      <div className="mt-4 grid gap-3 md:hidden">
        {cells.map((cell) => (
          <button
            aria-pressed={selected?.surface === cell.surface}
            className="rounded-lg border border-hairline bg-canvas p-4 text-left shadow-card"
            key={cell.surface}
            onClick={() => onSelect(cell)}
            type="button"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-medium">
                {surfaceLabels[cell.surface] ?? cell.surface}
              </span>
              <State state={cell.state} />
            </div>
            <p className="mt-3 text-sm text-body">{cell.summary}</p>
          </button>
        ))}
        {runtimes.map((runtime) =>
          runtime.executionId ? (
            <Link
              className="rounded-lg border border-hairline bg-canvas p-4 shadow-card"
              href={`/projects/${projectId}/products/${productId}/runs/${runId}/executions/${runtime.executionId}`}
              key={runtime.sourceSurface}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium">
                  {runtimeLabel(runtime)}
                </span>
                <span
                  className={`rounded-full px-2 py-1 text-[0.6875rem] font-semibold ${runtimeTone[runtime.state]}`}
                >
                  {runtime.state.replace("_", " ")}
                </span>
              </div>
              <p className="mt-3 text-sm text-body">{runtime.summary}</p>
              <p className="mt-3 text-xs text-body">
                {runtimeEvidenceLabel(runtime)}
              </p>
            </Link>
          ) : (
            <article
              className="rounded-lg border border-hairline bg-canvas p-4 shadow-card"
              key={runtime.sourceSurface}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium">
                  {runtimeLabel(runtime)}
                </span>
                <span className="rounded-full bg-canvas-soft px-2 py-1 text-[0.6875rem] font-semibold text-body">
                  NOT RUN
                </span>
              </div>
              <p className="mt-3 text-sm text-body">{runtime.summary}</p>
            </article>
          ),
        )}
      </div>

      <div className="mt-4 hidden overflow-x-auto rounded-lg border border-hairline bg-canvas md:block">
        <table className="min-w-[64rem] border-collapse text-left text-sm">
          <caption className="sr-only">
            Static state for sandbox.create memory limit across configured
            surfaces
          </caption>
          <thead className="bg-canvas-soft text-xs text-body">
            <tr>
              <th className="px-4 py-3 font-medium" scope="col">
                Capability
              </th>
              {cells.map((cell) => (
                <th
                  className="px-3 py-3 font-medium"
                  key={cell.surface}
                  scope="col"
                >
                  {surfaceLabels[cell.surface] ?? cell.surface}
                </th>
              ))}
              {runtimes.map((runtime) => (
                <th
                  className="px-3 py-3 font-medium"
                  key={runtime.sourceSurface}
                  scope="col"
                >
                  {runtimeLabel(runtime)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr className="border-t border-hairline">
              <th className="px-4 py-4 align-top font-medium" scope="row">
                {matrix.rows[0]?.capabilityId}
              </th>
              {cells.map((cell) => (
                <td className="px-3 py-3 align-top" key={cell.surface}>
                  <button
                    aria-label={`${surfaceLabels[cell.surface] ?? cell.surface}: ${cell.state}. Open evidence`}
                    aria-pressed={selected?.surface === cell.surface}
                    className="rounded-md focus-visible:outline-2"
                    onClick={() => onSelect(cell)}
                    type="button"
                  >
                    <State state={cell.state} />
                  </button>
                </td>
              ))}
              {runtimes.map((runtime) => (
                <td className="px-3 py-3 align-top" key={runtime.sourceSurface}>
                  {runtime.executionId ? (
                    <Link
                      aria-label={`${runtimeLabel(runtime)} ${runtime.state}. Open execution evidence`}
                      className={`inline-flex rounded-full px-2 py-1 text-[0.6875rem] font-semibold ${runtimeTone[runtime.state]}`}
                      href={`/projects/${projectId}/products/${productId}/runs/${runId}/executions/${runtime.executionId}`}
                    >
                      {runtime.state.replace("_", " ")}
                    </Link>
                  ) : (
                    <span className="inline-flex rounded-full bg-canvas-soft px-2 py-1 text-[0.6875rem] font-semibold text-body">
                      NOT RUN
                    </span>
                  )}
                  {runtimeEvidenceLabel(runtime) ? (
                    <p className="mt-2 text-xs text-body">
                      {runtimeEvidenceLabel(runtime)}
                    </p>
                  ) : null}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {selected ? (
        <aside
          aria-labelledby="evidence-heading"
          className="mt-4 rounded-lg border border-hairline bg-canvas p-5 shadow-card"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="font-mono text-xs text-body">CAPABILITY EVIDENCE</p>
              <h3 className="mt-2 font-medium" id="evidence-heading">
                sandbox.create.memory_mb / {surfaceLabels[selected.surface]}
              </h3>
            </div>
            <button
              className="rounded-md border border-hairline px-3 py-1.5 text-sm"
              onClick={() => onSelect(null)}
              type="button"
            >
              Close
            </button>
          </div>
          <div className="mt-5 grid gap-4 text-sm sm:grid-cols-2">
            <div>
              <p className="text-body">Comparison</p>
              <p className="mt-1">
                Observed <code>{selected.observed ?? "—"}</code>; expected{" "}
                <code>{selected.expected}</code>.
              </p>
            </div>
            <div>
              <p className="text-body">Source</p>
              <p className="mt-1 break-all font-mono text-xs">
                {selected.evidence?.path ?? "No source evidence"}
                {selected.evidence ? ` · ${selected.evidence.locator}` : ""}
              </p>
            </div>
          </div>
          {selected.evidence ? (
            <pre className="mt-4 overflow-x-auto rounded-md bg-ink p-4 text-xs text-white">
              <code>{selected.evidence.excerpt}</code>
            </pre>
          ) : null}
          <p className="mt-4 break-all font-mono text-xs text-body">
            SHA-256 {selected.evidence?.sha256 ?? "unavailable"}
          </p>
          {findingHref ? (
            <Link
              className="mt-5 inline-flex rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white"
              href={findingHref}
            >
              Review finding →
            </Link>
          ) : null}
        </aside>
      ) : null}
    </section>
  );
}
