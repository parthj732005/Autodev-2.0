import { useEffect, useRef } from "react";

const EVENT_COLORS = {
  started: "text-primary",
  completed: "text-success",
  failed: "text-danger",
  retry: "text-warning",
  retrying: "text-warning",
  error: "text-danger",
  log: "text-slate-400",
};

function formatTime(ts) {
  if (!ts) return "";
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString("en-US", { hour12: false });
}

export default function LiveLogs({ logs }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="card flex flex-col h-full min-h-0">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-widest">
          Live Logs
        </h2>
        <span className="text-xs text-slate-600">{logs.length} entries</span>
      </div>

      <div className="flex-1 overflow-y-auto font-mono text-xs space-y-0.5 min-h-0">
        {logs.length === 0 && (
          <p className="text-slate-700 py-4 text-center">Waiting for generation to start...</p>
        )}
        {logs.map((log) => (
          <div key={log._id} className="flex gap-2 leading-5">
            <span className="text-slate-700 shrink-0">{formatTime(log.timestamp)}</span>
            <span className="text-slate-600 shrink-0 w-36 truncate">[{log.agent || "System"}]</span>
            <span className={`${EVENT_COLORS[log.event] || "text-slate-400"} break-all`}>
              {log.message}
            </span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
