import { afterEach, describe, expect, it, vi } from "vitest";

import {
  browserApi,
  hasBrowserSessionExpired,
  isUnauthorized,
  resetBrowserSessionExpiryForTests,
  SessionExpiredError,
} from "./browser-api";
import { safeReturnPath } from "./identity";

afterEach(() => {
  resetBrowserSessionExpiryForTests();
  vi.unstubAllGlobals();
});

describe("browser API session expiry", () => {
  it("classifies only 401 responses as session expiry", () => {
    expect(isUnauthorized(new Response(null, { status: 401 }))).toBe(true);
    expect(isUnauthorized(new Response(null, { status: 403 }))).toBe(false);
    expect(isUnauthorized(new Response(null, { status: 404 }))).toBe(false);
  });

  it("blocks later polling requests after a 401", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 401 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(browserApi("/api/runs/run-id")).rejects.toBeInstanceOf(
      SessionExpiredError,
    );
    await expect(browserApi("/api/runs/run-id")).rejects.toBeInstanceOf(
      SessionExpiredError,
    );

    expect(hasBrowserSessionExpired()).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe("safe return paths", () => {
  it("preserves same-origin protected paths", () => {
    expect(safeReturnPath("/projects/project/runs?tab=all#latest")).toBe(
      "/projects/project/runs?tab=all#latest",
    );
  });

  it("rejects external and malformed paths", () => {
    expect(safeReturnPath("https://example.com")).toBeNull();
    expect(safeReturnPath("//example.com/path")).toBeNull();
    expect(safeReturnPath("/\\example.com/path")).toBeNull();
    expect(safeReturnPath("/path\nnext")).toBeNull();
    expect(safeReturnPath("javascript:alert(1)")).toBeNull();
    expect(safeReturnPath(undefined)).toBeNull();
  });
});
