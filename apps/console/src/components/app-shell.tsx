"use client";

import { UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
  productId: string;
  projectId: string;
  projectName: string;
};

export function AppShell({
  children,
  productId,
  projectId,
  projectName,
}: AppShellProps) {
  const pathname = usePathname();
  const projectHref = `/projects/${projectId}`;
  const runsHref = `${projectHref}/products/${productId}/runs`;
  const projectIsCurrent = pathname === projectHref;
  const runsIsCurrent =
    pathname === runsHref || pathname.startsWith(`${runsHref}/`);

  return (
    <div className="min-h-screen bg-canvas-soft text-ink">
      <header className="border-b border-hairline bg-canvas">
        <div className="mx-auto flex min-h-16 max-w-5xl items-center gap-3 px-4 py-3 sm:px-6">
          <Link
            className="shrink-0 text-sm font-semibold tracking-[-0.02em]"
            href={projectHref}
          >
            NOXYN
          </Link>
          <nav aria-label="Breadcrumb" className="min-w-0 flex-1">
            <ol className="flex min-w-0 items-center gap-1.5 text-sm text-body">
              <li className="truncate">
                <Link
                  aria-current={projectIsCurrent ? "page" : undefined}
                  className="font-medium text-ink"
                  href={projectHref}
                >
                  {projectName}
                </Link>
              </li>
              <li aria-hidden="true">/</li>
              <li className="truncate" aria-current="page">
                Sandbox
              </li>
            </ol>
          </nav>
          <details className="relative sm:hidden">
            <summary className="cursor-pointer rounded-md border border-hairline px-3 py-2 text-sm font-medium">
              Menu
            </summary>
            <nav
              aria-label="Mobile navigation"
              className="absolute right-0 top-[calc(100%+0.5rem)] z-10 w-52 rounded-md border border-hairline bg-canvas p-2 shadow-card"
            >
              <Link
                aria-current={runsIsCurrent ? "page" : undefined}
                className="block rounded-sm px-3 py-2 text-sm font-medium"
                href={runsHref}
              >
                Runs
              </Link>
              <div className="border-t border-hairline px-3 py-2">
                <UserButton />
              </div>
            </nav>
          </details>
          <nav
            aria-label="Product navigation"
            className="hidden items-center gap-1 sm:flex"
          >
            <Link
              aria-current={runsIsCurrent ? "page" : undefined}
              className="rounded-md px-3 py-2 text-sm font-medium"
              href={runsHref}
            >
              Runs
            </Link>
          </nav>
          <div className="hidden shrink-0 sm:block">
            <UserButton />
          </div>
        </div>
      </header>
      <main id="main-content">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">{children}</div>
      </main>
    </div>
  );
}
