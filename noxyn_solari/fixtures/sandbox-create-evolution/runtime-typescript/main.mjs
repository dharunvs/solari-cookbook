/** Controlled aligned consumer used by the Phase 6 runtime fixture. */

import { SandboxClient } from "@solarisdk/sandbox";

const sandbox = new SandboxClient({
  apiKey: process.env.SOLARI_API_KEY,
  baseUrl: process.env.SOLARI_API_BASE_URL ?? "https://api.getsolari.com",
});

const subject = await sandbox.create({ template: "base", memMb: 2048 });
try {
  console.log("TypeScript Sandbox.create({ memMb }) succeeded.");
} finally {
  await subject.kill();
}
