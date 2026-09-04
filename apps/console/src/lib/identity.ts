import { auth } from "@clerk/nextjs/server";
import { cookies } from "next/headers";

const E2E_COOKIE = "noxyn_e2e_user";

export type ApiIdentity =
  | { kind: "clerk"; token: string }
  | { kind: "e2e"; subject: string }
  | null;

export function isE2eAuthBypass() {
  return (
    process.env.NOXYN_E2E_AUTH_BYPASS === "true" &&
    process.env.NODE_ENV !== "production"
  );
}

export async function getApiIdentity(): Promise<ApiIdentity> {
  if (isE2eAuthBypass()) {
    const subject = (await cookies()).get(E2E_COOKIE)?.value;
    return subject?.startsWith("e2e_") ? { kind: "e2e", subject } : null;
  }
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) return null;
  const session = await auth();
  if (!session.userId) return null;
  const token = await session.getToken();
  return token ? { kind: "clerk", token } : null;
}

export const e2eCookieName = E2E_COOKIE;

export function safeReturnPath(value: string | null | undefined) {
  if (
    !value ||
    !value.startsWith("/") ||
    value.startsWith("//") ||
    /[\\\u0000-\u001f]/.test(value)
  )
    return null;
  try {
    const url = new URL(value, "http://noxyn.local");
    return url.origin === "http://noxyn.local"
      ? `${url.pathname}${url.search}${url.hash}`
      : null;
  } catch {
    return null;
  }
}
