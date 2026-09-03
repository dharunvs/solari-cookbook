import { NextResponse } from "next/server";

import { e2eCookieName, isE2eAuthBypass } from "@/lib/identity";

export async function POST(request: Request) {
  if (!isE2eAuthBypass())
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  const body = (await request.json()) as { email?: unknown };
  if (typeof body.email !== "string" || !body.email.includes("@"))
    return NextResponse.json(
      { error: "A valid email is required." },
      { status: 422 },
    );
  const response = NextResponse.json({ ok: true });
  const subject = `e2e_${Buffer.from(body.email.trim().toLowerCase()).toString("base64url")}`;
  response.cookies.set(e2eCookieName, subject, {
    httpOnly: true,
    maxAge: 60 * 60,
    path: "/",
    sameSite: "lax",
    secure: false,
  });
  return response;
}
