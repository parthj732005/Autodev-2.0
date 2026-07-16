export default function RepairSummary({ report }) {
  if (!report || !report.attempted || report.attempted.length === 0) return null;

  const { repaired = [], reverted = [] } = report;

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
          Repair Summary
        </h2>
        <span className="text-xs text-slate-600">
          {report.attempted.length} file{report.attempted.length === 1 ? "" : "s"} attempted
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-center">
        <div className="bg-surface-2 rounded-lg py-3">
          <div className="text-success text-xl font-bold">{repaired.length}</div>
          <div className="text-xs text-slate-600">✓ Fixed automatically</div>
        </div>
        <div className="bg-surface-2 rounded-lg py-3">
          <div className="text-warning text-xl font-bold">{reverted.length}</div>
          <div className="text-xs text-slate-600">⚠ Remaining errors</div>
        </div>
      </div>

      {repaired.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 mb-1.5">Files repaired:</p>
          <ul className="space-y-0.5">
            {repaired.map((f) => (
              <li key={f} className="text-xs font-mono text-success flex items-center gap-1.5">
                <span>✓</span> {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      {reverted.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 mb-1.5">Could not be auto-repaired (kept original):</p>
          <ul className="space-y-0.5">
            {reverted.map((f) => (
              <li key={f} className="text-xs font-mono text-warning flex items-center gap-1.5">
                <span>⚠</span> {f}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
