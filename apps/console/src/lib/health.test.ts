import { describe, expect, it } from "vitest";

import type { FoundationHealth } from "./health";

function statusLabel(result: FoundationHealth): string {
  return result.state === "ready" ? result.health.database : "unavailable";
}

describe("foundation health state", () => {
  it("preserves the generated API database state", () => {
    const result: FoundationHealth = {
      state: "ready",
      health: {
        status: "ok",
        service: "noxyn-api",
        version: "0.1.0",
        database: "connected",
      },
    };

    expect(statusLabel(result)).toBe("connected");
  });
});
