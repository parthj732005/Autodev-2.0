export default function ValidationReport({ report, valid }) {
  if (!report) return null;

  const passed = report.passed || [];
  const warnings = report.warnings || [];
  const errors = report.errors || [];

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
          Validation Report
        </h2>
        <span
          className={`text-xs font-mono px-2 py-0.5 rounded-full border ${
            valid
              ? "text-success border-success/30 bg-success/10"
              : "text-danger border-danger/30 bg-danger/10"
          }`}
        >
          {valid ? "✓ PASSED" : "✕ FAILED"}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-surface-2 rounded-lg py-3">
          <div className="text-success text-xl font-bold">{passed.length}</div>
          <div className="text-xs text-slate-600">Passed</div>
        </div>
        <div className="bg-surface-2 rounded-lg py-3">
          <div className="text-warning text-xl font-bold">{warnings.length}</div>
          <div className="text-xs text-slate-600">Warnings</div>
        </div>
        <div className="bg-surface-2 rounded-lg py-3">
          <div className="text-danger text-xl font-bold">{errors.length}</div>
          <div className="text-xs text-slate-600">Errors</div>
        </div>
      </div>

      {errors.length > 0 && (
        <div>
          <p className="text-xs text-danger mb-2">Errors</p>
          <div className="space-y-1">
            {errors.map((e, i) => (
              <div key={i} className="bg-danger/5 border border-danger/20 rounded px-3 py-2 text-xs">
                <span className="font-mono text-danger">{e.file}</span>
                <span className="text-slate-500 ml-2">{e.issue}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {warnings.length > 0 && (
        <div>
          <p className="text-xs text-warning mb-2">Warnings</p>
          <div className="space-y-1">
            {warnings.map((w, i) => (
              <div key={i} className="bg-warning/5 border border-warning/20 rounded px-3 py-2 text-xs">
                <span className="font-mono text-warning">{w.file}</span>
                <span className="text-slate-500 ml-2">{w.issue}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
