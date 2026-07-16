export default function ArchitecturePreview({ plan }) {
  if (!plan) {
    return (
      <div className="card text-slate-700 text-sm text-center py-8">
        Architecture plan will appear here after the Planner Agent runs.
      </div>
    );
  }

  const tech = plan.technologies || {};
  const agents = plan.agents_required || [];
  const features = plan.features || [];

  return (
    <div className="card space-y-4">
      <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
        Architecture Plan
      </h2>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-slate-600 text-xs mb-1">Project</p>
          <p className="text-slate-100 font-mono">{plan.project_name || "—"}</p>
        </div>
        <div>
          <p className="text-slate-600 text-xs mb-1">Type</p>
          <p className="text-primary font-mono">{plan.project_type || "—"}</p>
        </div>
        <div>
          <p className="text-slate-600 text-xs mb-1">Backend</p>
          <p className="text-slate-200">{tech.backend || "none"}</p>
        </div>
        <div>
          <p className="text-slate-600 text-xs mb-1">Frontend</p>
          <p className="text-slate-200">{tech.frontend || "none"}</p>
        </div>
        <div>
          <p className="text-slate-600 text-xs mb-1">Database</p>
          <p className="text-slate-200">{tech.database || "none"}</p>
        </div>
        <div>
          <p className="text-slate-600 text-xs mb-1">CSS</p>
          <p className="text-slate-200">{tech.css || "none"}</p>
        </div>
      </div>

      <div>
        <p className="text-slate-600 text-xs mb-2">Agents</p>
        <div className="flex flex-wrap gap-2">
          {agents.map((a) => (
            <span key={a} className="px-2 py-0.5 text-xs rounded bg-primary/10 text-primary border border-primary/20">
              {a}
            </span>
          ))}
        </div>
      </div>

      {features.length > 0 && (
        <div>
          <p className="text-slate-600 text-xs mb-2">Features</p>
          <ul className="space-y-1">
            {features.slice(0, 8).map((f, i) => (
              <li key={i} className="text-xs text-slate-400 flex gap-2">
                <span className="text-primary">▸</span> {f}
              </li>
            ))}
            {features.length > 8 && (
              <li className="text-xs text-slate-600">+{features.length - 8} more...</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
