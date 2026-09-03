"use client";

import type { components } from "@noxyn/generated-client";
import Link from "next/link";
import { useEffect, useState } from "react";

import { CapabilityMatrix } from "@/components/capability-matrix";
import { RunStatus, terminalStates, type Run } from "@/components/run-status";

type Matrix = components["schemas"]["MatrixView"];
type Finding = components["schemas"]["FindingView"];
type MatrixCell = components["schemas"]["MatrixCellView"];
type Execution = components["schemas"]["ExecutionView"];
type Proposal = components["schemas"]["ProposalView"];
type Analysis = {
  matrix: Matrix;
  findings: Finding[];
  executions: Execution[];
  proposals: Proposal[];
};

function date(value: string | null | undefined) {
  return value
    ? new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(value))
    : "—";
}

export function RunDetail({
  initialRun,
  initialAnalysis,
  projectId,
  productId,
}: {
  initialRun: Run;
  initialAnalysis: Analysis | null;
  projectId: string;
  productId: string;
}) {
  const [run, setRun] = useState(initialRun);
  const [analysis, setAnalysis] = useState(initialAnalysis);
  const [selected, setSelected] = useState<MatrixCell | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    if (terminalStates.has(run.state)) return;
    const controller = new AbortController();
    const timer = window.setInterval(async () => {
      try {
        const response = await fetch(`/api/runs/${run.id}`, {
          signal: controller.signal,
        });
        const data = (await response.json()) as Run & { error?: string };
        if (!response.ok)
          throw new Error(data.error ?? "Could not refresh the run.");
        setRun(data);
        setError(null);
      } catch (reason) {
        if (!controller.signal.aborted)
          setError(
            reason instanceof Error
              ? reason.message
              : "Could not refresh the run.",
          );
      }
    }, 1500);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [run.id, run.state]);

  useEffect(() => {
    if (run.state !== "COMPLETED" || analysis) return;
    const controller = new AbortController();
    async function loadAnalysis() {
      try {
        const response = await fetch(`/api/runs/${run.id}/analysis`, {
          signal: controller.signal,
        });
        const result = (await response.json()) as Analysis & { error?: string };
        if (!response.ok)
          throw new Error(result.error ?? "Could not load static analysis.");
        setAnalysis(result);
        setError(null);
      } catch (reason) {
        if (!controller.signal.aborted)
          setError(
            reason instanceof Error
              ? reason.message
              : "Could not load static analysis.",
          );
      }
    }
    void loadAnalysis();
    return () => controller.abort();
  }, [analysis, run.id, run.state]);

  async function cancel() {
    if (
      !window.confirm(
        "Cancel this run? Any evidence already captured will be preserved.",
      )
    )
      return;
    setCancelling(true);
    const response = await fetch(`/api/runs/${run.id}/cancel`, {
      method: "POST",
    });
    const data = (await response.json()) as Run & { error?: string };
    if (response.ok) {
      setRun(data);
      setError(null);
    } else {
      setError(data.error ?? "Could not cancel the run.");
    }
    setCancelling(false);
  }

  const snapshotComplete = !["QUEUED", "SNAPSHOTTING"].includes(run.state);
  const analysisComplete = !["QUEUED", "SNAPSHOTTING", "ANALYZING"].includes(
    run.state,
  );
  const verificationComplete = terminalStates.has(run.state);
  const verifiedProposals = analysis?.proposals.filter(
    (proposal) => proposal.state === "FIX_VERIFIED",
  ).length;

  return (
    <div className="mt-8">
      <div className="grid gap-4 lg:grid-cols-[1.4fr_0.6fr]">
        <section
          className="rounded-lg border border-hairline bg-canvas p-5 shadow-card sm:p-6"
          aria-live="polite"
        >
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-mono text-xs text-body">
                RUN / {run.id.slice(0, 8)} · CONTROLLED FIXTURE
              </p>
              <h1 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-balance">
                Controlled API evolution
              </h1>
            </div>
            <RunStatus state={run.state} />
          </div>
          <ol className="mt-8 grid gap-3" aria-label="Run progress">
            {[
              ["Queued", true],
              ["Snapshot and hash sources", snapshotComplete],
              ["Extract and normalize capabilities", analysisComplete],
              ["Run independent Python verification", verificationComplete],
              [
                "Execute the exact Python documentation block",
                verificationComplete,
              ],
              ["Run independent TypeScript verification", verificationComplete],
              ["Persist immutable execution evidence", verificationComplete],
            ].map(([label, complete]) => (
              <li
                className="flex items-center gap-3 text-sm"
                key={String(label)}
              >
                <span
                  className={`grid size-6 place-items-center rounded-full border ${complete ? "border-ink bg-ink text-white" : "border-hairline text-body"}`}
                  aria-hidden="true"
                >
                  {complete ? "✓" : "·"}
                </span>
                {label}
              </li>
            ))}
          </ol>
          <div className="mt-8 rounded-md border border-hairline bg-canvas-soft p-4 text-sm text-body">
            This controlled API-evolution fixture verifies the Python example,
            exact Python documentation block, and TypeScript example against
            pinned packages. Replay mode is deterministic CI evidence; live mode
            creates a fresh Solari Sandbox for every subject.
          </div>
          {!terminalStates.has(run.state) ? (
            <button
              className="mt-6 rounded-md border border-hairline bg-canvas px-4 py-2.5 text-sm font-medium disabled:cursor-wait disabled:opacity-60"
              disabled={cancelling}
              onClick={cancel}
              type="button"
            >
              {cancelling ? "Cancelling…" : "Cancel run"}
            </button>
          ) : null}
          {error ? (
            <p className="mt-4 text-sm text-error-deep" role="alert">
              {error}
            </p>
          ) : null}
        </section>
        <aside className="rounded-lg border border-hairline bg-canvas p-5 shadow-card">
          <p className="font-mono text-xs text-body">IMMUTABLE RECORD</p>
          <dl className="mt-4 grid gap-4 text-sm">
            <div>
              <dt className="text-body">Configuration</dt>
              <dd className="mt-1 font-medium">v{run.configuration_version}</dd>
            </div>
            <div>
              <dt className="text-body">Attempts</dt>
              <dd className="mt-1 font-medium">
                {run.attempt} / {run.max_attempts}
              </dd>
            </div>
            <div>
              <dt className="text-body">Created</dt>
              <dd className="mt-1 font-medium">{date(run.created_at)}</dd>
            </div>
            <div>
              <dt className="text-body">Completed</dt>
              <dd className="mt-1 font-medium">{date(run.completed_at)}</dd>
            </div>
            <div>
              <dt className="text-body">Final evidence</dt>
              <dd className="mt-1 break-all font-mono text-xs">
                {run.artifact
                  ? `${run.artifact.sha256.slice(0, 16)}… · ${run.artifact.byte_length} bytes`
                  : "Pending"}
              </dd>
            </div>
          </dl>
        </aside>
      </div>

      {analysis ? (
        <>
          <section className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              ["Capabilities", analysis.matrix.summary.capabilities],
              ["Aligned cells", analysis.matrix.summary.aligned],
              ["Suspected", analysis.matrix.summary.suspected],
              ["Fixes verified", `${verifiedProposals} / 2`],
            ].map(([label, value]) => (
              <div
                className="rounded-lg border border-hairline bg-canvas p-4 shadow-card"
                key={label}
              >
                <p className="text-xs text-body">{label}</p>
                <p className="mt-2 text-2xl font-semibold tabular-nums">
                  {value}
                </p>
              </div>
            ))}
          </section>
          <CapabilityMatrix
            matrix={analysis.matrix}
            onSelect={setSelected}
            productId={productId}
            projectId={projectId}
            runId={run.id}
            selected={selected}
          />
          {analysis.matrix.parity ? (
            <section
              aria-labelledby="parity-heading"
              className="mt-6 rounded-lg border border-hairline bg-canvas p-5 shadow-card sm:p-6"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-mono text-xs text-body">RUNTIME PARITY</p>
                  <h2 className="mt-2 font-medium" id="parity-heading">
                    Python and TypeScript
                  </h2>
                </div>
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-semibold ${analysis.matrix.parity.state === "MATCH" ? "bg-success-soft text-success-deep" : analysis.matrix.parity.state === "DIFFERENT" ? "bg-warning-soft text-warning-deep" : "bg-canvas-soft text-body"}`}
                >
                  {analysis.matrix.parity.state}
                </span>
              </div>
              <p className="mt-3 text-sm text-body">
                {analysis.matrix.parity.summary}
              </p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {analysis.executions
                  .filter(
                    (execution) =>
                      execution.phase === "VERIFY" &&
                      execution.source_surface !== "docs_python",
                  )
                  .map((execution) => (
                    <article
                      className="rounded-md border border-hairline bg-canvas-soft p-4"
                      key={execution.id}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <h3 className="text-sm font-medium">
                          {execution.language === "typescript"
                            ? "TypeScript"
                            : "Python"}
                        </h3>
                        <span
                          className={`rounded-full px-2 py-1 text-[0.6875rem] font-semibold ${execution.infrastructure_state === "FAIL" ? "bg-warning-soft text-warning-deep" : execution.subject_state === "PASS" ? "bg-success-soft text-success-deep" : "bg-error-soft text-error-deep"}`}
                        >
                          {execution.infrastructure_state === "FAIL"
                            ? "UNVERIFIED"
                            : execution.subject_state}
                        </span>
                      </div>
                      <p className="mt-2 text-xs text-body">
                        Infrastructure {execution.infrastructure_state} ·{" "}
                        {execution.backend}
                      </p>
                      <Link
                        className="mt-4 inline-flex text-sm font-medium underline underline-offset-4"
                        href={`/projects/${projectId}/products/${productId}/runs/${run.id}/executions/${execution.id}`}
                      >
                        View{" "}
                        {execution.language === "typescript"
                          ? "TypeScript"
                          : "Python"}{" "}
                        execution evidence
                      </Link>
                    </article>
                  ))}
              </div>
            </section>
          ) : null}
          <section
            className="mt-6 rounded-lg border border-hairline bg-canvas p-5 shadow-card sm:p-6"
            aria-labelledby="fixes-heading"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-mono text-xs text-body">
                  PROPOSAL LIFECYCLE
                </p>
                <h2 className="mt-2 font-medium" id="fixes-heading">
                  Reproduced fixture drift
                </h2>
              </div>
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-semibold ${verifiedProposals === 2 ? "bg-success-soft text-success-deep" : "bg-warning-soft text-warning-deep"}`}
              >
                {verifiedProposals === 2
                  ? "FIXES VERIFIED"
                  : `${verifiedProposals} / 2 VERIFIED`}
              </span>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {analysis.findings.map((finding) => {
                const proposal = analysis.proposals.find(
                  (item) => item.finding_id === finding.id,
                );
                return (
                  <Link
                    className="rounded-md border border-hairline bg-canvas-soft p-4"
                    href={`/projects/${projectId}/products/${productId}/runs/${run.id}/findings/${finding.id}`}
                    key={finding.id}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium">
                        {finding.source_surface === "docs_python"
                          ? "Python documentation"
                          : "Python example"}
                      </span>
                      <span className="text-xs font-semibold">
                        {proposal?.state.replace("_", " ") ??
                          finding.lifecycle_state.replace("_", " ")}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-body">
                      Review source evidence, exact patch, and fresh
                      verification.
                    </p>
                  </Link>
                );
              })}
            </div>
            <p className="mt-4 text-xs text-body">
              Verified means the proposed bytes passed in a fresh sandbox. Noxyn
              did not merge, publish, or deploy them.
            </p>
          </section>
        </>
      ) : run.state === "COMPLETED" ? (
        <section className="mt-6 rounded-lg border border-hairline bg-canvas p-5 text-sm text-error-deep shadow-card">
          Verification completed, but its evidence is temporarily unavailable.
          Refresh to retry the authorized artifact read.
        </section>
      ) : null}
    </div>
  );
}
