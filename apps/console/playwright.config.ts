import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  use: { baseURL: "http://127.0.0.1:3000", trace: "retain-on-failure" },
  webServer: [
    {
      command:
        "NOXYN_E2E_AUTH_BYPASS=true uv run --package noxyn-api uvicorn noxyn_api.main:app --host 127.0.0.1 --port 8000",
      cwd: "../..",
      reuseExistingServer: false,
      url: "http://127.0.0.1:8000/health",
    },
    {
      command: "NOXYN_E2E_AUTH_BYPASS=true pnpm --filter @noxyn/console dev",
      cwd: "../..",
      reuseExistingServer: false,
      url: "http://127.0.0.1:3000/sign-up",
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
