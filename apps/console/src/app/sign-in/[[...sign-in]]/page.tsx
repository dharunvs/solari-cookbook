import { SignIn } from "@clerk/nextjs";
import Link from "next/link";

import { E2ESignUp } from "@/components/e2e-sign-up";
import { isE2eAuthBypass, safeReturnPath } from "@/lib/identity";

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ returnTo?: string }>;
}) {
  const e2e = isE2eAuthBypass();
  const returnTo = safeReturnPath((await searchParams).returnTo) ?? "/";
  return (
    <main
      className="grid min-h-screen place-items-center bg-canvas-soft px-4"
      id="main-content"
    >
      <section className="w-full max-w-md rounded-xl border border-hairline bg-canvas p-7 shadow-card">
        <p className="font-mono text-xs text-body">NOXYN / SOLARI</p>
        <h1 className="mt-3 text-2xl font-semibold tracking-[-0.04em]">
          Sign in to your workspace
        </h1>
        {e2e ? (
          <E2ESignUp returnTo={returnTo} />
        ) : (
          <>
            <div className="mt-7">
              <SignIn
                forceRedirectUrl={returnTo}
                routing="path"
                path="/sign-in"
                signUpUrl="/sign-up"
              />
            </div>
            <p className="mt-4 text-sm text-body">
              New here?{" "}
              <Link className="font-medium text-ink underline" href="/sign-up">
                Create an account
              </Link>
            </p>
          </>
        )}
      </section>
    </main>
  );
}
