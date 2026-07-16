import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ConsistencyReport from "../components/ConsistencyReport";
import RepairSummary from "../components/RepairSummary";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";

// ─── File Tree ────────────────────────────────────────────────────────────────

function buildTree(files) {
  const tree = {};
  for (const f of files) {
    const parts = (f.path || f).split("/");
    let node = tree;
    for (const part of parts) {
      node[part] = node[part] || {};
      node = node[part];
    }
  }
  return tree;
}

function TreeNode({ name, node, depth = 0 }) {
  const [open, setOpen] = useState(depth < 2);
  const isFolder = Object.keys(node).length > 0;
  return (
    <div>
      <button
        onClick={() => isFolder && setOpen((p) => !p)}
        className="flex items-center gap-1.5 w-full text-left py-0.5 hover:text-slate-100 transition-colors"
        style={{ paddingLeft: depth * 14 + 4 }}
      >
        <span className="text-slate-600 text-xs w-3">
          {isFolder ? (open ? "▼" : "▶") : "·"}
        </span>
        <span className={`text-xs font-mono ${isFolder ? "text-warning" : "text-slate-400"}`}>
          {name}
        </span>
      </button>
      {isFolder && open &&
        Object.entries(node).map(([child, childNode]) => (
          <TreeNode key={child} name={child} node={childNode} depth={depth + 1} />
        ))}
    </div>
  );
}

// ─── Setup Instructions ───────────────────────────────────────────────────────

