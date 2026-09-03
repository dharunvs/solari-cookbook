import { describe, expect, it } from "vitest";

import { createNoxynClient } from "./index.js";

describe("generated client boundary", () => {
  it("imports and calls the typed health operation", async () => {
    const client = createNoxynClient({
      baseUrl: "https://api.noxyn.test",
      fetch: async () =>
        new Response(
          JSON.stringify({
            status: "ok",
            service: "noxyn-api",
            version: "0.1.0",
            database: "connected",
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
    });

    const { data, error } = await client.GET("/health");

    expect(error).toBeUndefined();
    expect(data?.database).toBe("connected");
  });
});
