// api.js
// The contract between this page and your team's API, in one file.
// Course kit, module 12

// The page never calls fetch() anywhere else. If the API changes, this is the only file to change.
// It keeps Module 10's contract exactly: POST {"question": "..."}, reply {"answer": "...", "source": "..."}.

// 0. SETUP ###################################

// The API address comes from VITE_API_URL, an environment variable read when the page is built.
// Vite only passes variables whose names start with VITE_ to the page, so a key never leaks by accident.
//   VITE_API_URL=https://your-team-api.example.org/ask npm run dev
// Never put a key in a VITE_ variable: everything here ends up in a file anyone can download.
export const API_URL = import.meta.env.VITE_API_URL || "";

// How long to wait for the API, in milliseconds. Too short and a slow API is never used;
// too long and the reader stares at "Asking..." with no way out.
export const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS) || 8000;

// 1. ASK THE API, WITH A TIMEOUT ###################################

// The reply is always one of two shapes, so the page has exactly two cases to draw:
//   { ok: true,  answer: "...", source: "..." or null }
//   { ok: false, why: "one plain sentence" }
// Every way this can fail becomes one plain sentence, because the reader cannot read an error code.
export async function askApi(question) {
  if (!API_URL) return { ok: false, why: "this page has no API address (set VITE_API_URL and build again)" };
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), API_TIMEOUT_MS);
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question }),
      signal: ctrl.signal,
    });
    if (!res.ok) return { ok: false, why: "the server answered with an error (HTTP " + res.status + ")" };
    const body = await res.json().catch(() => null);
    if (!body || typeof body.answer !== "string") return { ok: false, why: "the server's reply had no answer in it" };
    // An answer with no source is still shown, but the page says so: the source is what earns trust.
    return { ok: true, answer: body.answer, source: typeof body.source === "string" && body.source ? body.source : null };
  } catch (err) {
    if (err.name === "AbortError") return { ok: false, why: "the server took longer than " + API_TIMEOUT_MS / 1000 + " s" };
    return { ok: false, why: "the server could not be reached (" + (navigator.onLine ? "it may be down" : "this device is offline") + ")" };
  } finally {
    clearTimeout(timer);
  }
}
