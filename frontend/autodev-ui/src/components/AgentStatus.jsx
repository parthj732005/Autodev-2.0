const STATUS_CONFIG = {
  running: { color: "text-primary", icon: "⟳", spin: true },
  completed: { color: "text-success", icon: "✓", spin: false },
  failed: { color: "text-danger", icon: "✕", spin: false },
  retrying: { color: "text-warning", icon: "↺", spin: true },
  pending: { color: "text-slate-600", icon: "○", spin: false },
};

const ALL_AGENTS = [
  "PlannerAgent",
  "DatabaseAgent",
  "BackendAgent",
  "FrontendAgent",
  "DevOpsAgent",
  "TestingAgent",
  "DocumentationAgent",
  "ValidatorAgent",
];

export default function AgentStatus({ agentStatuses }) {
  return (
    <div className="card flex flex-col gap-2 h-full min-h-0">
      <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest mb-1 shrink-0">
        Agent Status
      </h2>
      <div className="space-y-2 overflow-y-auto min-h-0">
        {ALL_AGENTS.map((agent) => {
          const status = agentStatuses[agent] || "pending";
          const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
          return (
            <div key={agent} className="flex items-center gap-2">
              <span
                className={`text-sm font-mono ${cfg.color} ${cfg.spin ? "animate-spin inline-block" : ""}`}
                style={{ minWidth: 14 }}
              >
                {cfg.icon}
              </span>
              <span className={`text-sm ${status === "pending" ? "text-slate-600" : "text-slate-300"}`}>
                {agent}
              </span>
              {status !== "pending" && (
                <span className={`ml-auto text-xs font-mono ${cfg.color}`}>{status}</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
