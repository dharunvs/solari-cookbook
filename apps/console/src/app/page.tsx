import Link from "next/link";
import { redirect } from "next/navigation";

import { apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";

export const dynamic = "force-dynamic";

export default async function Home() {
  const identity = await getApiIdentity();
  if (!identity) redirect("/sign-in");
  const { data, error, response } = await apiFor(identity).GET("/v1/me");
  if (response.status === 401 || response.status === 403)
    redirect("/auth-error");
  if (error || !data) {
    return (
      <main
        className="grid min-h-screen place-items-center bg-canvas-soft px-4 text-ink"
        id="main-content"
      >
        <section className="w-full max-w-lg rounded-xl border border-hairline bg-canvas p-7 shadow-card">
          <p className="font-mono text-xs text-body">NOXYN / CONNECTION</p>
          <h1 className="mt-3 text-2xl font-semibold tracking-[-0.04em]">
            Your workspace is temporarily unavailable.
          </h1>
          <p className="mt-3 text-sm leading-6 text-body">
            Noxyn could not reach the workspace service. Your setup has not been
            changed. Check that the API is running, then try again.
          </p>
          <Link
            className="mt-6 inline-flex rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white"
            href="/"
          >
            Try again
          </Link>
        </section>
      </main>
    );
  }
  redirect(
    data.workspace.onboarding_complete && data.project_id
      ? `/projects/${data.project_id}`
      : "/onboarding",
  );
}
