"use client";

import {
  type MouseEvent,
  type ReactNode,
  type RefObject,
  useEffect,
  useId,
  useRef,
} from "react";

type DialogProps = {
  children: ReactNode;
  /** A visible heading that gives the dialog its accessible name. */
  title: string;
  /** Optional supporting text announced with the dialog. */
  description?: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Focus this element after the dialog opens. */
  initialFocusRef?: RefObject<HTMLElement | null>;
  /** Destructive confirmations can only be closed through an explicit action. */
  destructive?: boolean;
  /** Allows a dismissible overlay to close when its backdrop is clicked. */
  closeOnBackdrop?: boolean;
  /** Allows a dismissible overlay to close when Escape is pressed. */
  closeOnEscape?: boolean;
  className?: string;
};

let scrollLockCount = 0;
let previousBodyOverflow = "";

function lockScroll() {
  if (scrollLockCount++ === 0) {
    previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
  }
}

function unlockScroll() {
  scrollLockCount = Math.max(0, scrollLockCount - 1);
  if (scrollLockCount === 0) {
    document.body.style.overflow = previousBodyOverflow;
  }
}

/**
 * A controlled, modal native dialog. Native `showModal()` supplies the modal
 * top layer, inert background, and keyboard focus containment.
 */
export function Dialog({
  children,
  title,
  description,
  open,
  onOpenChange,
  initialFocusRef,
  destructive = false,
  closeOnBackdrop = true,
  closeOnEscape = true,
  className,
}: DialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const openerRef = useRef<HTMLElement | null>(null);
  const titleId = useId();
  const descriptionId = useId();
  const canDismiss = !destructive;
  const allowBackdrop = canDismiss && closeOnBackdrop;
  const allowEscape = canDismiss && closeOnEscape;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open) {
      openerRef.current = document.activeElement as HTMLElement | null;
      if (!dialog.open) dialog.showModal();
      lockScroll();
      queueMicrotask(() => initialFocusRef?.current?.focus());
      return () => {
        if (dialog.open) dialog.close();
        unlockScroll();
      };
    }

    if (dialog.open) dialog.close();
  }, [initialFocusRef, open]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    function restoreFocus() {
      openerRef.current?.focus();
    }

    function handleCancel(event: Event) {
      event.preventDefault();
      if (allowEscape) onOpenChange(false);
    }

    function handleClose() {
      restoreFocus();
    }

    dialog.addEventListener("cancel", handleCancel);
    dialog.addEventListener("close", handleClose);
    return () => {
      dialog.removeEventListener("cancel", handleCancel);
      dialog.removeEventListener("close", handleClose);
    };
  }, [allowEscape, onOpenChange]);

  function handleBackdropClick(event: MouseEvent<HTMLDialogElement>) {
    if (allowBackdrop && event.target === event.currentTarget) {
      onOpenChange(false);
    }
  }

  return (
    <dialog
      aria-describedby={description ? descriptionId : undefined}
      aria-labelledby={titleId}
      aria-modal="true"
      className="noxyn-overlay"
      onClick={handleBackdropClick}
      ref={dialogRef}
    >
      <div className={`noxyn-dialog ${className ?? ""}`}>
        <div className="noxyn-dialog__header">
          <h2
            className="text-pretty text-xl font-semibold tracking-tight"
            id={titleId}
          >
            {title}
          </h2>
          {description ? (
            <p className="mt-2 text-sm text-body" id={descriptionId}>
              {description}
            </p>
          ) : null}
        </div>
        {children}
      </div>
    </dialog>
  );
}
