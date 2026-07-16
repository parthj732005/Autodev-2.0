// Isolated client for the Java/Spring Boot platform service (auth only).
// This is the only module that knows the platform service's base URL or
// endpoint shapes — everything else in the app that needs auth goes
// through AuthContext.
const PLATFORM_BASE = "http://localhost:8081";

async function request(path, options = {}) {
  const res = await fetch(`${PLATFORM_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  // 204 No Content has no body to parse
  if (res.status === 204) return null;
  return res.json();
}

export const authApi = {
  register: (email, password) =>
    request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email, password) =>
    request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: (token) =>
    request("/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    }),
};
