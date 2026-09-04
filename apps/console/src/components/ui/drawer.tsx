"use client";

import type { ReactNode, RefObject } from "react";

import { Dialog } from "./dialog";

type DrawerProps = {
  children: ReactNode;
  title: string;
  description?: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialFocusRef?: RefObject<HTMLElement | null>;
  destructive?: boolean;
  closeOnBackdrop?: boolean;
  closeOnEscape?: boolean;
  className?: string;
};

/**
 * A responsive dialog: full-viewport sheet on mobile, right-side drawer from
 * the `sm` breakpoint upward. It shares Dialog's native modal behavior.
 */
export function Drawer(props: DrawerProps) {
  return (
    <Dialog
      {...props}
      className={`noxyn-drawer ${props.className ?? ""}`}
    />
  );
}
