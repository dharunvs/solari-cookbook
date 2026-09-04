import { NextResponse } from "next/server";

import { apiError, apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";
import { isSameOrigin } from "@/lib/request-origin";

export async function POST(request: Request) {
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
  const body = (await request.json()) as {
    productId?: unknown;
    idempotencyKey?: unknown;
    scenario?: unknown;
  };
  if (
    typeof body.productId !== "string" ||
    typeof body.idempotencyKey !== "string" ||
    (body.scenario !== "controlled_api_evolution" &&
      body.scenario !== "current_configured_solari")
  ) {
    return NextResponse.json(
      { error: "Run request is invalid." },
      { status: 422 },
    );
  }
  const { data, response } = await apiFor(identity).POST(
    "/v1/products/{product_id}/runs",
    {
      params: { path: { product_id: body.productId } },
      body: { scenario: body.scenario },
      headers: {
        "Idempotency-Key": body.idempotencyKey,
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
  return NextResponse.json(data, { status: response.status });
}
