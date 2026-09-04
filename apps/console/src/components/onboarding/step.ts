export const onboardingSteps = ["project", "product", "configuration"] as const;

export type OnboardingStep = (typeof onboardingSteps)[number];
export type PersistedOnboardingStep = OnboardingStep | "complete";

export function resolveOnboardingStep(
  persistedStep: PersistedOnboardingStep,
): OnboardingStep | "complete" {
  return persistedStep;
}

export function isCurrentOnboardingStep(
  persistedStep: OnboardingStep,
  queryStep: unknown,
): boolean {
  return queryStep === persistedStep;
}

export function onboardingStepPath(step: OnboardingStep): string {
  return `/onboarding?step=${step}`;
}
