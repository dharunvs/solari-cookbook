import { expect, test } from "@playwright/test";
import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

const exec = promisify(execFile);
const repositoryRoot = path.resolve(process.cwd(), "../..");

test("registration, resume, and Sandbox configuration journey", async ({
  page,
}) => {
  test.setTimeout(120_000);
  const email = `builder-${Date.now()}@example.com`;

  await page.goto("/sign-up");
  await page.getByLabel("Work email").fill(email);
  await page.getByRole("button", { name: "Create private workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Start with Solari." }),
  ).toBeVisible();

  await page.getByLabel("Project name").fill("Solari");
  await page.getByRole("button", { name: "Create project" }).click();
  await expect(
    page.getByRole("heading", { name: "Choose what to verify first." }),
  ).toBeVisible();

  // A refresh retains the server-side onboarding draft and the authenticated workspace.
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Choose what to verify first." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Coming later" }).first(),
  ).toBeDisabled();

  await page.getByRole("button", { name: "Add Sandbox" }).click();
  await expect(
    page.getByRole("heading", { name: "Configure Sandbox verification." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Save configuration v1" }).click();
  await expect(
    page.getByRole("heading", { name: "Solari is ready for verification." }),
  ).toBeVisible();

  // Returning users go directly to their Solari project overview.
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Solari is ready for verification." }),
  ).toBeVisible();

  const runsHref = await page
    .getByRole("link", { name: "Open Sandbox runs" })
    .getAttribute("href");
  expect(runsHref).toBeTruthy();
  await page.goto(runsHref!);
  await expect(
    page.getByRole("heading", { name: "Verify the controlled evolution." }),
  ).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "Start verification" }).click();
  await expect(
    page.getByRole("heading", { name: "Controlled API evolution" }),
  ).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Queued", { exact: true })).toBeVisible();

  // Refresh proves the run is server-persisted, then a separately invoked worker
  // completes it through the PostgreSQL lease and immutable artifact path.
  await page.reload();
  await expect(page.getByText("Queued", { exact: true })).toBeVisible();
  for (let attempt = 0; attempt < 8; attempt += 1) {
    await exec(
      "uv",
      [
        "run",
        "--package",
        "noxyn-verification-worker",
        "noxyn-verification-worker",
        "--once",
      ],
      {
        cwd: repositoryRoot,
      },
    );
    if (
      await page.getByText("Verification complete", { exact: true }).isVisible()
    )
      break;
    await page.waitForTimeout(1700);
  }
  await expect(
    page.getByText("Verification complete", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/bytes$/)).toBeVisible();
  await expect(page.getByText("Suspected").first()).toBeVisible();
  await expect(page.getByText("Fixes verified")).toBeVisible();
  await expect(page.getByText("DIFFERENT", { exact: true })).toBeVisible();
  await expect(
    page.getByText(
      "Python reproduces the stale parameter while TypeScript passes with memMb.",
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("link", {
      name: "Python runtime FAIL. Open execution evidence",
    }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "View Python execution evidence" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Runtime evidence" }),
  ).toBeVisible();
  await expect(page.getByText(/Deterministic replay evidence/)).toBeVisible();
  await expect(
    page.getByText(/unexpected keyword argument 'memory'/),
  ).toBeVisible();
  await expect(page.getByText(/842 ms · PASS/)).toBeVisible();
  await page.getByRole("link", { name: "Back to run" }).click();

  await page
    .getByRole("link", { name: "View TypeScript execution evidence" })
    .click();
  await expect(
    page.getByText("TYPESCRIPT EXECUTION", { exact: false }),
  ).toBeVisible();
  await expect(page.getByText("@solarisdk/sandbox@0.1.2")).toBeVisible();
  await expect(
    page.getByText("No finding: this aligned subject passed."),
  ).toBeVisible();
  await page.getByRole("link", { name: "Back to run" }).click();

  await page
    .getByRole("button", { name: "Python: SUSPECTED. Open evidence" })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "sandbox.create.memory_mb / Python",
    }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Review finding" }).click();
  await expect(
    page.getByRole("heading", {
      name: "sandbox.create.memory_mb / Python example",
    }),
  ).toBeVisible();
  await expect(
    page.getByText(/Infrastructure PASS · Subject FAIL/),
  ).toBeVisible();
  await expect(page.getByText(/failure was reproduced/)).toBeVisible();
  await page.getByRole("button", { name: "Generate proposal" }).click();
  await expect(
    page.getByRole("heading", { name: "One reviewed parameter rename" }),
  ).toBeVisible({ timeout: 30_000 });
  await expect(page.getByLabel("Unified proposal diff")).toContainText(
    "mem_mb=2048",
  );
  await page.getByRole("button", { name: "Verify proposed fix" }).click();
  for (let attempt = 0; attempt < 8; attempt += 1) {
    await exec(
      "uv",
      [
        "run",
        "--package",
        "noxyn-verification-worker",
        "noxyn-verification-worker",
        "--once",
      ],
      { cwd: repositoryRoot },
    );
    if (await page.getByText("Fresh verification passed").isVisible()) break;
    await page.waitForTimeout(1700);
  }
  await expect(page.getByText("Fresh verification passed")).toBeVisible();
  await expect(page.getByText(/repository was not changed/i)).toBeVisible();
  await page.getByRole("link", { name: "Capability matrix" }).click();

  await page
    .getByRole("button", { name: "Python docs: SUSPECTED. Open evidence" })
    .click();
  await page.getByRole("link", { name: "Review finding" }).click();
  await expect(
    page.getByRole("heading", {
      name: "sandbox.create.memory_mb / Python documentation",
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Generate proposal" }).click();
  await expect(
    page.getByRole("heading", { name: "One reviewed parameter rename" }),
  ).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "Verify proposed fix" }).click();
  for (let attempt = 0; attempt < 8; attempt += 1) {
    await exec(
      "uv",
      [
        "run",
        "--package",
        "noxyn-verification-worker",
        "noxyn-verification-worker",
        "--once",
      ],
      { cwd: repositoryRoot },
    );
    if (await page.getByText("Fresh verification passed").isVisible()) break;
    await page.waitForTimeout(1700);
  }
  await expect(page.getByText("Fresh verification passed")).toBeVisible();
  await page.getByRole("link", { name: "Capability matrix" }).click();
  await expect(page.getByText("FIXES VERIFIED", { exact: true })).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("button", { name: /^Python SUSPECTED/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /^TypeScript runtime PASS/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /^Python docs runtime FAIL/ }),
  ).toBeVisible();

  await page.getByRole("link", { name: "Run history" }).click();
  await page.getByRole("button", { name: "Start verification" }).click();
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Cancel run" }).click();
  await expect(page.getByText("Cancelled", { exact: true })).toBeVisible({
    timeout: 30_000,
  });
  await page.reload();
  await expect(page.getByText("Cancelled", { exact: true })).toBeVisible({
    timeout: 30_000,
  });

  await page.getByRole("link", { name: "Run history" }).click();
  await page
    .getByLabel("Current configured Solari ecosystem")
    .check();
  await page.getByRole("button", { name: "Start verification" }).click();
  await expect(
    page.getByRole("heading", { name: "Current configured Solari ecosystem" }),
  ).toBeVisible({ timeout: 30_000 });
  for (let attempt = 0; attempt < 8; attempt += 1) {
    await exec(
      "uv",
      [
        "run",
        "--package",
        "noxyn-verification-worker",
        "noxyn-verification-worker",
        "--once",
      ],
      { cwd: repositoryRoot },
    );
    if (await page.getByText("MATCH", { exact: true }).isVisible()) break;
    await page.waitForTimeout(1700);
  }
  await expect(page.getByText("NO FINDINGS", { exact: true })).toBeVisible();
  await expect(page.getByText("MATCH", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "View Go execution evidence" }).click();
  await expect(page.getByText("GO EXECUTION", { exact: false })).toBeVisible();
  await expect(
    page.getByText("github.com/solari-sdk/solari-sandbox-go@v0.1.2"),
  ).toBeVisible();
  await expect(page.getByText(/Deterministic replay evidence/)).toBeVisible();
});
