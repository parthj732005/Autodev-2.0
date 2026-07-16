import { useState } from "react";

const EXAMPLES = [
  "Build a FastAPI REST API for a todo app with SQLite",
  "Build a React dashboard for displaying sales analytics",
  "Build a full-stack inventory management system with PostgreSQL",
  "Build a Flask REST API with JWT authentication",
];

export default function PromptEditor({ onGenerate, isRunning }) {
  const [prompt, setPrompt] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (prompt.trim()) onGenerate(prompt.trim());
  }

  return (
    <div className="card flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
          Prompt
        </h2>
        <span className="text-xs text-slate-600">{prompt.length} chars</span>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <textarea
          className="input resize-none font-mono text-sm leading-relaxed"
          rows={5}
          placeholder="Describe the software you want to build..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={isRunning}
        />

        <button
          type="submit"
          className="btn-primary flex items-center justify-center gap-2"
          disabled={isRunning || !prompt.trim()}
        >
          {isRunning ? (
            <>
              <span className="animate-spin text-base">⟳</span> Generating...
            </>
          ) : (
            <>⚡ Generate Project</>
          )}
        </button>
      </form>

      <div className="pt-1">
        <p className="text-xs text-slate-600 mb-2">Examples:</p>
        <div className="flex flex-col gap-1">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setPrompt(ex)}
              disabled={isRunning}
              className="text-left text-xs text-slate-500 hover:text-primary transition-colors truncate"
            >
              → {ex}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
