import { SandboxClient } from "@solarisdk/sandbox";

const sandbox = new SandboxClient({ apiKey: process.env.SOLARI_API_KEY });
await sandbox.create({ template: "base", memMb: 2048 });
