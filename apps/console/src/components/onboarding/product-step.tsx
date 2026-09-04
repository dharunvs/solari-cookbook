import { SubmitButton } from "./submit-button";

export function ProductStep({
  disabled,
  onSubmit,
}: {
  disabled: boolean;
  onSubmit: () => void;
}) {
  return (
    <div>
      <p className="font-mono text-xs text-body">02 / PRODUCT</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em]">
        Choose what to verify first.
      </h1>
      <div className="mt-8 grid gap-3">
        <form
          action={onSubmit}
          className="rounded-lg border border-ink bg-canvas p-5 shadow-card"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Sandbox</h2>
              <p className="mt-1 text-sm text-body">
                Disposable execution environments for reproducible evidence.
              </p>
            </div>
            <span className="rounded-full bg-success-soft px-2 py-1 text-xs text-success-deep">
              Available
            </span>
          </div>
          <div className="mt-5">
            <SubmitButton disabled={disabled}>Add Sandbox</SubmitButton>
          </div>
        </form>
        {["Browser", "Desktop"].map((product) => (
          <article
            className="rounded-lg border border-hairline bg-canvas-soft p-5 opacity-70"
            key={product}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold">{product}</h2>
                <p className="mt-1 text-sm text-body">
                  Informational for this MVP.
                </p>
              </div>
              <button
                aria-disabled="true"
                className="cursor-not-allowed rounded-md border border-hairline px-3 py-2 text-xs"
                disabled
                type="button"
              >
                Coming later
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
