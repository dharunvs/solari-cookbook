import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { RunStatus } from "@/components/run-status";
import { StartRunButton } from "@/components/start-run-button";
import { apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";

export const dynamic = "force-dynamic";

export default async function RunsPage({
  params,
}: {
  params: Promise<{ projectId: string; productId: string }>;
}) {
  const identity = await getApiIdentity();
  if (!identity) redirect("/sign-in");
  const { projectId, productId } = await params;
  const api = apiFor(identity);
  const [
    { data: project, response: projectResponse },
    { data: runs, response: runsResponse },
  ] = await Promise.all([
    api.GET("/v1/projects/{project_id}", {
      params: { path: { project_id: projectId } },
    }),
    api.GET("/v1/products/{product_id}/runs", {
      params: { path: { product_id: productId }, query: { limit: 25 } },
    }),
  ]);
  if (projectResponse.status === 404 || runsResponse.status === 404) notFound();
  if (!project || !runs) throw new Error("Run history is unavailable.");
  const runPath = `/projects/${projectId}/products/${productId}/runs`;
  return (
    <section className="py-10 sm:py-12">
      <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-end">
        <div>
          <p className="font-mono text-xs text-body">VERIFICATION RUNS</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-balance">
            Verify configured Solari sources.
          </h1>
          <p className="mt-3 max-w-2xl text-body">
            Select either the controlled fixture or the reviewed current source
            set. Both preserve immutable source evidence.
          </p>
        </div>
        <StartRunButton productId={productId} runPath={runPath} />
      </div>
      <section className="mt-10 overflow-hidden rounded-lg border border-hairline bg-canvas shadow-card">
        <div className="border-b border-hairline px-5 py-4">
          <h2 className="font-medium">Run history</h2>
        </div>
        {runs.items.length ? (
          <ul className="divide-y divide-hairline">
            {runs.items.map((run) => (
              <li key={run.id}>
                <Link
                  className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
                  href={`${runPath}/${run.id}`}
                >
                  <div>
                    <p className="text-sm font-medium">
                      {run.scenario === "controlled_api_evolution"
                        ? "Controlled API evolution · Fixture"
                        : "Current configured Solari ecosystem"}
                    </p>
                    <p className="mt-1 font-mono text-xs text-body">
                      {run.id.slice(0, 8)} · config v{run.configuration_version}{" "}
                      · attempt {run.attempt}
                    </p>
                  </div>
                  <RunStatus state={run.state} />
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <div className="px-5 py-12 text-center">
            <p className="font-medium">No runs yet</p>
            <p className="mt-2 text-sm text-body">
              Your first run creates immutable source snapshots, a static
              matrix, suspected findings, and Python execution evidence.
            </p>
          </div>
        )}
      </section>
    </section>
  );
}
