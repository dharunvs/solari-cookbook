import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("@clerk/nextjs", () => ({
  UserButton: () => <button type="button">Account menu</button>,
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/projects/solari/products/sandbox/runs/run-1",
}));

import { AppShell } from "./app-shell";

describe("AppShell", () => {
  it("provides landmarks, project context, and marks Runs as current", () => {
    const markup = renderToStaticMarkup(
      <AppShell productId="sandbox" projectId="solari" projectName="Solari">
        <h1>Run detail</h1>
      </AppShell>,
    );

    expect(markup).toContain('id="main-content"');
    expect(markup).toContain('aria-label="Breadcrumb"');
    expect(markup).toContain('aria-label="Product navigation"');
    expect(markup).toContain("Solari");
    expect(markup).toContain("Sandbox");
    expect(markup).toContain('href="/projects/solari/products/sandbox/runs"');
    expect(markup).toContain('aria-current="page"');
  });
});
