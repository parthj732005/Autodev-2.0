import { useState } from "react";

const SEVERITY_STYLES = {
  error: "bg-danger/5 border-danger/20 text-danger",
  warning: "bg-warning/5 border-warning/20 text-warning",
  info: "bg-gray-500/5 border-gray-500/20 text-gray-400",
};

const SEVERITY_LABEL = { error: "Error", warning: "Warning", info: "Info" };
const SEVERITY_ORDER = { error: 0, warning: 1, info: 2 };

export default function ConsistencyReport({ report }) {
  const [expanded, setExpanded] = useState(false);
  if (!report || report.checks_run === undefined) return null;

  const issues = [...(report.issues || [])].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3)
  );

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
          Consistency Check
        </h2>
        <span
          className={`text-xs font-mono px-2 py-0.5 rounded-full border ${
            issues.length === 0
              ? "text-success border-success/30 bg-success/10"
              : "text-warning border-warning/30 bg-warning/10"
          }`}
        >
          {issues.length === 0 ? "✓ CONSISTENT" : `${issues.length} ISSUE${issues.length === 1 ? "" : "S"}`}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-surface-2 rounded-lg py-3">
          <div className="text-danger text-xl font-bold">{report.error_count || 0}</div>
          <div className="text-xs text-slate-600">Errors</div>
        </div>
        <div className="bg-surface-2 rounded-lg py-3">
          <div className="text-warning text-xl font-bold">{report.warning_count || 0}</div>
          <div className="text-xs text-slate-600">Warnings</div>
        </div>
        <div className="bg-surface-2 rounded-lg py-3">
          <div className="text-gray-400 text-xl font-bold">{report.info_count || 0}</div>
          <div className="text-xs text-slate-600">Info</div>
        </div>
      </div>

      {issues.length === 0 && (
        <p className="text-xs text-slate-600 text-center">
          All generated files agree on routes, contracts, and dependencies.
        </p>
      )}

      {issues.length > 0 && (
        <div>
          <button
            onClick={() => setExpanded((p) => !p)}
            className="text-xs text-primary hover:text-primary-hover font-medium"
          >
            {expanded ? "▲ Hide Details" : "▼ Show Details"}
          </button>

          {expanded && (
            <div className="space-y-1.5 mt-3">
              {issues.map((issue, i) => (
                <div
                  key={i}
                  className={`border rounded px-3 py-2 text-xs ${SEVERITY_STYLES[issue.severity] || SEVERITY_STYLES.info}`}
                >
                  <p className="font-semibold uppercase tracking-wide text-[10px] mb-1 opacity-80">
                    {SEVERITY_LABEL[issue.severity] || issue.severity}
                  </p>
                  <p className="font-medium">{issue.message}</p>
                  {issue.suggestion && (
                    <p className="text-slate-500 mt-1">💡 {issue.suggestion}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
