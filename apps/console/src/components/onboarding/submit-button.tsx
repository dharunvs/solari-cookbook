export function SubmitButton({
  children,
  disabled = false,
}: {
  children: string;
  disabled?: boolean;
}) {
  return (
    <button
      className="rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white disabled:cursor-wait disabled:opacity-60"
      disabled={disabled}
      type="submit"
    >
      {children}
    </button>
  );
}
