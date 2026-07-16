import { Link } from "react-router-dom";

const FEATURES = [
  {
    icon: "🧠",
    title: "Planner Agent",
    desc: "Analyzes your prompt and produces the authoritative plan: tech stack, API routes, entities, and env vars every other agent must follow.",
  },
  {
    icon: "🗄️",
    title: "Database Agent",
    desc: "Owns the canonical SQLAlchemy models — the single source of truth every other agent imports from, never redefines.",
  },
  {
    icon: "⚙️",
    title: "Backend Agent",
    desc: "Implements exactly the API contract from the plan — FastAPI or Flask routes, services, and business logic.",
  },
  {
    icon: "🎨",
    title: "Frontend Agent",
    desc: "Generates React + Vite + TailwindCSS UIs that call exactly the backend's planned endpoints — no invented routes.",
  },
  {
    icon: "🐳",
    title: "DevOps Agent",
    desc: "Generates Dockerfile, docker-compose.yml, .gitignore, and a complete .env.example matching the plan's env vars.",
  },
  {
    icon: "🧪",
    title: "Testing Agent",
    desc: "Writes pytest suites covering every planned route — happy paths, validation errors, and edge cases.",
  },
  {
    icon: "📄",
    title: "Documentation Agent",
    desc: "Generates a full README — install steps, API reference, and env var docs — scoped to the real API contract.",
  },
  {
    icon: "✅",
    title: "Validator Agent",
    desc: "Parses every generated file (ast for Python, bracket-balance for JS) and reports structured, actionable syntax diagnostics.",
  },
  {
    icon: "🛠️",
    title: "Targeted Repair Phase",
    desc: "Deterministic, one-shot repair: only files with a real syntax error get a single fix attempt, accepted only if independently re-verified — otherwise the original is kept untouched.",
  },
  {
    icon: "🔗",
    title: "Consistency Checker",
    desc: "Deterministic, zero-LLM pass verifying frontend calls, tests, README, Docker entry point, and requirements.txt all agree with the backend.",
  },
];

const PROVIDERS = ["OpenAI", "Anthropic", "Groq", "HuggingFace", "Ollama (local)"];

export default function Home() {
  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-4xl">⚡</span>
          <div>
            <h1 className="text-3xl font-bold text-slate-100">AutoDev 2.0</h1>
            <p className="text-slate-500 text-lg">AI-Powered Software Engineering Platform</p>
          </div>
        </div>
        <p className="text-slate-400 text-base max-w-2xl leading-relaxed">
          Describe any software project in plain English. AutoDev combines seven specialized AI
          agents — sharing one authoritative plan and API contract — with deterministic validation,
          a one-shot targeted repair pass, and consistency checking, to generate a structured,
          internally-consistent software project: backend, frontend, database, Docker config,
          tests, and documentation.
        </p>
        <div className="flex gap-3 mt-6">
          <Link to="/generate" className="btn-primary inline-flex items-center gap-2">
            ⚡ Start Generating
          </Link>
          <Link to="/settings" className="btn-ghost inline-flex items-center gap-2">
            ⚙️ Configure API Key
          </Link>
        </div>
        <div className="flex items-center gap-2 mt-5 flex-wrap">
          <span className="text-xs text-slate-500 uppercase tracking-widest font-semibold mr-1">
            Bring your own provider
          </span>
          {PROVIDERS.map((p) => (
            <span
              key={p}
              className="text-xs px-2.5 py-1 rounded-full border border-slate-700 text-slate-400"
            >
              {p}
            </span>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {FEATURES.map((f) => (
          <div key={f.title} className="card hover:border-primary/30 transition-colors">
            <div className="text-2xl mb-2">{f.icon}</div>
            <h3 className="text-sm font-semibold text-slate-200 mb-1">{f.title}</h3>
            <p className="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 card bg-primary/5 border-primary/20">
        <p className="text-xs text-slate-500 mb-2 font-semibold uppercase tracking-widest">
          How it works
        </p>
        <div className="flex items-center gap-2 text-sm text-slate-400 flex-wrap">
          {[
            "Your prompt",
            "Planner (contract)",
            "Database + Backend + Frontend",
            "DevOps + Tests + Docs",
            "Validator",
            "Targeted Repair",
            "Consistency Check",
            "Project on disk",
          ].map((step, i, arr) => (
            <span key={step} className="flex items-center gap-2">
              <span className="text-slate-300">{step}</span>
              {i < arr.length - 1 && <span className="text-primary">→</span>}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
