"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import type { Run } from "@/components/run-status";
import { browserApi } from "@/lib/browser-api";

type Scenario = "controlled_api_evolution" | "current_configured_solari";

export function StartRunButton({
  productId,
  runPath,
}: {
  productId: string;
  runPath: string;
}) {
  const router = useRouter();
  const key = useRef(crypto.randomUUID());
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scenario, setScenario] = useState<Scenario>(
    "controlled_api_evolution",
  );

  async function start() {
    setPending(true);
    setError(null);
    try {
      const response = await browserApi("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          productId,
          idempotencyKey: key.current,
          scenario,
        }),
      });
      const data = (await response.json()) as Run & { error?: string };
      if (!response.ok || !data.id)
        throw new Error(data.error ?? "Could not start the run.");
      router.push(`${runPath}/${data.id}`);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Could not start the run.",
      );
      setPending(false);
    }
  }

  return (
    <div>
      <fieldset className="mb-4 space-y-2" disabled={pending}>
        <legend className="text-sm font-medium">Run mode</legend>
        <label className="flex cursor-pointer items-start gap-2 text-sm text-body">
          <input
            checked={scenario === "controlled_api_evolution"}
            name="scenario"
            onChange={() => setScenario("controlled_api_evolution")}
            type="radio"
            value="controlled_api_evolution"
          />
          <span>
            Controlled API evolution{" "}
            <span className="font-mono text-xs">FIXTURE</span>
          </span>
        </label>
        <label className="flex cursor-pointer items-start gap-2 text-sm text-body">
          <input
            checked={scenario === "current_configured_solari"}
            name="scenario"
            onChange={() => setScenario("current_configured_solari")}
            type="radio"
            value="current_configured_solari"
          />
          <span>Current configured Solari ecosystem</span>
        </label>
      </fieldset>
      <button
        className="rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white disabled:cursor-wait disabled:opacity-60"
        disabled={pending}
        onClick={start}
        type="button"
      >
        {pending ? "Starting…" : "Start verification"}
      </button>
      {error ? (
        <p className="mt-3 text-sm text-error-deep" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
