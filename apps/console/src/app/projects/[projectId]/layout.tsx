import { notFound, redirect } from "next/navigation";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import { apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";

export const dynamic = "force-dynamic";

export default async function ProjectLayout({
  children,
  params,
}: Readonly<{
  children: ReactNode;
  params: Promise<{ projectId: string }>;
}>) {
  const identity = await getApiIdentity();
  if (!identity) redirect("/sign-in");
  const { projectId } = await params;
  const api = apiFor(identity);
  const [{ data: project, response: projectResponse }, { data: me }] =
    await Promise.all([
      api.GET("/v1/projects/{project_id}", {
        params: { path: { project_id: projectId } },
      }),
      api.GET("/v1/me"),
    ]);
  if (projectResponse.status === 404 || !project) notFound();
  if (!me?.workspace.onboarding_complete || !me.onboarding.product_id)
    redirect("/onboarding");

  return (
    <AppShell
      productId={me.onboarding.product_id}
      projectId={projectId}
      projectName={project.name}
    >
      {children}
    </AppShell>
  );
}
