import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";

export const dynamic = "force-dynamic";

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const identity = await getApiIdentity();
  if (!identity) redirect("/sign-in");
  const { projectId } = await params;
  const api = apiFor(identity);
  const [{ data: project, response }, { data: me }] = await Promise.all([
    api.GET("/v1/projects/{project_id}", {
      params: { path: { project_id: projectId } },
    }),
    api.GET("/v1/me"),
  ]);
  if (response.status === 404) notFound();
  if (!project || !me?.workspace.onboarding_complete) redirect("/onboarding");
  const configuration = me.onboarding.product_id
    ? await api.GET("/v1/products/{product_id}/configuration", {
        params: { path: { product_id: me.onboarding.product_id } },
      })
    : null;
  return (
    <main className="min-h-screen bg-canvas-soft text-ink" id="main-content">
      <header className="border-b border-hairline bg-canvas">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
          <p className="text-sm font-medium">
            NOXYN{" "}
            <span className="font-normal text-body">/ {project.name}</span>
          </p>
          <span className="rounded-full bg-success-soft px-3 py-1 text-xs font-medium text-success-deep">
            Configuration v1 saved
          </span>
        </div>
      </header>
      <section className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
        <p className="font-mono text-xs text-body">SOLARI / SANDBOX</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em]">
          {project.name} is ready for verification.
        </h1>
        <p className="mt-3 max-w-xl text-body">
          Noxyn will find API ecosystem drift; Solari Sandboxes will provide
          reproducible runtime evidence.
        </p>
        <div className="mt-10 grid gap-4 md:grid-cols-2">
          <article className="rounded-lg border border-hairline bg-canvas p-5 shadow-card">
            <p className="font-mono text-xs text-body">PRODUCT</p>
            <h2 className="mt-2 text-xl font-semibold">Sandbox</h2>
            <p className="mt-4 text-sm text-body">
              The only active MVP product. Browser and Desktop remain
              intentionally out of scope.
            </p>
          </article>
          <article className="rounded-lg border border-hairline bg-canvas p-5 shadow-card">
            <p className="font-mono text-xs text-body">CONFIGURATION</p>
            <h2 className="mt-2 text-xl font-semibold">Immutable v1</h2>
            <p className="mt-4 text-sm text-body">
              {configuration?.data
                ? `${configuration.data.sources.length} sources · ${configuration.data.packages.length} SDK package identities`
                : "Configuration evidence unavailable."}
            </p>
          </article>
        </div>
        <div className="mt-8 flex flex-wrap gap-3">
          {me.onboarding.product_id ? (
            <Link
              className="inline-flex rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white"
              href={`/projects/${projectId}/products/${me.onboarding.product_id}/runs`}
            >
              Open Sandbox runs
            </Link>
          ) : null}
          <Link
            className="inline-flex rounded-md border border-hairline bg-canvas px-4 py-2.5 text-sm font-medium"
            href="/onboarding"
          >
            Review setup
          </Link>
        </div>
      </section>
    </main>
  );
}
