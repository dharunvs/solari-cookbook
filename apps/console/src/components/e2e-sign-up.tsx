"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function E2ESignUp({ returnTo = "/" }: { returnTo?: string }) {
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  async function register(formData: FormData) {
    setError(null);
    const response = await fetch("/api/e2e/sign-up", {
      body: JSON.stringify({ email: formData.get("email") }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    if (!response.ok) {
      setError("Unable to create the test session.");
      return;
    }
    router.push(returnTo);
    router.refresh();
  }
  return (
    <form action={register} className="mt-7 space-y-4" noValidate>
      <div>
        <label className="text-sm font-medium" htmlFor="email">
          Work email
        </label>
        <input
          autoComplete="email"
          className="mt-2 w-full rounded-md border border-hairline bg-canvas px-3 py-2 text-sm"
          defaultValue="builder@example.com"
          id="email"
          name="email"
          required
          spellCheck={false}
          type="email"
        />
      </div>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <button
        className="w-full rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white"
        type="submit"
      >
        Create private workspace
      </button>
      <p className="text-xs leading-5 text-body">
        Local Playwright mode only. Production uses Clerk sign-up and email
        verification.
      </p>
    </form>
  );
}
