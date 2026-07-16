// Isolated client for the platform service's per-user provider settings.
// Mirrors authApi.js's pattern — this is the only module that knows these
// endpoint shapes. Never returns/sends a full API key except the one the
// user just typed in (for saving); GET responses are always masked.
const PLATFORM_BASE = "http://localhost:8081";

async function request(path, token, options = {}) {
  const res = await fetch(`${PLATFORM_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export const settingsApi = {
  get: (token) => request("/api/settings", token),
  update: (token, partialUpdate) =>
    request("/api/settings", token, {
      method: "POST",
      body: JSON.stringify(partialUpdate),
    }),
};
