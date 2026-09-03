import { clerkMiddleware } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const bypass =
  process.env.NOXYN_E2E_AUTH_BYPASS === "true" &&
  process.env.NODE_ENV !== "production";
const clerk = clerkMiddleware(async (auth, request) => {
  const path = request.nextUrl.pathname;
  const publicRoute =
    path === "/sign-in" ||
    path.startsWith("/sign-in/") ||
    path === "/sign-up" ||
    path.startsWith("/sign-up/") ||
    path.startsWith("/__clerk/");

  if (!publicRoute) await auth.protect();
});

export default bypass ? () => NextResponse.next() : clerk;

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico)).*)",
    "/(api|trpc)(.*)",
  ],
};
