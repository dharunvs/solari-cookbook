import { NextResponse } from "next/server";

import { apiError, apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";

const idempotency = () => crypto.randomUUID();
const packages = [
  { ecosystem: "python" as const, package: "solari-sandbox", version: "0.2.0" },
  {
    ecosystem: "typescript" as const,
    package: "@solarisdk/sandbox",
    version: "0.1.2",
  },
  {
    ecosystem: "go" as const,
    package: "github.com/solari-sdk/solari-sandbox-go",
    version: "v0.1.2",
  },
];

export async function POST(request: Request) {
  const identity = await getApiIdentity();
  if (!identity)
    return NextResponse.json(
      { error: "Authentication required." },
      { status: 401 },
    );
  const body = (await request.json()) as {
    action?: string;
    projectName?: unknown;
    projectSlug?: unknown;
    sources?: unknown;
  };
  const api = apiFor(identity);
  if (body.action === "save-project-draft") {
    const { data, response } = await api.PATCH("/v1/onboarding", {
      body: {
        current_step: "project",
        project_name: String(body.projectName ?? ""),
        project_slug: String(body.projectSlug ?? ""),
      },
      headers: { "Idempotency-Key": idempotency() },
    });
    if (!data)
      return NextResponse.json(
        { error: await apiError(response) },
        { status: response.status },
      );
    return NextResponse.json({ saved: true });
  }
  if (body.action === "create-project") {
    const { data, response } = await api.POST("/v1/projects", {
      body: {
        name: String(body.projectName ?? ""),
        slug: String(body.projectSlug ?? ""),
      },
      headers: { "Idempotency-Key": idempotency() },
    });
    if (!data)
      return NextResponse.json(
        { error: await apiError(response) },
        { status: response.status },
      );
    return NextResponse.json({ nextPath: "/onboarding?step=product" });
  }
  const me = await api.GET("/v1/me");
  if (!me.data)
    return NextResponse.json(
      { error: await apiError(me.response) },
      { status: me.response.status },
    );
  if (body.action === "create-product" && me.data.onboarding.project_id) {
    const { data, response } = await api.POST(
      "/v1/projects/{project_id}/products",
      {
        params: { path: { project_id: me.data.onboarding.project_id } },
        body: { slug: "sandbox" },
        headers: { "Idempotency-Key": idempotency() },
      },
    );
    if (!data)
      return NextResponse.json(
        { error: await apiError(response) },
        { status: response.status },
      );
    return NextResponse.json({ nextPath: "/onboarding?step=configuration" });
  }
  if (body.action === "save-configuration" && me.data.onboarding.product_id) {
    const sources = Array.isArray(body.sources)
      ? body.sources.filter(
          (source): source is string => typeof source === "string",
        )
      : [];
    const { data, response } = await api.POST(
      "/v1/products/{product_id}/configurations",
      {
        params: { path: { product_id: me.data.onboarding.product_id } },
        body: { sources, packages },
        headers: { "Idempotency-Key": idempotency() },
      },
    );
    if (!data)
      return NextResponse.json(
        { error: await apiError(response) },
        { status: response.status },
      );
    return NextResponse.json({
      nextPath: `/projects/${me.data.onboarding.project_id}`,
    });
  }
  return NextResponse.json(
    { error: "Onboarding state is unavailable." },
    { status: 409 },
  );
}
