// Controlled aligned fixture for the reviewed TypeScript 0.1.2 spelling.
import { Sandbox } from "@solarisdk/sandbox";

export async function createSandbox() {
  return Sandbox.create({ memMb: 2048 });
}
