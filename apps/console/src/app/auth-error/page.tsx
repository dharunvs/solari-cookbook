import { SignOutButton } from "@clerk/nextjs";

export default function AuthenticationRecoveryPage() {
  return (
    <main
      className="grid min-h-screen place-items-center bg-canvas-soft px-4 text-ink"
      id="main-content"
    >
      <section className="w-full max-w-lg rounded-xl border border-hairline bg-canvas p-7 shadow-card">
        <p className="font-mono text-xs text-body">NOXYN / AUTHENTICATION</p>
        <h1 className="mt-3 text-2xl font-semibold tracking-[-0.04em]">
          Your session needs to be renewed.
        </h1>
        <p className="mt-3 text-sm leading-6 text-body">
          Clerk still recognizes this browser session, but Noxyn could not
          verify it with the API. Sign out, then sign in again to continue.
        </p>
        <SignOutButton redirectUrl="/sign-in">
          <button
            className="mt-6 rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white"
            type="button"
          >
            Sign out and try again
          </button>
        </SignOutButton>
      </section>
    </main>
  );
}
