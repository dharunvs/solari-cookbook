"use client";

import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";

import { ConfigurationStep } from "./onboarding/configuration-step";
import { ProductStep } from "./onboarding/product-step";
import { OnboardingProgressShell } from "./onboarding/progress-shell";
import { ProjectStep } from "./onboarding/project-step";
import type {
  OnboardingStep,
  PersistedOnboardingStep,
} from "./onboarding/step";

type Draft = {
  current_step: PersistedOnboardingStep;
  project_name?: string | null;
  project_slug?: string | null;
};

export function OnboardingFlow({
  draft,
  step,
}: {
  draft: Draft;
  step: OnboardingStep;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const pendingDraftSave = useRef<Promise<void>>(Promise.resolve());
  const submitting = useRef(false);

  const saveProjectDraft = useCallback(
    async (projectName: string, projectSlug: string) => {
      pendingDraftSave.current = pendingDraftSave.current.then(async () => {
        try {
          const response = await fetch("/api/onboarding", {
            body: JSON.stringify({
              action: "save-project-draft",
              projectName,
              projectSlug,
            }),
            headers: { "Content-Type": "application/json" },
            method: "POST",
          });
          if (!response.ok) {
            const data = (await response.json()) as { error?: string };
            setError(data.error ?? "Could not save your progress.");
          }
        } catch {
          setError("Could not save your progress.");
        }
      });
      await pendingDraftSave.current;
    },
    [],
  );

  async function submit(action: string, formData?: FormData) {
    if (submitting.current) return;
    submitting.current = true;
    setError(null);
    setIsSubmitting(true);
    try {
      if (action === "create-project") await pendingDraftSave.current;
      const response = await fetch("/api/onboarding", {
        body: JSON.stringify({
          action,
          projectName: formData?.get("projectName"),
          projectSlug: formData?.get("projectSlug"),
          sources: formData?.getAll("sources"),
        }),
        headers: { "Content-Type": "application/json" },
        method: "POST",
      });
      const data = (await response.json()) as {
        error?: string;
        nextPath?: string;
      };
      if (!response.ok || !data.nextPath) {
        setError(data.error ?? "Could not save your progress.");
        return;
      }
      router.push(data.nextPath);
      router.refresh();
    } finally {
      submitting.current = false;
      setIsSubmitting(false);
    }
  }

  return (
    <OnboardingProgressShell currentStep={step}>
      {step === "project" ? (
        <ProjectStep
          disabled={isSubmitting}
          onDraftChange={saveProjectDraft}
          onSubmit={(formData) => submit("create-project", formData)}
          projectName={draft.project_name}
          projectSlug={draft.project_slug}
        />
      ) : null}
      {step === "product" ? (
        <ProductStep
          disabled={isSubmitting}
          onSubmit={() => submit("create-product")}
        />
      ) : null}
      {step === "configuration" ? (
        <ConfigurationStep
          disabled={isSubmitting}
          onSubmit={(formData) => submit("save-configuration", formData)}
        />
      ) : null}
      {error ? (
        <p className="mt-5 text-sm text-error-deep" role="alert">
          {error}
        </p>
      ) : null}
    </OnboardingProgressShell>
  );
}
