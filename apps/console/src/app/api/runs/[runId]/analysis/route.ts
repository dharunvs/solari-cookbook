import { NextResponse } from "next/server";

import { apiError, apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";

export async function GET(
  _request: Request,
  context: { params: Promise<{ runId: string }> },
) {
  const identity = await getApiIdentity();
  if (!identity) {
    return NextResponse.json(
      { error: "Authentication required." },
      { status: 401 },
    );
  }
  const { runId } = await context.params;
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
  if (!matrixResult.data) {
    return NextResponse.json(
      { error: await apiError(matrixResult.response) },
      { status: matrixResult.response.status },
    );
  }
  if (!findingsResult.data) {
    return NextResponse.json(
      { error: await apiError(findingsResult.response) },
      { status: findingsResult.response.status },
    );
  }
  if (!executionsResult.data) {
    return NextResponse.json(
      { error: await apiError(executionsResult.response) },
      { status: executionsResult.response.status },
    );
  }
  if (!proposalsResult.data) {
    return NextResponse.json(
      { error: await apiError(proposalsResult.response) },
      { status: proposalsResult.response.status },
    );
  }
  return NextResponse.json({
    matrix: matrixResult.data,
    findings: findingsResult.data.items,
    executions: executionsResult.data.items,
    proposals: proposalsResult.data.items,
  });
}
