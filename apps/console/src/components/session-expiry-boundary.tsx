"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { useBrowserSessionExpired } from "@/lib/browser-api";
import { safeReturnPath } from "@/lib/identity";

function currentPath() {
  if (typeof window === "undefined") return null;
  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
}

function SessionExpiredRecovery() {
  const returnTo = safeReturnPath(currentPath());
  const href = returnTo
    ? `/sign-in?returnTo=${encodeURIComponent(returnTo)}`
    : "/sign-in";

  return (
    <main
      className="grid min-h-[calc(100vh-4rem)] place-items-center px-4 py-10"
      id="main-content"
    >
      <section
        aria-live="polite"
        className="w-full max-w-lg rounded-xl border border-hairline bg-canvas p-6 shadow-card sm:p-7"
      >
        <p className="font-mono text-xs text-body">NOXYN / AUTHENTICATION</p>
        <h1 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-balance">
          Your session has expired.
        </h1>
        <p className="mt-3 text-sm leading-6 text-body">
          Sign in again to continue. Any verification already running continues
          in the background.
        </p>
        <Link
          className="mt-6 inline-flex rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white"
          href={href}
        >
          Sign In
        </Link>
      </section>
    </main>
  );
}

export function SessionExpiryBoundary({ children }: { children: ReactNode }) {
  return useBrowserSessionExpired() ? <SessionExpiredRecovery /> : children;
}
