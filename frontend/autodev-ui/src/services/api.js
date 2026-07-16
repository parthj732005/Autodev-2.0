const BASE = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const api = {
  // Server/machine-scoped only (output_directory) — no credentials here anymore.
  getSettings: () => request("/settings/"),
  getProviders: () => request("/settings/providers"),
  saveSettings: (data) =>
    request("/settings/", { method: "POST", body: JSON.stringify(data) }),

  // Project browsing is now ownership-scoped — every call requires the
  // caller's JWT so FastAPI can verify ownership via the platform service.
  getGeneratedProjects: (token) =>
    request("/projects/generated", { headers: authHeaders(token) }),
  getGeneratedProject: (name, token) =>
    request(`/projects/generated/${name}`, { headers: authHeaders(token) }),
  openInVSCode: (name, token) =>
    request(`/projects/generated/${name}/open-vscode`, {
      method: "POST",
      headers: authHeaders(token),
    }),
  getSetupInstructions: (name, token) =>
    request(`/projects/generated/${name}/setup-instructions`, {
      method: "POST",
      headers: authHeaders(token),
    }),
};
