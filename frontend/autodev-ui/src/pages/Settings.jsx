import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import { settingsApi } from "../services/settingsApi";

const PROVIDERS = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "groq", label: "Groq (Free)" },
  { value: "huggingface", label: "HuggingFace" },
  { value: "ollama", label: "Ollama (Local • Slow on CPU)" },
];

// Maps a provider value to its field names in the platform-service response/update payload.
const FIELD_NAMES = {
  openai: { model: "openaiModel", configured: "openaiApiKeyConfigured", suffix: "openaiApiKeySuffix", keyField: "openaiApiKey" },
  anthropic: { model: "anthropicModel", configured: "anthropicApiKeyConfigured", suffix: "anthropicApiKeySuffix", keyField: "anthropicApiKey" },
  groq: { model: "groqModel", configured: "groqApiKeyConfigured", suffix: "groqApiKeySuffix", keyField: "groqApiKey" },
  huggingface: { model: "huggingfaceModel", configured: "huggingfaceApiKeyConfigured", suffix: "huggingfaceApiKeySuffix", keyField: "huggingfaceApiKey" },
};

export default function Settings() {
  const { token } = useAuth();
  const [providerSettings, setProviderSettings] = useState(null);
  const [outputDirectory, setOutputDirectory] = useState(null);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [modelDrafts, setModelDrafts] = useState({});
  const [keyInputs, setKeyInputs] = useState({}); // new plaintext keys typed this session only
  const [ollamaBaseUrlDraft, setOllamaBaseUrlDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    Promise.all([settingsApi.get(token), api.getSettings()])
      .then(([provider, server]) => {
        setProviderSettings(provider);
        setSelectedProvider(provider.selectedProvider);
        setOllamaBaseUrlDraft(provider.ollamaBaseUrl || "");
        setOutputDirectory(server.output_directory || "");
        setModelDrafts({
          openai: provider.openaiModel || "",
          anthropic: provider.anthropicModel || "",
          groq: provider.groqModel || "",
          huggingface: provider.huggingfaceModel || "",
          ollama: provider.ollamaModel || "",
        });
      })
      .catch((e) => setError(e.message));
  }, [token]);

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const update = { selectedProvider };
      for (const p of ["openai", "anthropic", "groq", "huggingface"]) {
        const f = FIELD_NAMES[p];
        update[f.model] = modelDrafts[p] || null;
        // Omit the key field entirely unless the user actually typed a new one —
        // that preserves the existing stored (encrypted) key server-side.
        if (keyInputs[p]) {
          update[f.keyField] = keyInputs[p];
        }
      }
      update.ollamaModel = modelDrafts.ollama || null;
      update.ollamaBaseUrl = ollamaBaseUrlDraft || null;

      const [updatedProvider] = await Promise.all([
        settingsApi.update(token, update),
        api.saveSettings({ output_directory: outputDirectory }),
      ]);

      setProviderSettings(updatedProvider);
      setKeyInputs({}); // never keep typed plaintext keys around after a successful save
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  function setModel(provider, value) {
    setModelDrafts((prev) => ({ ...prev, [provider]: value }));
  }

  function setKeyInput(provider, value) {
    setKeyInputs((prev) => ({ ...prev, [provider]: value }));
  }

  if (!providerSettings || outputDirectory === null) {
    return (
      <div className="p-8 space-y-3 max-w-lg">
        {error ? (
          <>
            <p className="text-danger font-medium">Could not reach backend</p>
            <p className="text-slate-500 text-sm">{error}</p>
            <div className="card bg-warning/5 border-warning/20 text-xs text-slate-400 space-y-1">
              <p className="text-warning font-semibold mb-2">Start the backend and platform service first:</p>
              <p className="font-mono">cd backend</p>
              <p className="font-mono">uvicorn app.main:app --reload</p>
              <p className="font-mono">docker compose up platform-service postgres</p>
            </div>
          </>
        ) : (
          <p className="text-slate-500 text-sm">Loading settings...</p>
        )}
      </div>
    );
  }

  function keyStatusLabel(provider) {
    const f = FIELD_NAMES[provider];
    if (keyInputs[provider]) return "New key entered — will replace on save";
    if (providerSettings[f.configured]) return `Configured (ends in ${providerSettings[f.suffix]})`;
    return "Not configured";
  }

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-xl font-bold text-slate-100 mb-1">Settings</h1>
      <p className="text-sm text-slate-500 mb-6">
        Configure your AI provider and output directory. Provider credentials are yours alone —
        encrypted at rest and never shared with other accounts.
      </p>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Provider */}
        <div className="card space-y-4">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
            AI Provider
          </h2>
          <div className="flex gap-3">
            {PROVIDERS.map((p) => (
              <button
                key={p.value}
                type="button"
                onClick={() => setSelectedProvider(p.value)}
                className={`flex-1 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
                  selectedProvider === p.value
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-slate-400 hover:border-slate-500"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {selectedProvider === "openai" && (
            <div className="space-y-3">
              <label className="block">
                <span className="text-xs text-slate-500 mb-1 block">OpenAI API Key</span>
                <input
                  type="password"
                  className="input"
                  value={keyInputs.openai || ""}
                  onChange={(e) => setKeyInput("openai", e.target.value)}
                  placeholder="sk-..."
                />
                <span className="text-xs text-slate-600 mt-1 block">{keyStatusLabel("openai")}</span>
              </label>
              <label className="block">
                <span className="text-xs text-slate-500 mb-1 block">Model</span>
                <select
                  className="input"
                  value={modelDrafts.openai || "gpt-5.4-mini"}
                  onChange={(e) => setModel("openai", e.target.value)}
                >
                  <option value="gpt-5.4-mini">gpt-5.4-mini (recommended)</option>
                  <option value="gpt-5.5">gpt-5.5</option>
                  <option value="gpt-5.4">gpt-5.4</option>
                </select>
              </label>
            </div>
          )}

          {selectedProvider === "anthropic" && (
            <div className="space-y-3">
              <label className="block">
                <span className="text-xs text-slate-500 mb-1 block">Anthropic API Key</span>
                <input
                  type="password"
                  className="input"
                  value={keyInputs.anthropic || ""}
                  onChange={(e) => setKeyInput("anthropic", e.target.value)}
                  placeholder="sk-ant-..."
                />
                <span className="text-xs text-slate-600 mt-1 block">{keyStatusLabel("anthropic")}</span>
              </label>
              <label className="block">
                <span className="text-xs text-slate-500 mb-1 block">Model</span>
                <select
                  className="input"
                  value={modelDrafts.anthropic || "claude-sonnet-5"}
                  onChange={(e) => setModel("anthropic", e.target.value)}
                >
                  <option value="claude-sonnet-5">claude-sonnet-5 (recommended)</option>
                  <option value="claude-opus-4-8">claude-opus-4-8</option>
                  <option value="claude-haiku-4-5">claude-haiku-4-5</option>
                </select>
              </label>
            </div>
          )}

          {selectedProvider === "groq" && (
            <div className="space-y-3">
              <div className="text-xs text-success bg-success/10 border border-success/20 rounded-lg px-3 py-2">
                Groq is free and very fast. Get your key at{" "}
                <span className="font-mono">console.groq.com</span>
              </div>
              <label className="block">
                <span className="text-xs text-slate-500 mb-1 block">Groq API Key</span>
                <input
                  type="password"
                  className="input"
                  value={keyInputs.groq || ""}
                  onChange={(e) => setKeyInput("groq", e.target.value)}
                  placeholder="gsk_..."
                />
                <span className="text-xs text-slate-600 mt-1 block">{keyStatusLabel("groq")}</span>
              </label>
              <label className="block">
                <span className="text-xs text-slate-500 mb-1 block">Model</span>
                <select
                  className="input"
                  value={modelDrafts.groq || "llama-3.3-70b-versatile"}
                  onChange={(e) => setModel("groq", e.target.value)}
                >
                  <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile (recommended)</option>
                  <option value="openai/gpt-oss-120b">openai/gpt-oss-120b</option>
                  <option value="openai/gpt-oss-20b">openai/gpt-oss-20b</option>
                  <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                </select>
              </label>
            </div>
          )}

          {selectedProvider === "huggingface" && (
            <div className="space-y-3">
              <div className="text-xs text-primary bg-primary/10 border border-primary/20 rounded-lg px-3 py-2">
                Uses the HuggingFace Inference Router. Get your key at{" "}
                <span className="font-mono">huggingface.co/settings/tokens</span>
              </div>
              <label className="block">
                <span className="text-xs text-slate-500 mb-1 block">HuggingFace API Key</span>
                <input
                  type="password"
                  className="input"
                  value={keyInputs.huggingface || ""}
                  onChange={(e) => setKeyInput("huggingface", e.target.value)}
                  placeholder="hf_..."
                />
                <span className="text-xs text-slate-600 mt-1 block">{keyStatusLabel("huggingface")}</span>
              </label>
              <label className="block">
                <span className="text-xs text-slate-500 mb-1 block">Model</span>
                <select
                  className="input"
                  value={modelDrafts.huggingface || "Qwen/Qwen3-Coder-30B-A3B-Instruct"}
                  onChange={(e) => setModel("huggingface", e.target.value)}
                >
                  <option value="Qwen/Qwen3-Coder-30B-A3B-Instruct">Qwen3-Coder-30B-A3B-Instruct (recommended)</option>
                  <option value="Qwen/Qwen2.5-Coder-32B-Instruct">Qwen2.5-Coder-32B-Instruct</option>
                  <option value="meta-llama/Llama-3.3-70B-Instruct">Llama-3.3-70B-Instruct</option>
                </select>
              </label>
            </div>
          )}

          {selectedProvider === "ollama" && (
            <div className="space-y-3">
              <label className="block">
                <span className="text-xs text-slate-500 mb-1 block">Ollama Base URL</span>
                <input
                  className="input"
                  value={ollamaBaseUrlDraft}
                  onChange={(e) => setOllamaBaseUrlDraft(e.target.value)}
                  placeholder="http://localhost:11434"
                />
              </label>
              <label className="block">
                <span className="text-xs text-slate-500 mb-1 block">Model</span>
                <input
                  className="input"
                  value={modelDrafts.ollama || ""}
                  onChange={(e) => setModel("ollama", e.target.value)}
                  placeholder="qwen2.5-coder:7b, qwen2.5-coder:14b, codellama..."
                />
              </label>
            </div>
          )}
        </div>

        {/* Output directory */}
        <div className="card space-y-3">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
            Output Directory
          </h2>
          <label className="block">
            <span className="text-xs text-slate-500 mb-1 block">
              Generated projects will be saved here (shared by this machine)
            </span>
            <input
              className="input font-mono text-sm"
              value={outputDirectory}
              onChange={(e) => setOutputDirectory(e.target.value)}
              placeholder="C:/Users/you/autodev-projects"
            />
          </label>
        </div>

        {error && <p className="text-danger text-sm">{error}</p>}

        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? "Saving..." : saved ? "✓ Saved!" : "Save Settings"}
        </button>
      </form>
    </div>
  );
}