function SetupInstructions({ projectName, token }) {
  const [instructions, setInstructions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const fetched = useRef(false);

  useEffect(() => {
    if (fetched.current || !token) return;
    fetched.current = true;
    api.getSetupInstructions(projectName, token)
      .then((data) => setInstructions(data.instructions))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [projectName, token]);

  if (loading) {
    return (
      <div className="card space-y-2">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
          Setup Instructions
        </h2>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <span className="animate-spin">⟳</span>
          Generating setup guide with AI...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card border-danger/20">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest mb-2">
          Setup Instructions
        </h2>
        <p className="text-danger text-xs">{error}</p>
      </div>
    );
  }

  if (!instructions) return null;

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
          Setup Instructions
        </h2>
        <span className="text-xs text-slate-600">AI-generated · specific to this project</span>
      </div>

      <div className="space-y-5">
        {instructions.map((step, i) => (
          <div key={i} className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center font-bold shrink-0">
                {i + 1}
              </span>
              <span className="text-sm font-medium text-slate-200">{step.title}</span>
            </div>

            {step.commands?.length > 0 && (
              // Fixed (non-theme-reactive) colors: this is a deliberate dark
              // "terminal" look in both themes, like a code editor — using
              // theme-aware text-slate-* here would invert to dark-on-dark
              // in light mode instead of staying readable on the black bg.
              <div className="ml-7 bg-[#0d0d0d] border border-[#2a2a2a] rounded-lg overflow-hidden">
                {step.commands.map((cmd, j) => (
                  <div key={j} className="flex items-center gap-2 px-3 py-2 border-b border-[#2a2a2a] last:border-0 group">
                    <span className="text-success text-xs shrink-0">$</span>
                    <code className="text-xs font-mono text-[#cbd5e1] flex-1 select-all">{cmd}</code>
                    <button
                      onClick={() => navigator.clipboard.writeText(cmd)}
                      className="opacity-0 group-hover:opacity-100 text-[#64748b] hover:text-[#cbd5e1] text-xs transition-all"
                    >
                      copy
                    </button>
                  </div>
                ))}
              </div>
            )}

            {step.note && (
              <p className="ml-7 text-xs text-slate-500 leading-relaxed">
                💡 {step.note}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Generation Logs ──────────────────────────────────────────────────────────

function GenerationLogs({ logs }) {
  const [open, setOpen] = useState(false);
  if (!logs || logs.length === 0) return null;

  return (
    <div className="card space-y-3">
      <button
        onClick={() => setOpen((p) => !p)}
        className="flex items-center justify-between w-full text-left"
      >
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
          Generation Logs
        </h2>
        <span className="text-xs text-slate-600">
          {logs.length} events {open ? "▼" : "▶"}
        </span>
      </button>

      {open && (
        <div className="max-h-80 overflow-y-auto space-y-1 font-mono text-xs">
          {logs.map((log, i) => (
            <div key={i} className="flex gap-2 py-1 border-b border-border last:border-0">
              <span className="text-slate-600 shrink-0">{log.agent}</span>
              <span
                className={
                  log.event === "failed" || log.event === "error"
                    ? "text-danger"
                    : log.event === "completed"
                    ? "text-success"
                    : "text-slate-400"
                }
              >
                {log.message}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Validation Badge ─────────────────────────────────────────────────────────

function ValidationBadge({ report }) {
  if (!report) {
    return (
      <div className="card flex items-center justify-center text-slate-700 text-sm">
        No validation data
      </div>
    );
  }

  const passed = report.passed?.length || 0;
  const errors = report.errors?.length || 0;
  const warnings = report.warnings?.length || 0;
  const ok = errors === 0;

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
          Validation
        </h2>
        <span className={`text-xs px-3 py-1 rounded-full border font-mono font-semibold ${
          ok
            ? "text-success border-success/40 bg-success/10"
            : "text-danger border-danger/40 bg-danger/10"
        }`}>
          {ok ? "✓ PASSED" : "✕ FAILED"}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-surface-2 border border-border rounded-xl py-4">
          <div className="text-2xl font-bold text-success">{passed}</div>
          <div className="text-xs text-slate-500 mt-1">Passed</div>
        </div>
        <div className="bg-surface-2 border border-border rounded-xl py-4">
          <div className="text-2xl font-bold text-warning">{warnings}</div>
          <div className="text-xs text-slate-500 mt-1">Warnings</div>
        </div>
        <div className="bg-surface-2 border border-border rounded-xl py-4">
          <div className="text-2xl font-bold text-danger">{errors}</div>
          <div className="text-xs text-slate-500 mt-1">Errors</div>
        </div>
      </div>

      {ok && (
        <p className="text-xs text-slate-600 text-center">
          All generated files passed syntax validation.
        </p>
      )}

      {report.errors?.map((e, i) => (
        <div key={i} className="text-xs bg-danger/5 border border-danger/20 rounded-lg px-3 py-2">
          <span className="font-mono text-danger">{e.file}</span>
          <p className="text-slate-500 mt-0.5">{e.issue}</p>
        </div>
      ))}

      {report.warnings?.map((w, i) => (
        <div key={i} className="text-xs bg-warning/5 border border-warning/20 rounded-lg px-3 py-2">
          <span className="font-mono text-warning">{w.file}</span>
          <p className="text-slate-500 mt-0.5">{w.issue}</p>
        </div>
      ))}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const TYPE_LABELS = {
  backend_only: "Backend Only",
  frontend_only: "Frontend Only",
  fullstack: "Full Stack",
  cli: "CLI",
  library: "Library",
};

export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [vsCodeMsg, setVsCodeMsg] = useState("");

  useEffect(() => {
    if (!token) return;
    api.getGeneratedProject(id, token)
      .then(setProject)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, token]);

  async function handleOpenVSCode() {
    try {
      await api.openInVSCode(id, token);
      setVsCodeMsg("Opened in VS Code!");
      setTimeout(() => setVsCodeMsg(""), 2000);
    } catch {
      setVsCodeMsg("VS Code not found in PATH");
      setTimeout(() => setVsCodeMsg(""), 3000);
    }
  }

  if (loading) return <div className="p-8 text-slate-500 text-sm">Loading project...</div>;
  if (error) return (
    <div className="p-8 space-y-2">
      <p className="text-danger">{error}</p>
      <button onClick={() => navigate("/projects")} className="btn-ghost text-sm">← Back</button>
    </div>
  );
  if (!project) return null;

  const tech = project.technologies || {};
  const fileTree = buildTree(project.file_details || project.files || []);
  const totalLines = (project.file_details || []).reduce((s, f) => s + (f.lines || 0), 0);
  const date = project.generated_at
    ? new Date(project.generated_at).toLocaleString("en-US", {
        month: "long", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit",
      })
    : "";

  return (
    <div className="p-6 space-y-5 max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <button onClick={() => navigate("/projects")} className="text-xs text-slate-600 hover:text-slate-400 mb-2 flex items-center gap-1">
            ← Projects
          </button>
          <h1 className="text-2xl font-bold font-mono text-slate-100">{project.project_name}</h1>
          <p className="text-slate-500 mt-1">{project.description}</p>
          <p className="text-xs text-slate-700 mt-1">{date}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleOpenVSCode}
            className="btn-ghost text-sm flex items-center gap-1.5"
          >
            🖥️ {vsCodeMsg || "Open in VS Code"}
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Type", value: TYPE_LABELS[project.project_type] || project.project_type },
          { label: "Files", value: project.file_count },
          { label: "Lines of Code", value: totalLines.toLocaleString() },
          { label: "Agents Run", value: project.agents_required?.length || "—" },
        ].map(({ label, value }) => (
          <div key={label} className="card text-center">
            <div className="text-lg font-bold text-slate-100">{value}</div>
            <div className="text-xs text-slate-600">{label}</div>
          </div>
        ))}
      </div>

      {/* Tech + Features */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card space-y-3">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
            Tech Stack
          </h2>
          <div className="space-y-2">
            {[
              ["Backend", tech.backend],
              ["Frontend", tech.frontend],
              ["Database", tech.database],
              ["CSS", tech.css],
            ].filter(([, v]) => v && v !== "none").map(([label, value]) => (
              <div key={label} className="flex items-center justify-between text-sm">
                <span className="text-slate-600">{label}</span>
                <span className="font-mono text-slate-300">{value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card space-y-3">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
            Features
          </h2>
          <ul className="space-y-1">
            {(project.features || []).map((f, i) => (
              <li key={i} className="text-xs text-slate-400 flex gap-2">
                <span className="text-primary shrink-0">▸</span> {f}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Setup Instructions (LLM-generated) */}
      <SetupInstructions projectName={id} token={token} />

      {/* File Tree + Validation side by side */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
              File Tree
            </h2>
            <span className="text-xs text-slate-600">{project.file_count} files</span>
          </div>
          <div className="overflow-y-auto max-h-80">
            {Object.entries(fileTree).map(([name, node]) => (
              <TreeNode key={name} name={name} node={node} depth={0} />
            ))}
          </div>
          <div className="pt-1 border-t border-border">
            <p className="text-xs font-mono text-slate-600 break-all">{project.path}</p>
          </div>
        </div>

        <ValidationBadge report={project.validation_report} />
      </div>

      <RepairSummary report={project.repair_report} />

      <ConsistencyReport report={project.consistency_report} />

      <GenerationLogs logs={project.generation_logs} />
    </div>
  );
}
