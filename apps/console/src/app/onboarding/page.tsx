import { redirect } from "next/navigation";

import { OnboardingFlow } from "@/components/onboarding-flow";
import { apiFor } from "@/lib/api";
import { getApiIdentity } from "@/lib/identity";

export const dynamic = "force-dynamic";

export default async function OnboardingPage() {
  const identity = await getApiIdentity();
  if (!identity) redirect("/sign-in");
  const { data } = await apiFor(identity).GET("/v1/me");
  if (!data) throw new Error("Your private workspace is unavailable.");
  if (data.workspace.onboarding_complete && data.project_id)
    redirect(`/projects/${data.project_id}`);
  return (
    <main className="min-h-screen bg-canvas-soft text-ink" id="main-content">
      <header className="border-b border-hairline bg-canvas px-4 py-5 sm:px-6">
        <p className="mx-auto max-w-2xl text-sm font-medium tracking-[-0.02em]">
          NOXYN <span className="font-normal text-body">/ Solari setup</span>
        </p>
      </header>
      <OnboardingFlow draft={data.onboarding} />
    </main>
  );
}
