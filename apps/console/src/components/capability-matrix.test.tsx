import type { components } from "@noxyn/generated-client";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { CapabilityMatrix } from "./capability-matrix";

type Matrix = components["schemas"]["MatrixView"];
type Runtime = components["schemas"]["RuntimeCellView"];

const goRuntime: Runtime = {
  state: "PASS",
  summary: "The controlled Go example subject passed.",
  language: "go",
  sourceSurface: "go",
  infrastructureState: "PASS",
  subjectState: "PASS",
  executionId: "00000000-0000-0000-0000-000000000004",
  backend: "REPLAY",
};

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
    aligned: 1,
    suspected: 0,
    notExpected: 0,
    unverified: 0,
  },
  rows: [
    {
      capabilityId: "sandbox.create.memory_mb",
      label: "Memory limit",
      cells: [],
      runtime: goRuntime,
      runtimeCells: [goRuntime],
    },
  ],
} as Matrix;

describe("CapabilityMatrix", () => {
  it("renders Go runtime evidence with its execution deep link and separate states", () => {
    const markup = renderToStaticMarkup(
      <CapabilityMatrix
        matrix={matrix}
        onSelect={() => undefined}
        productId="product-id"
        projectId="project-id"
        runId="run-id"
        selected={null}
      />,
    );

    expect((markup.match(/Go runtime/g) ?? []).length).toBeGreaterThanOrEqual(
      2,
    );
    expect(markup).toContain(
      "Infrastructure PASS · Subject PASS · REPLAY · FIXTURE",
    );
    expect(markup).toContain(
      "/projects/project-id/products/product-id/runs/run-id/executions/00000000-0000-0000-0000-000000000004",
    );
  });
});
