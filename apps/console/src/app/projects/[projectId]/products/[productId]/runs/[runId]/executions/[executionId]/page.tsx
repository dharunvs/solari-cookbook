import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";

export const dynamic = "force-dynamic";

function value(value: string | number | null | undefined) {
  return value === null || value === undefined || value === "" ? "—" : value;
}

export default async function ExecutionPage({
  params,
}: {
  params: Promise<{
    projectId: string;
    productId: string;
    runId: string;
    executionId: string;
  }>;
}) {
  const identity = await getApiIdentity();
  if (!identity) redirect("/sign-in");
  const { projectId, productId, runId, executionId } = await params;
  const api = apiFor(identity);
  const { data: execution, response } = await api.GET(
    "/v1/executions/{execution_id}",
    { params: { path: { execution_id: executionId } } },
  );
  if (response.status === 404) notFound();
  if (!execution || execution.run_id !== runId) notFound();
  const { data: run } = await api.GET("/v1/runs/{run_id}", {
    params: { path: { run_id: runId } },
  });
  if (!run || run.product_id !== productId) notFound();

  const outcome =
    execution.infrastructure_state === "FAIL"
      ? "UNVERIFIED"
      : execution.subject_state === "FAIL"
        ? "REPRODUCED"
        : execution.phase === "FIX_VERIFY"
          ? "FIX VERIFIED"
          : "PASS";
  const outcomeTone =
    outcome === "PASS" || outcome === "FIX VERIFIED"
      ? "bg-success-soft text-success-deep"
      : outcome === "REPRODUCED"
        ? "bg-error-soft text-error-deep"
        : "bg-warning-soft text-warning-deep";
  const backHref = `/projects/${projectId}/products/${productId}/runs/${runId}`;
  const findingHref = execution.finding_id
    ? `${backHref}/findings/${execution.finding_id}`
    : null;
  const languageLabel =
    execution.source_surface === "docs_python"
      ? "Python documentation"
      : execution.language === "typescript"
        ? "TypeScript"
        : execution.language === "go"
          ? "Go"
          : "Python";

  return (
    <main className="min-h-screen bg-canvas-soft text-ink" id="main-content">
      <header className="border-b border-hairline bg-canvas">
        <div className="mx-auto flex min-h-16 max-w-5xl items-center px-4 py-3 sm:px-6">
          <Link className="text-sm font-medium" href={backHref}>
            ← Back to run
          </Link>
        </div>
      </header>
      <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-12">
        <article className="rounded-lg border border-hairline bg-canvas p-5 shadow-card sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-mono text-xs text-body">
                {languageLabel.toUpperCase()}{" "}
                {execution.phase.replace("_", " ")} / {execution.id.slice(0, 8)}
              </p>
              <h1 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-balance">
                Runtime evidence
              </h1>
            </div>
            <span
              className={`rounded-full px-2.5 py-1 text-xs font-semibold ${outcomeTone}`}
            >
              {outcome}
            </span>
          </div>

          {execution.backend === "REPLAY" ? (
            <div className="mt-6 rounded-md border border-warning-deep/30 bg-warning-soft p-4 text-sm text-warning-deep">
              Controlled replay evidence for deterministic local and CI runs. It
              is bound to this exact package and source hash, but is not a live
              Solari execution.
            </div>
          ) : (
            <div className="mt-6 rounded-md border border-hairline bg-canvas-soft p-4 text-sm text-body">
              Live execution in a fresh Solari Sandbox. Cleanup is reported as
              an independent result below.
            </div>
          )}

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <section className="rounded-md border border-hairline p-4">
              <p className="text-xs text-body">Infrastructure</p>
              <p className="mt-1 text-lg font-semibold">
                {execution.infrastructure_state}
              </p>
              <p className="mt-1 text-sm text-body">
                Last stage: {execution.infrastructure_step}
              </p>
            </section>
            <section className="rounded-md border border-hairline p-4">
              <p className="text-xs text-body">Subject</p>
              <p className="mt-1 text-lg font-semibold">
                {execution.subject_state}
              </p>
              <p className="mt-1 text-sm text-body">
                Exit code: {value(execution.exit_code)}
              </p>
            </section>
          </div>

          <dl className="mt-6 grid gap-x-8 gap-y-4 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-body">Backend / sandbox</dt>
              <dd className="mt-1 break-all font-mono text-xs">
                {execution.backend} · {value(execution.sandbox_id)}
              </dd>
            </div>
            <div>
              <dt className="text-body">Package</dt>
              <dd className="mt-1 font-mono text-xs">
                {execution.package_name}
                {execution.language === "go"
                  ? "@"
                  : execution.language === "typescript"
                    ? "@"
                    : "=="}
                {execution.package_version}
              </dd>
            </div>
            <div>
              <dt className="text-body">Source</dt>
              <dd className="mt-1 break-all font-mono text-xs">
                {execution.source_path} · {execution.source_sha256}
              </dd>
            </div>
            <div>
              <dt className="text-body">Duration / cleanup</dt>
              <dd className="mt-1 font-mono text-xs">
                {execution.duration_ms} ms · {execution.cleanup_state}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-body">Command plan SHA-256</dt>
              <dd className="mt-1 break-all font-mono text-xs">
                {execution.command_sha256}
              </dd>
            </div>
          </dl>

          <section className="mt-7" aria-labelledby="stdout-heading">
            <h2 className="text-sm font-medium" id="stdout-heading">
              stdout {execution.output_truncated ? "· truncated" : ""}
            </h2>
            <pre className="mt-2 min-h-14 overflow-x-auto whitespace-pre-wrap rounded-md bg-ink p-4 font-mono text-xs text-white">
              {execution.stdout || "(empty)"}
            </pre>
          </section>
          <section className="mt-5" aria-labelledby="stderr-heading">
            <h2 className="text-sm font-medium" id="stderr-heading">
              stderr {execution.output_truncated ? "· truncated" : ""}
            </h2>
            <pre className="mt-2 min-h-14 overflow-x-auto whitespace-pre-wrap rounded-md bg-ink p-4 font-mono text-xs text-white">
              {execution.stderr || "(empty)"}
            </pre>
          </section>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-hairline pt-5">
            <p className="break-all font-mono text-xs text-body">
              Evidence SHA-256 {execution.evidence.sha256}
            </p>
            {findingHref ? (
              <Link
                className="rounded-md border border-hairline px-4 py-2.5 text-sm font-medium"
                href={findingHref}
              >
                Review finding →
              </Link>
            ) : (
              <span className="text-xs text-body">
                No finding: this aligned subject passed.
              </span>
            )}
          </div>
        </article>
      </section>
    </main>
  );
}
