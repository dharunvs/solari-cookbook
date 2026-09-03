"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Draft = {
  current_step: "project" | "product" | "configuration" | "complete";
  project_name?: string | null;
  project_slug?: string | null;
};

function SubmitButton({ children }: { children: string }) {
  return (
    <button
      className="rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white"
      type="submit"
    >
      {children}
    </button>
  );
}

export function OnboardingFlow({ draft }: { draft: Draft }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  async function submit(action: string, formData?: FormData) {
    setError(null);
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
  }
  const steps = ["Project", "Product", "Configuration", "Ready"];
  const names = { project: 0, product: 1, configuration: 2, complete: 3 };
  return (
    <section className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <ol
        aria-label="Onboarding progress"
        className="mb-12 grid grid-cols-4 gap-2"
      >
        {steps.map((step, index) => (
          <li key={step}>
            <div
              className={
                index <= names[draft.current_step]
                  ? "h-1 rounded bg-ink"
                  : "h-1 rounded bg-hairline"
              }
            />
            <p
              className={
                index === names[draft.current_step]
                  ? "mt-2 text-xs font-medium"
                  : "mt-2 text-xs text-body"
              }
            >
              {step}
            </p>
          </li>
        ))}
      </ol>
      {draft.current_step === "project" ? (
        <form
          action={(formData) => submit("create-project", formData)}
          className="space-y-5"
        >
          <div>
            <p className="font-mono text-xs text-body">01 / PROJECT</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em]">
              Start with Solari.
            </h1>
            <p className="mt-3 text-body">
              Create the private project that Noxyn will verify.
            </p>
          </div>
          <label className="block text-sm font-medium">
            Project name
            <input
              autoComplete="off"
              className="mt-2 w-full rounded-md border border-hairline bg-canvas px-3 py-2"
              defaultValue={draft.project_name ?? "Solari"}
              name="projectName"
              required
            />
          </label>
          <label className="block text-sm font-medium">
            Project slug
            <input
              autoComplete="off"
              className="mt-2 w-full rounded-md border border-hairline bg-canvas px-3 py-2 font-mono"
              defaultValue={draft.project_slug ?? "solari"}
              name="projectSlug"
              pattern="[a-z0-9]+(-[a-z0-9]+)*"
              required
              spellCheck={false}
            />
          </label>
          <SubmitButton>Create project</SubmitButton>
        </form>
      ) : null}
      {draft.current_step === "product" ? (
        <div>
          <p className="font-mono text-xs text-body">02 / PRODUCT</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em]">
            Choose what to verify first.
          </h1>
          <div className="mt-8 grid gap-3">
            <form
              action={() => submit("create-product")}
              className="rounded-lg border border-ink bg-canvas p-5 shadow-card"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold">Sandbox</h2>
                  <p className="mt-1 text-sm text-body">
                    Disposable execution environments for reproducible evidence.
                  </p>
                </div>
                <span className="rounded-full bg-success-soft px-2 py-1 text-xs text-success-deep">
                  Available
                </span>
              </div>
              <div className="mt-5">
                <SubmitButton>Add Sandbox</SubmitButton>
              </div>
            </form>
            {["Browser", "Desktop"].map((product) => (
              <article
                className="rounded-lg border border-hairline bg-canvas-soft p-5 opacity-70"
                key={product}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">{product}</h2>
                    <p className="mt-1 text-sm text-body">
                      Informational for this MVP.
                    </p>
                  </div>
                  <button
                    aria-disabled="true"
                    className="cursor-not-allowed rounded-md border border-hairline px-3 py-2 text-xs"
                    disabled
                  >
                    Coming later
                  </button>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}
      {draft.current_step === "configuration" ? (
        <form
          action={(formData) => submit("save-configuration", formData)}
          className="space-y-6"
        >
          <div>
            <p className="font-mono text-xs text-body">03 / CONFIGURATION</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em]">
              Configure Sandbox verification.
            </h1>
            <p className="mt-3 text-body">
              This saves an immutable configuration v1. No Solari credential is
              requested here.
            </p>
          </div>
          <fieldset>
            <legend className="text-sm font-medium">Sources to verify</legend>
            <div className="mt-3 grid gap-2">
              {[
                "Cookbook examples",
                "Documentation snippets",
                "Published SDK packages",
              ].map((source) => (
                <label
                  className="flex items-center gap-3 rounded-md border border-hairline bg-canvas p-3 text-sm"
                  key={source}
                >
                  <input
                    defaultChecked
                    name="sources"
                    type="checkbox"
                    value={source.toLowerCase().replaceAll(" ", "-")}
                  />
                  {source}
                </label>
              ))}
            </div>
          </fieldset>
          <div className="rounded-lg border border-hairline bg-canvas-soft p-4">
            <p className="font-mono text-xs text-body">READINESS CHECK</p>
            <ul className="mt-3 space-y-2 text-sm">
              <li>✓ Solari project selected</li>
              <li>✓ Sandbox product selected</li>
              <li>✓ Python, TypeScript, and Go identities pinned</li>
            </ul>
          </div>
          <SubmitButton>Save configuration v1</SubmitButton>
        </form>
      ) : null}
      {error ? (
        <p className="mt-5 text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
