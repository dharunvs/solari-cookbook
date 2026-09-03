import { createNoxynClient, type components } from "@noxyn/generated-client";

export type ApiHealth = components["schemas"]["HealthResponse"];

export type FoundationHealth =
  | { state: "ready"; health: ApiHealth }
  | { state: "unavailable" };

export async function getFoundationHealth(): Promise<FoundationHealth> {
  const client = createNoxynClient({
    baseUrl: process.env.NOXYN_API_BASE_URL ?? "http://127.0.0.1:8000",
  });

  try {
    const { data, response } = await client.GET("/health", {
      cache: "no-store",
    });
    if (!response.ok || !data) return { state: "unavailable" };
    return { state: "ready", health: data };
  } catch {
    return { state: "unavailable" };
  }
}
