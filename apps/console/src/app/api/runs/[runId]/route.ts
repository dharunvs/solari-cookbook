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
  const { data, response } = await apiFor(identity).GET("/v1/runs/{run_id}", {
    params: { path: { run_id: runId } },
  });
  if (!data) {
    return NextResponse.json(
      { error: await apiError(response) },
      { status: response.status },
    );
  }
  return NextResponse.json(data);
}
