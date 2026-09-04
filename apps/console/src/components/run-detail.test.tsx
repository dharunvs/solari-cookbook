import type { components } from "@noxyn/generated-client";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { RunDetail } from "./run-detail";

type Matrix = components["schemas"]["MatrixView"];
type Execution = components["schemas"]["ExecutionView"];
type Run = components["schemas"]["RunView"];

const executions = [
  { id: "python-execution", language: "python" },
  { id: "typescript-execution", language: "typescript" },
  { id: "go-execution", language: "go" },
].map(
  (execution) =>
    ({
      ...execution,
      phase: "VERIFY",
      source_surface: execution.language,
      infrastructure_state: "PASS",
      subject_state: execution.language === "python" ? "FAIL" : "PASS",
      backend: "REPLAY",
    }) as Execution,
);

const matrix = {
  schemaVersion: "noxyn-static-analysis-result/1.0",
  scenario: "sandbox-create-evolution",
  fixture: true,
  parserVersion: "test",
  manifestSha256: "a".repeat(64),
  contractDiff: {
    capabilityId: "sandbox.create.memory_mb",
    before: "memory",
    after: "memMb",
    classification: "RENAMED",
  },
  packages: {},
  summary: {
    capabilities: 1,
    aligned: 0,
    suspected: 1,
    notExpected: 0,
    unverified: 0,
  },
  rows: [],
  parity: {
    state: "DIFFERENT",
    summary:
      "Python reproduces the stale parameter while TypeScript and Go pass with memMb and MemMb.",
    comparedLanguages: ["python", "typescript", "go"],
  },
} as Matrix;

describe("RunDetail", () => {
  it("summarizes Python, TypeScript, and Go parity with immutable evidence links", () => {
    const markup = renderToStaticMarkup(
      <RunDetail
        initialAnalysis={{
          matrix,
          findings: [],
          executions,
          proposals: [],
        }}
        initialRun={
          {
            id: "run-id",
            state: "COMPLETED",
            configuration_version: 1,
            attempt: 1,
            max_attempts: 1,
            created_at: "2026-09-04T00:00:00Z",
            completed_at: "2026-09-04T00:01:00Z",
          } as Run
        }
        productId="product-id"
        projectId="project-id"
      />,
    );

    expect(markup).toContain("Python, TypeScript, and Go");
    expect(markup).toContain("View Python execution evidence");
    expect(markup).toContain("View TypeScript execution evidence");
    expect(markup).toContain("View Go execution evidence");
    for (const execution of executions) {
      expect(markup).toContain(
        `/projects/project-id/products/product-id/runs/run-id/executions/${execution.id}`,
      );
    }
  });

  it("renders a current no-drift run without calling it a controlled fixture", () => {
    const markup = renderToStaticMarkup(
      <RunDetail
        initialAnalysis={{
          matrix: { ...matrix, fixture: false, scenario: "current-configured-solari" },
          findings: [],
          executions: executions.map(
            (execution) => ({ ...execution, subject_state: "PASS" }) as Execution,
          ),
          proposals: [],
        }}
        initialRun={{
          id: "current-run-id",
          state: "COMPLETED",
          scenario: "current_configured_solari",
          configuration_version: 1,
          attempt: 1,
          max_attempts: 1,
          created_at: "2026-09-04T00:00:00Z",
          completed_at: "2026-09-04T00:01:00Z",
        } as Run}
        productId="product-id"
        projectId="project-id"
      />,
    );

    expect(markup).toContain("Current configured Solari ecosystem");
    expect(markup).toContain("No reproduced drift");
    expect(markup).toContain("NO FINDINGS");
    expect(markup).toContain("View Go execution evidence");
    expect(markup).not.toContain("CONTROLLED FIXTURE");
  });
});
