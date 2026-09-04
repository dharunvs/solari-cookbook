import { SubmitButton } from "./submit-button";

const sources = [
  "Cookbook examples",
  "Documentation snippets",
  "Published SDK packages",
];

export function ConfigurationStep({
  disabled,
  onSubmit,
}: {
  disabled: boolean;
  onSubmit: (formData: FormData) => void;
}) {
  return (
    <form action={onSubmit} className="space-y-6">
      <div>
        <p className="font-mono text-xs text-body">03 / CONFIGURATION</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em]">
          Configure Sandbox verification.
        </h1>
        <p className="mt-3 text-body">
          This saves an immutable configuration v1. No Solari credential is
          requested here.
        </p>
      </div>
      <fieldset disabled={disabled}>
        <legend className="text-sm font-medium">Sources to verify</legend>
        <div className="mt-3 grid gap-2">
          {sources.map((source) => (
            <label
              className="flex items-center gap-3 rounded-md border border-hairline bg-canvas p-3 text-sm"
              key={source}
            >
              <input
                defaultChecked
                name="sources"
                type="checkbox"
                value={source.toLowerCase().replaceAll(" ", "-")}
              />
              {source}
            </label>
          ))}
        </div>
      </fieldset>
      <div className="rounded-lg border border-hairline bg-canvas-soft p-4">
        <p className="font-mono text-xs text-body">READINESS CHECK</p>
        <ul className="mt-3 space-y-2 text-sm">
          <li>✓ Solari project selected</li>
          <li>✓ Sandbox product selected</li>
          <li>✓ Python, TypeScript, and Go identities pinned</li>
        </ul>
      </div>
      <SubmitButton disabled={disabled}>Save configuration v1</SubmitButton>
    </form>
  );
}
