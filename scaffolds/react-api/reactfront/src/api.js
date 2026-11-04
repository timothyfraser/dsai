// The ONLY place the API address lives.
//
// Set VITE_API_URL in a .env.local file (or in the build environment) to point
// at your deployed API. With no value, the page calls "/api", which the Vite
// dev proxy forwards to the local API (see vite.config.js), so local work
// needs no CORS at all.
//
// WARNING: anything named VITE_ is printed into the public JavaScript that
// every visitor downloads. The address of your API is fine there. A key, a
// token or a password is never fine there. The API holds the key; this page
// never does.
export const API_URL = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

async function getJson(path, options) {
  const res = await fetch(`${API_URL}${path}`, options)
  if (!res.ok) throw new Error(`${path} returned HTTP ${res.status}`)
  return res.json()
}

/** GET /health. Returns {"status": "ok", "version": "..."}. */
export function checkApi() {
  return getJson('/health')
}

/** POST /summary with {"values": [...]}. Returns {n, mean, min, max}. */
export function summarizeOnServer(values) {
  return getJson('/summary', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ values }),
  })
}

/** Parse "10.1, 9.8 10.3" into numbers; ignores blanks, rejects junk. */
export function parseValues(text) {
  const parts = text.split(/[\s,;]+/).filter(Boolean)
  const nums = parts.map(Number)
  if (nums.length === 0) throw new Error('Enter at least one number')
  if (nums.some((n) => !Number.isFinite(n))) throw new Error('Every value must be a number')
  return nums
}
