// FIXTURE: hand-written to show a passing folder. No model produced it.
// The ONLY place the API address lives. Set VITE_API_URL in web/.env.local.
export const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

export async function getRows () {
  const res = await fetch(`${API_URL}/rows`)
  if (!res.ok) throw new Error(`The API answered ${res.status}`)
  return res.json()
}
