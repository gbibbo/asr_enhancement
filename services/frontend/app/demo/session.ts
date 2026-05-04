// X-Demo-Session-Id helper. The backend (B10.2) requires this header on
// AssemblyAI uploads and uses a SHA-256 hash of it to enforce a 3-uses-per-24h
// rate limit. The plain value never leaves the browser except in that single
// header on AssemblyAI uploads. We never render or log the value.

const STORAGE_KEY = "demo_session_id";

function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof window.crypto !== "undefined";
}

function generateId(): string {
  // crypto.randomUUID exists in modern browsers (Next.js 14 target).
  if (isBrowser() && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  // Fallback: 16 random bytes hex. Never reached on supported browsers.
  const bytes = new Uint8Array(16);
  if (isBrowser() && typeof window.crypto.getRandomValues === "function") {
    window.crypto.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i += 1) bytes[i] = Math.floor(Math.random() * 256);
  }
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

export function getOrCreateDemoSessionId(): string {
  if (!isBrowser()) {
    return generateId();
  }
  try {
    const existing = window.localStorage.getItem(STORAGE_KEY);
    if (existing && existing.length > 0) {
      return existing;
    }
    const fresh = generateId();
    window.localStorage.setItem(STORAGE_KEY, fresh);
    return fresh;
  } catch {
    // localStorage unavailable (private mode, quota, etc.) — fall back to a
    // per-page-load id. The 24h ledger gate then resets on each reload.
    return generateId();
  }
}
