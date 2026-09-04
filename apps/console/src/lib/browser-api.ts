"use client";

import { useSyncExternalStore } from "react";

const SESSION_EXPIRED_EVENT = "noxyn:session-expired";

let sessionExpired = false;

export class SessionExpiredError extends Error {
  constructor() {
    super("Your session has expired.");
    this.name = "SessionExpiredError";
  }
}

export function isUnauthorized(response: Response) {
  return response.status === 401;
}

export function hasBrowserSessionExpired() {
  return sessionExpired;
}

function expireBrowserSession() {
  if (sessionExpired) return;
  sessionExpired = true;
  if (typeof window !== "undefined")
    window.dispatchEvent(new window.Event(SESSION_EXPIRED_EVENT));
}

export async function browserApi(
  input: RequestInfo | URL,
  init?: RequestInit,
) {
  if (sessionExpired) throw new SessionExpiredError();
  const response = await fetch(input, init);
  if (isUnauthorized(response)) {
    expireBrowserSession();
    throw new SessionExpiredError();
  }
  return response;
}

function subscribe(onStoreChange: () => void) {
  window.addEventListener(SESSION_EXPIRED_EVENT, onStoreChange);
  return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onStoreChange);
}

export function useBrowserSessionExpired() {
  return useSyncExternalStore(subscribe, hasBrowserSessionExpired, () => false);
}

export function resetBrowserSessionExpiryForTests() {
  sessionExpired = false;
}
