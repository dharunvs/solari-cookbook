"use client";

import { useEffect, useRef, useState } from "react";

import { SubmitButton } from "./submit-button";

export function ProjectStep({
  disabled,
  onDraftChange,
  onSubmit,
  projectName: initialProjectName,
  projectSlug: initialProjectSlug,
}: {
  disabled: boolean;
  onDraftChange: (projectName: string, projectSlug: string) => void;
  onSubmit: (formData: FormData) => void;
  projectName?: string | null;
  projectSlug?: string | null;
}) {
  const [projectName, setProjectName] = useState(
    initialProjectName ?? "Solari",
  );
  const [projectSlug, setProjectSlug] = useState(
    initialProjectSlug ?? "solari",
  );
  const hasEdited = useRef(false);

  useEffect(() => {
    if (!hasEdited.current || disabled) return;
    const timeout = window.setTimeout(
      () => onDraftChange(projectName, projectSlug),
      350,
    );
    return () => window.clearTimeout(timeout);
  }, [disabled, onDraftChange, projectName, projectSlug]);

  return (
    <form action={onSubmit} className="space-y-5">
      <div>
        <p className="font-mono text-xs text-body">01 / PROJECT</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em]">
          Start with Solari.
        </h1>
        <p className="mt-3 text-body">
          Create the private project that Noxyn will verify.
        </p>
      </div>
      <label className="block text-sm font-medium">
        Project name
        <input
          autoComplete="off"
          className="mt-2 w-full rounded-md border border-hairline bg-canvas px-3 py-2"
          disabled={disabled}
          name="projectName"
          onChange={(event) => {
            hasEdited.current = true;
            setProjectName(event.target.value);
          }}
          required
          value={projectName}
        />
      </label>
      <label className="block text-sm font-medium">
        Project slug
        <input
          autoComplete="off"
          className="mt-2 w-full rounded-md border border-hairline bg-canvas px-3 py-2 font-mono"
          disabled={disabled}
          name="projectSlug"
          onChange={(event) => {
            hasEdited.current = true;
            setProjectSlug(event.target.value);
          }}
          pattern="[a-z0-9]+(-[a-z0-9]+)*"
          required
          spellCheck={false}
          value={projectSlug}
        />
      </label>
      <SubmitButton disabled={disabled}>Create project</SubmitButton>
    </form>
  );
}
