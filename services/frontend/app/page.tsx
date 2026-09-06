"use client";

import { useEffect } from "react";

// The public demo lives at /demo/. The root path just forwards there so a
// recruiter who opens the site root lands on the demo UI. Client-side redirect
// so it works under static export (no server runtime).
export default function Home() {
  useEffect(() => {
    window.location.replace("/demo/");
  }, []);

  return (
    <main style={{ padding: "1.5rem", fontFamily: "system-ui, sans-serif" }}>
      <p>
        Redirecting to the demo… If nothing happens, open <a href="/demo/">/demo/</a>.
      </p>
    </main>
  );
}
