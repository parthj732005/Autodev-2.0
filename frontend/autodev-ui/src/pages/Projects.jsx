import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";

const TYPE_BADGE = {
  backend_only: { label: "Backend", cls: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
  frontend_only: { label: "Frontend", cls: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
  fullstack: { label: "Full Stack", cls: "bg-primary/10 text-primary border-primary/20" },
  cli: { label: "CLI", cls: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
  library: { label: "Library", cls: "bg-warning/10 text-warning border-warning/20" },
};

function TechPill({ label }) {
  if (!label || label === "none") return null;
  return (
    <span className="px-2 py-0.5 text-xs rounded bg-surface-3 text-slate-400 border border-border">
      {label}
    </span>
  );
}

function ProjectCard({ project }) {
  const tech = project.technologies || {};
  const badge = TYPE_BADGE[project.project_type] || TYPE_BADGE.backend_only;
  const date = project.generated_at
    ? new Date(project.generated_at).toLocaleDateString("en-US", {
        month: "short", day: "numeric", year: "numeric",
      })
    : "";
  const errors = project.validation_report?.errors?.length || 0;

  return (
    <Link
      to={`/projects/${project.project_name}`}
      className="card hover:border-primary/40 transition-all group block"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-mono font-semibold text-slate-100 group-hover:text-primary transition-colors truncate">
            {project.project_name}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{project.description}</p>
        </div>
        <span className={`shrink-0 px-2 py-0.5 text-xs rounded-full border font-medium ${badge.cls}`}>
          {badge.label}
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        <TechPill label={tech.backend} />
        <TechPill label={tech.frontend} />
        <TechPill label={tech.database} />
        <TechPill label={tech.css} />
      </div>

      <div className="flex items-center justify-between text-xs text-slate-600">
        <div className="flex items-center gap-3">
          <span>📄 {project.file_count} Files</span>
          <span className={errors > 0 ? "text-warning" : "text-success"}>
            {errors > 0 ? `⚠ Validation: ${errors} Issue${errors === 1 ? "" : "s"}` : "✓ Validation Passed"}
          </span>
        </div>
        <span>{date}</span>
      </div>
    </Link>
  );
}

export default function Projects() {
  const { token } = useAuth();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api.getGeneratedProjects(token)
      .then(setProjects)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Generated Projects</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Projects created by AutoDev on your machine
          </p>
        </div>
        <Link to="/generate" className="btn-primary text-sm">
          ⚡ New Project
        </Link>
      </div>

      {loading && (
        <p className="text-slate-500 text-sm">Scanning output directory...</p>
      )}

      {error && (
        <div className="card border-danger/20 bg-danger/5 text-sm text-slate-400 space-y-2">
          <p className="text-danger font-medium">Could not load projects</p>
          <p>{error}</p>
          <p className="text-xs text-slate-600">Make sure the backend is running on port 8000.</p>
        </div>
      )}

      {!loading && !error && projects.length === 0 && (
        <div className="card text-center py-12 space-y-3">
          <p className="text-3xl">📂</p>
          <p className="text-slate-300 font-medium">No projects yet</p>
          <p className="text-slate-500 text-sm">
            Go to Generate and describe your first project.
          </p>
          <Link to="/generate" className="btn-primary inline-block mt-2">
            ⚡ Generate First Project
          </Link>
        </div>
      )}

      {projects.length > 0 && (
        <div className="grid grid-cols-2 gap-4">
          {projects.map((p) => (
            <ProjectCard key={p.project_name} project={p} />
          ))}
        </div>
      )}
    </div>
  );
}
