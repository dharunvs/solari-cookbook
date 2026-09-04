import { notFound, redirect } from "next/navigation";

import { RunDetail } from "@/components/run-detail";
import { apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";

export const dynamic = "force-dynamic";

export default async function RunPage({
  params,
}: {
  params: Promise<{ projectId: string; productId: string; runId: string }>;
}) {
  const identity = await getApiIdentity();
  if (!identity) redirect("/sign-in");
  const { projectId, productId, runId } = await params;
  const { data: run, response } = await apiFor(identity).GET(
    "/v1/runs/{run_id}",
    {
      params: { path: { run_id: runId } },
    },
  );
  if (response.status === 404) notFound();
  if (!run || run.product_id !== productId) notFound();
  let initialAnalysis = null;
  if (run.state === "COMPLETED") {
    const api = apiFor(identity);
    const [matrixResult, findingsResult, executionsResult, proposalsResult] =
      await Promise.all([
        api.GET("/v1/runs/{run_id}/matrix", {
          params: { path: { run_id: runId } },
        }),
        api.GET("/v1/runs/{run_id}/findings", {
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
      !matrixResult.data ||
      !findingsResult.data ||
      !executionsResult.data ||
      !proposalsResult.data
    )
      throw new Error("Verification evidence is unavailable.");
    initialAnalysis = {
      matrix: matrixResult.data,
      findings: findingsResult.data.items,
      executions: executionsResult.data.items,
      proposals: proposalsResult.data.items,
    };
  }
  return (
    <section className="py-10 sm:py-12">
      <RunDetail
        initialAnalysis={initialAnalysis}
        initialRun={run}
        productId={productId}
        projectId={projectId}
      />
    </section>
  );
}
