import { describe, expect, it } from "vitest";

import {
  isCurrentOnboardingStep,
  onboardingStepPath,
  resolveOnboardingStep,
} from "./step";

describe("onboarding step reconciliation", () => {
  it("uses the persisted durable step when the query is missing or invalid", () => {
    expect(resolveOnboardingStep("project")).toBe("project");
    expect(resolveOnboardingStep("product")).toBe("product");
    expect(resolveOnboardingStep("configuration")).toBe("configuration");
    expect(isCurrentOnboardingStep("project", undefined)).toBe(false);
    expect(isCurrentOnboardingStep("product", "workspace")).toBe(false);
    expect(isCurrentOnboardingStep("configuration", "product")).toBe(false);
  });

  it("accepts only the URL for the persisted durable step", () => {
    expect(isCurrentOnboardingStep("project", "project")).toBe(true);
    expect(isCurrentOnboardingStep("product", "product")).toBe(true);
    expect(isCurrentOnboardingStep("configuration", "configuration")).toBe(
      true,
    );
  });

  it("keeps the canonical path stable", () => {
    expect(onboardingStepPath("configuration")).toBe(
      "/onboarding?step=configuration",
    );
  });
});
