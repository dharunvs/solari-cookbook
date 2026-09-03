import { createNoxynClient } from "@noxyn/generated-client";

import type { ApiIdentity } from "@/lib/identity";

const API_BASE_URL = process.env.NOXYN_API_URL ?? "http://127.0.0.1:8000";

export function apiFor(identity: Exclude<ApiIdentity, null>) {
  return createNoxynClient({
    baseUrl: API_BASE_URL,
    headers:
      identity.kind === "clerk"
        ? { Authorization: `Bearer ${identity.token}` }
        : { "X-Noxyn-Test-User": identity.subject },
  });
}

export async function apiError(response: Response) {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? "The request could not be completed.";
  } catch {
    return "The request could not be completed.";
  }
}
