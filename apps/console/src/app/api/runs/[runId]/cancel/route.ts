import { NextResponse } from "next/server";

import { apiError, apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";
import { isSameOrigin } from "@/lib/request-origin";

export async function POST(
  request: Request,
  context: { params: Promise<{ runId: string }> },
) {
  if (!isSameOrigin(request)) {
    return NextResponse.json(
      { error: "Request origin unavailable." },
      { status: 403 },
    );
  }
  const identity = await getApiIdentity();
  if (!identity) {
    return NextResponse.json(
      { error: "Authentication required." },
      { status: 401 },
    );
  }
  const { runId } = await context.params;
  const { data, response } = await apiFor(identity).POST(
    "/v1/runs/{run_id}/cancel",
    {
      params: { path: { run_id: runId } },
      headers: {
        "Idempotency-Key": crypto.randomUUID(),
        "X-CSRF-Token": "same-origin",
      },
    },
  );
  if (!data) {
    return NextResponse.json(
      { error: await apiError(response) },
      { status: response.status },
    );
  }
  return NextResponse.json(data);
}
