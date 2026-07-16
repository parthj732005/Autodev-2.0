import { useEffect, useState } from "react";
import AgentStatus from "../components/AgentStatus";
import ArchitecturePreview from "../components/ArchitecturePreview";
import ConsistencyReport from "../components/ConsistencyReport";
import LiveLogs from "../components/LiveLogs";
import ProjectTree from "../components/ProjectTree";
import PromptEditor from "../components/PromptEditor";
import RepairSummary from "../components/RepairSummary";
import ValidationReport from "../components/ValidationReport";
import { useAuth } from "../hooks/useAuth";
import { useGeneration } from "../hooks/useGeneration";
import { api } from "../services/api";
import { settingsApi } from "../services/settingsApi";

const CONFIGURED_FIELD = {
  openai: "openaiApiKeyConfigured",
  anthropic: "anthropicApiKeyConfigured",
  groq: "groqApiKeyConfigured",
  huggingface: "huggingfaceApiKeyConfigured",
};

const MODEL_FIELD = {
  openai: "openaiModel",
  anthropic: "anthropicModel",
  groq: "groqModel",
  huggingface: "huggingfaceModel",
  ollama: "ollamaModel",
};

const STATUS_BANNER = {
  idle: null,
  connecting: { text: "Connecting to backend...", cls: "text-primary" },
  running: { text: "Generating your project...", cls: "text-primary" },
  completed: { text: "Project generated successfully!", cls: "text-success" },
  error: { text: "An error occurred. Check the logs.", cls: "text-danger" },
  cancelled: { text: "Generation cancelled — no project was saved.", cls: "text-slate-400" },
};

function ProviderSelector({ selected, onChange, providers, disabled }) {
  if (!providers || providers.length === 0) return null;

  const selectedEntry = providers.find((p) => p.value === selected);

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-600 shrink-0">Provider:</span>
        <div className="flex gap-1.5 flex-wrap">
          {providers.map((p) => (
            <button
              key={p.value}
              onClick={() => !disabled && onChange(p.value)}
              disabled={disabled}
              title={p.configured ? p.model : `${p.label} needs an API key — configure it in Settings`}
              className={`px-2.5 py-1 text-xs rounded-lg border transition-colors font-medium ${
                disabled ? "opacity-60 cursor-not-allowed" : ""
              } ${
                selected === p.value
                  ? p.configured
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-warning bg-warning/10 text-warning"
                  : "border-border text-slate-500 hover:border-slate-500 hover:text-slate-300"
              }`}
            >
              {p.configured ? "" : "🔒 "}
              {p.label}
            </button>
          ))}
        </div>
        {selectedEntry && (
          <span className="text-xs text-slate-700 font-mono ml-1">{selectedEntry.model}</span>
        )}
      </div>
      {selectedEntry && !selectedEntry.configured && (
        <span className="text-xs text-warning">
          {selectedEntry.label} is not configured — add an API key in Settings before generating.
        </span>
      )}
    </div>
  );
}

export default function Generate() {
  const { token } = useAuth();
  const { status, logs, agentStatuses, result, generate, cancel } = useGeneration();
  const isRunning = status === "connecting" || status === "running";
  const plan = result?.plan || null;
  const banner = STATUS_BANNER[status];

  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState(null);

  useEffect(() => {
    if (!token) return;
    // The provider list/labels are a static, non-secret catalog from FastAPI;
    // whether each one is actually configured (and which model/selection)
    // is per-user state that now lives in the platform service.
    Promise.all([api.getProviders(), settingsApi.get(token)])
      .then(([catalog, userSettings]) => {
        const merged = (catalog.providers || []).map((p) => ({
          value: p.value,
          label: p.label,
          model: userSettings[MODEL_FIELD[p.value]] || p.defaultModel,
          configured: p.value === "ollama" ? true : !!userSettings[CONFIGURED_FIELD[p.value]],
        }));
        setProviders(merged);
        setSelectedProvider(userSettings.selectedProvider || null);
      })
      .catch(() => {});
  }, [token]);

  function handleGenerate(prompt) {
    generate(prompt, selectedProvider, token);
  }

  return (
    <div className="flex flex-col h-full min-h-0 p-5 gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Generate Project</h1>
          <p className="text-sm text-slate-500">Describe what you want to build</p>
        </div>
        <div className="flex items-center gap-4">
          <ProviderSelector
            providers={providers}
            selected={selectedProvider}
            onChange={setSelectedProvider}
            disabled={isRunning}
          />
          {banner && (
            <span className={`text-sm font-medium ${banner.cls} flex items-center gap-2`}>
              {isRunning && <span className="animate-spin text-base">⟳</span>}
              {banner.text}
              {isRunning && (
                <button onClick={cancel} className="btn-ghost text-xs px-2 py-1 ml-2">
                  Cancel
                </button>
              )}
            </span>
          )}
        </div>
      </div>

      {/* Main layout */}
      <div className="flex gap-4 flex-1 min-h-0">
        {/* Left column */}
        <div className="flex flex-col gap-4 w-80 flex-shrink-0 overflow-y-auto">
          <PromptEditor onGenerate={handleGenerate} isRunning={isRunning} />
          <ArchitecturePreview plan={plan} />
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-4 flex-1 min-h-0 overflow-y-auto">
          <div className="grid grid-cols-3 gap-4 h-56 flex-shrink-0 overflow-hidden">
            <div className="col-span-1 h-full min-h-0">
              <AgentStatus agentStatuses={agentStatuses} />
            </div>
            <div className="col-span-2 flex flex-col min-h-0 h-full">
              <LiveLogs logs={logs} />
            </div>
          </div>

          {result && (
            <div className="grid grid-cols-2 gap-4">
              <ProjectTree
                files={result.files || []}
                projectPath={result.project_path}
              />
              <div className="space-y-4">
                <ValidationReport
                  report={result.validation_report}
                  valid={result.valid}
                />
                <RepairSummary report={result.repair_report} />
                <ConsistencyReport report={result.consistency_report} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
