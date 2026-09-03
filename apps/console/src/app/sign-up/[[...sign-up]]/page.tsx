import { SignUp } from "@clerk/nextjs";

import { E2ESignUp } from "@/components/e2e-sign-up";
import { isE2eAuthBypass } from "@/lib/identity";

export default function SignUpPage() {
  return (
    <main
      className="grid min-h-screen place-items-center bg-canvas-soft px-4"
      id="main-content"
    >
      <section className="w-full max-w-md rounded-xl border border-hairline bg-canvas p-7 shadow-card">
        <p className="font-mono text-xs text-body">NOXYN / SOLARI</p>
        <h1 className="mt-3 text-2xl font-semibold tracking-[-0.04em]">
          Create your private workspace
        </h1>
        {isE2eAuthBypass() ? (
          <E2ESignUp />
        ) : (
          <div className="mt-7">
            <SignUp
              forceRedirectUrl="/"
              routing="path"
              path="/sign-up"
              signInUrl="/sign-in"
            />
          </div>
        )}
      </section>
    </main>
  );
}
