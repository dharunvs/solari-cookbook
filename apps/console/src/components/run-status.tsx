import type { components } from "@noxyn/generated-client";

export type Run = components["schemas"]["RunView"];

const labels: Record<Run["state"], string> = {
  QUEUED: "Queued",
  SNAPSHOTTING: "Snapshotting",
  ANALYZING: "Analyzing",
  VERIFYING: "Verifying",
  PROPOSING: "Proposing",
  REVERIFYING: "Reverifying",
  CANCEL_REQUESTED: "Cancelling",
  COMPLETED: "Verification complete",
  FAILED: "Failed",
  CANCELLED: "Cancelled",
};

export const terminalStates = new Set<Run["state"]>([
  "COMPLETED",
  "FAILED",
  "CANCELLED",
]);

export function RunStatus({ state }: { state: Run["state"] }) {
  const tone =
    state === "COMPLETED"
      ? "bg-success-soft text-success-deep"
      : state === "FAILED" || state === "CANCELLED"
        ? "bg-error-soft text-error-deep"
        : "bg-warning-soft text-warning-deep";
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${tone}`}
    >
      {labels[state]}
    </span>
  );
}
