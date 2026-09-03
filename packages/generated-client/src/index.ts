import createClient, { type ClientOptions } from "openapi-fetch";

import type { paths } from "./schema.js";

export type { components, operations, paths } from "./schema.js";

/** Create a fetch client whose operations and DTOs come from FastAPI OpenAPI. */
export function createNoxynClient(options: ClientOptions) {
  return createClient<paths>(options);
}
