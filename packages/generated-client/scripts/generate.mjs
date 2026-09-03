import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

import openapiTS, { astToString } from "openapi-typescript";
import { format } from "prettier";

const packageRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
const repositoryRoot = path.resolve(packageRoot, "../..");
const source = path.join(repositoryRoot, "services/api/openapi.json");
const destination = path.join(packageRoot, "src/schema.ts");
const check = process.argv.includes("--check");

const ast = await openapiTS(pathToFileURL(source));
const generated = await format(astToString(ast), { parser: "typescript" });

let existing = null;
try {
  existing = await readFile(destination, "utf8");
} catch (error) {
  if (error.code !== "ENOENT") throw error;
}

if (check && existing !== generated) {
  throw new Error(
    "packages/generated-client/src/schema.ts is stale; run pnpm client:generate",
  );
}
if (!check) {
  await writeFile(destination, generated);
}
