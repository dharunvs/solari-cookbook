"use client";

export default function RunError({ retry }: { retry: () => void }) {
  return (
    <main className="grid min-h-screen place-items-center bg-canvas-soft p-6 text-ink">
      <section className="w-full max-w-lg rounded-lg border border-hairline bg-canvas p-6 shadow-card">
        <p className="font-mono text-xs text-body">VERIFICATION EVIDENCE</p>
        <h1 className="mt-3 text-xl font-semibold">Evidence is unavailable.</h1>
        <p className="mt-3 text-sm leading-6 text-body">
          Noxyn could not complete the authorized evidence read. The run and
          stored artifacts have not been changed.
        </p>
        <button
          className="mt-6 rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white"
          onClick={retry}
          type="button"
        >
          Try again
        </button>
      </section>
    </main>
  );
}
