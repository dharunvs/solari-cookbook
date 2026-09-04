import { onboardingSteps, type OnboardingStep } from "./step";

const stepLabels: Record<OnboardingStep, string> = {
  project: "Project",
  product: "Product",
  configuration: "Configuration",
};

export function OnboardingProgressShell({
  children,
  currentStep,
}: {
  children: React.ReactNode;
  currentStep: OnboardingStep;
}) {
  const currentIndex = onboardingSteps.indexOf(currentStep);

  return (
    <section className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <ol
        aria-label="Onboarding progress"
        className="mb-12 grid grid-cols-3 gap-2"
      >
        {onboardingSteps.map((step, index) => (
          <li key={step}>
            <div
              className={
                index <= currentIndex
                  ? "h-1 rounded bg-ink"
                  : "h-1 rounded bg-hairline"
              }
            />
            <p
              className={
                index === currentIndex
                  ? "mt-2 text-xs font-medium"
                  : "mt-2 text-xs text-body"
              }
            >
              {stepLabels[step]}
            </p>
          </li>
        ))}
      </ol>
      {children}
    </section>
  );
}
