import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";
import { ProposalPanel } from "@/components/proposal-panel";

export const dynamic = "force-dynamic";

const surfaceLabels: Record<string, string> = {
  python: "Python example",
  docs_python: "Python documentation",
};

export default async function FindingPage({
  params,
}: {
  params: Promise<{
    projectId: string;
    productId: string;
    runId: string;
    findingId: string;
  }>;
}) {
  const identity = await getApiIdentity();
  if (!identity) redirect("/sign-in");
  const { projectId, productId, runId, findingId } = await params;
  const api = apiFor(identity);
  const [findingResult, runResult, executionsResult, proposalsResult] =
    await Promise.all([
      api.GET("/v1/findings/{finding_id}", {
        params: { path: { finding_id: findingId } },
      }),
      api.GET("/v1/runs/{run_id}", {
        params: { path: { run_id: runId } },
      }),
      api.GET("/v1/runs/{run_id}/executions", {
        params: { path: { run_id: runId } },
      }),
      api.GET("/v1/runs/{run_id}/proposals", {
        params: { path: { run_id: runId } },
      }),
    ]);
  if (
    findingResult.response.status === 404 ||
    runResult.response.status === 404
  )
    notFound();
  const finding = findingResult.data;
  const run = runResult.data;
  const execution = executionsResult.data?.items.find(
    (item) => item.finding_id === findingId && item.phase === "VERIFY",
  );
  const proposal = proposalsResult.data?.items.find(
    (item) => item.finding_id === findingId,
  );
  if (
    !finding ||
    !run ||
    finding.run_id !== runId ||
    run.product_id !== productId
  )
    notFound();
  const runPath = `/projects/${projectId}/products/${productId}/runs/${runId}`;

  return (
    <main className="min-h-screen bg-canvas-soft text-ink" id="main-content">
      <header className="border-b border-hairline bg-canvas">
        <div className="mx-auto flex min-h-16 max-w-5xl items-center px-4 py-3 sm:px-6">
          <Link className="text-sm font-medium" href={runPath}>
            ← Capability matrix
          </Link>
        </div>
      </header>
      <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-12">
        <div className="rounded-lg border border-hairline bg-canvas p-5 shadow-card sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-mono text-xs text-body">
                CONTROLLED FIXTURE / STATIC FINDING
              </p>
              <h1 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-balance">
                {finding.capability_id} /{" "}
                {surfaceLabels[finding.source_surface] ??
                  finding.source_surface}
              </h1>
            </div>
            <span className="rounded-full bg-warning-soft px-2.5 py-1 text-xs font-semibold text-warning-deep">
              {finding.lifecycle_state}
            </span>
          </div>

          <div className="mt-8 overflow-x-auto" aria-label="Finding lifecycle">
            <ol className="flex min-w-max items-center gap-2 text-xs font-medium">
              <li className="rounded-full bg-warning-soft px-3 py-1.5 text-warning-deep">
                SUSPECTED
              </li>
              <li aria-hidden="true" className="text-body">
                →
              </li>
              <li
                className={`rounded-full px-3 py-1.5 ${["REPRODUCED", "FIX_PROPOSED", "FIX_VERIFIED"].includes(finding.lifecycle_state) ? "bg-error-soft text-error-deep" : "border border-hairline text-body"}`}
              >
                REPRODUCED
              </li>
              <li aria-hidden="true" className="text-body">
                →
              </li>
              <li
                className={`rounded-full px-3 py-1.5 ${["FIX_PROPOSED", "FIX_VERIFIED"].includes(finding.lifecycle_state) ? "bg-warning-soft text-warning-deep" : "border border-hairline text-body"}`}
              >
                FIX PROPOSED
              </li>
              <li aria-hidden="true" className="text-body">
                →
              </li>
              <li
                className={`rounded-full px-3 py-1.5 ${finding.lifecycle_state === "FIX_VERIFIED" ? "bg-success-soft text-success-deep" : "border border-hairline text-body"}`}
              >
                FIX VERIFIED
              </li>
            </ol>
          </div>

          <section
            className="mt-8 grid gap-6 sm:grid-cols-2"
            aria-label="Static comparison"
          >
            <div>
              <h2 className="text-sm font-medium">Why suspected</h2>
              <p className="mt-2 text-sm leading-6 text-body">
                {finding.summary}
              </p>
            </div>
            <dl className="grid gap-3 text-sm">
              <div>
                <dt className="text-body">Observed</dt>
                <dd className="mt-1 font-mono">
                  {finding.observed_value ?? "—"}
                </dd>
              </div>
              <div>
                <dt className="text-body">Expected</dt>
                <dd className="mt-1 font-mono">{finding.expected_value}</dd>
              </div>
              <div>
                <dt className="text-body">Runtime status</dt>
                <dd className="mt-1 font-medium">
                  {execution
                    ? `Infrastructure ${execution.infrastructure_state} · Subject ${execution.subject_state}`
                    : "NOT RUN"}
                </dd>
              </div>
            </dl>
          </section>

          <section
            className="mt-8 border-t border-hairline pt-6"
            aria-labelledby="source-evidence"
          >
            <h2 className="text-sm font-medium" id="source-evidence">
              Immutable source evidence
            </h2>
            <p className="mt-2 break-all font-mono text-xs text-body">
              {finding.evidence.path} · {finding.evidence.locator}
            </p>
            <pre className="mt-4 overflow-x-auto rounded-md bg-ink p-4 text-xs text-white">
              <code>{finding.evidence.excerpt}</code>
            </pre>
            <p className="mt-4 break-all font-mono text-xs text-body">
              SHA-256 {finding.evidence.sha256}
            </p>
          </section>

          {execution ? (
            <div className="mt-8 rounded-md border border-hairline bg-canvas-soft p-4 text-sm text-body">
              The Python failure was reproduced against {execution.package_name}
              =={execution.package_version} with exit code {execution.exit_code}
              .{" "}
              <Link
                className="font-medium text-ink underline underline-offset-4"
                href={`${runPath}/executions/${execution.id}`}
              >
                View execution evidence
              </Link>
              .
            </div>
          ) : (
            <div className="mt-8 rounded-md border border-hairline bg-canvas-soft p-4 text-sm text-body">
              This surface remains a static suspicion because no execution is
              bound to it.
            </div>
          )}
          <ProposalPanel
            canGenerate={finding.lifecycle_state === "REPRODUCED"}
            findingId={findingId}
            initialProposal={proposal ?? null}
            runPath={runPath}
          />
        </div>
      </section>
    </main>
  );
}
