"use client";

import type { components } from "@noxyn/generated-client";
import Link from "next/link";
import { useEffect, useState } from "react";

type Proposal = components["schemas"]["ProposalView"];

export function ProposalPanel({
  findingId,
  initialProposal,
  runPath,
  canGenerate,
}: {
  findingId: string;
  initialProposal: Proposal | null;
  runPath: string;
  canGenerate: boolean;
}) {
  const [proposal, setProposal] = useState(initialProposal);
  const [busy, setBusy] = useState<"generate" | "verify" | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (
      !proposal ||
      !["QUEUED", "LEASED"].includes(proposal.verification_job_state ?? "")
    )
      return;
    const controller = new AbortController();
    const timer = window.setInterval(async () => {
      const response = await fetch(`/api/proposals/${proposal.id}`, {
        signal: controller.signal,
      });
      const body = (await response.json()) as Proposal & { error?: string };
      if (response.ok) {
        setProposal(body);
        setError(null);
      } else if (!controller.signal.aborted) {
        setError(body.error ?? "Could not refresh proposal verification.");
      }
    }, 1500);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [proposal]);

  async function mutate(action: "generate" | "verify") {
    setBusy(action);
    setError(null);
    const target =
      action === "generate"
        ? `/api/findings/${findingId}/proposals`
        : `/api/proposals/${proposal?.id}/verify`;
    const response = await fetch(target, { method: "POST" });
    const body = (await response.json()) as Proposal & { error?: string };
    if (response.ok) setProposal(body);
    else setError(body.error ?? "The proposal request failed safely.");
    setBusy(null);
  }

  if (!proposal)
    return (
      <section
        className="mt-8 rounded-md border border-hairline bg-canvas-soft p-5"
        aria-labelledby="proposal-heading"
      >
        <h2 className="text-sm font-medium" id="proposal-heading">
          Focused proposal
        </h2>
        <p className="mt-2 text-sm leading-6 text-body">
          Noxyn can create a minimal source-bound patch for this controlled
          fixture. It will not edit the checkout, open a PR, merge, publish, or
          deploy anything.
        </p>
        <button
          className="mt-5 rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
          disabled={!canGenerate || busy !== null}
          onClick={() => void mutate("generate")}
          type="button"
        >
          {busy === "generate" ? "Generating proposal…" : "Generate proposal"}
        </button>
        {!canGenerate ? (
          <p className="mt-3 text-xs text-body">
            Runtime reproduction is required first.
          </p>
        ) : null}
        {error ? (
          <p className="mt-3 text-sm text-error-deep" role="alert">
            {error}
          </p>
        ) : null}
      </section>
    );

  const verifying = ["QUEUED", "LEASED"].includes(
    proposal.verification_job_state ?? "",
  );
  const verified = proposal.state === "FIX_VERIFIED";
  return (
    <section
      className="mt-8 border-t border-hairline pt-7"
      aria-labelledby="proposal-heading"
      aria-live="polite"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-xs text-body">SOURCE-BOUND PROPOSAL</p>
          <h2 className="mt-2 font-medium" id="proposal-heading">
            One reviewed parameter rename
          </h2>
        </div>
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${verified ? "bg-success-soft text-success-deep" : "bg-warning-soft text-warning-deep"}`}
        >
          {proposal.state.replace("_", " ")}
        </span>
      </div>
      <pre
        className="mt-5 overflow-x-auto rounded-md bg-ink p-4 text-xs leading-6 text-white"
        aria-label="Unified proposal diff"
      >
        <code>{proposal.patch}</code>
      </pre>
      <dl className="mt-5 grid gap-4 text-xs sm:grid-cols-2">
        <div>
          <dt className="text-body">Original SHA-256</dt>
          <dd className="mt-1 break-all font-mono">{proposal.source_sha256}</dd>
        </div>
        <div>
          <dt className="text-body">Proposed SHA-256</dt>
          <dd className="mt-1 break-all font-mono">
            {proposal.proposed_sha256}
          </dd>
        </div>
      </dl>
      {verified && proposal.verification ? (
        <div className="mt-6 rounded-md border border-success-deep/20 bg-success-soft p-4 text-sm">
          <p className="font-medium text-success-deep">
            Fresh verification passed
          </p>
          <p className="mt-2 text-body">
            Infrastructure PASS · Subject PASS · Cleanup{" "}
            {proposal.verification.cleanup_state} · exit{" "}
            {proposal.verification.exit_code}
          </p>
          <Link
            className="mt-3 inline-flex font-medium underline underline-offset-4"
            href={`${runPath}/executions/${proposal.verification.id}`}
          >
            View verification evidence
          </Link>
        </div>
      ) : (
        <button
          className="mt-6 rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white disabled:cursor-wait disabled:opacity-60"
          disabled={busy !== null || verifying}
          onClick={() => void mutate("verify")}
          type="button"
        >
          {verifying || busy === "verify"
            ? "Verifying in a fresh sandbox…"
            : "Verify proposed fix"}
        </button>
      )}
      <p className="mt-4 text-xs text-body">
        Noxyn preserves this as evidence only. The repository was not changed.
      </p>
      {error ? (
        <p className="mt-3 text-sm text-error-deep" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
