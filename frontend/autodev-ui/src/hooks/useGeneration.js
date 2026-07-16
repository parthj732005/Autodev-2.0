import { useCallback, useRef, useState } from "react";

const WS_URL = "ws://127.0.0.1:8000/generate/ws";

export function useGeneration() {
  const [status, setStatus] = useState("idle"); // idle | connecting | running | completed | error | cancelled
  const [logs, setLogs] = useState([]);
  const [agentStatuses, setAgentStatuses] = useState({});
  const [result, setResult] = useState(null);
  const wsRef = useRef(null);
  const idRef = useRef(0);
  const cancellingRef = useRef(false);

  const addLog = useCallback((entry) => {
    idRef.current += 1;
    setLogs((prev) => [...prev, { ...entry, _id: idRef.current }]);
  }, []);

  const generate = useCallback(
    (prompt, provider = null, token = null) => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      cancellingRef.current = false;
      setStatus("connecting");
      setLogs([]);
      setAgentStatuses({});
      setResult(null);

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        // Authentication handshake — must be the first message. The backend
        // resolves identity via the platform service and replies with an
        // "authenticated" event before the actual prompt is sent, so a token
        // never sits in a URL/query string.
        ws.send(JSON.stringify({ type: "authenticate", token }));
      };

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        addLog(data);

        const { agent, event } = data;

        if (event === "authenticated" && agent === "System") {
          setStatus("running");
          ws.send(JSON.stringify({ prompt, ...(provider && { provider }) }));
          addLog({ agent: "System", event: "log", message: "Starting generation..." });
          return;
        }

        if (agent) {
          setAgentStatuses((prev) => ({
            ...prev,
            [agent]:
              event === "completed"
                ? "completed"
                : event === "failed"
                ? "failed"
                : event === "started"
                ? "running"
                : event === "retry"
                ? "retrying"
                : prev[agent] || "running",
          }));
        }

        if (event === "completed" && agent === "System") {
          setStatus("completed");
          setResult(data.data || null);
        }

        if (event === "cancelled" && agent === "System") {
          setStatus("cancelled");
        }

        if (event === "error") {
          setStatus("error");
        }
      };

      ws.onerror = () => {
        setStatus("error");
        addLog({ agent: "System", event: "error", message: "WebSocket connection failed. Is the backend running on port 8000?" });
      };

      ws.onclose = () => {
        wsRef.current = null;
        if (cancellingRef.current) {
          cancellingRef.current = false;
          return;
        }
        // Unexpected close while still running — surface an error to the user
        setStatus((prev) => {
          if (prev === "running" || prev === "connecting") {
            addLog({ agent: "System", event: "error", message: "Connection closed unexpectedly. The backend may have crashed or timed out." });
            return "error";
          }
          return prev;
        });
      };
    },
    [addLog]
  );

  const cancel = useCallback(() => {
    if (wsRef.current) {
      cancellingRef.current = true;
      addLog({ agent: "System", event: "log", message: "Cancelling..." });
      try {
        // Any text the backend receives during generation is treated as a
        // cancel signal — this actually interrupts the in-flight LLM call
        // server-side instead of just closing our end of the socket.
        wsRef.current.send(JSON.stringify({ action: "cancel" }));
      } catch {
        // socket may already be closing; fall through to close()
      }
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus("cancelled");
  }, [addLog]);

  return { status, logs, agentStatuses, result, generate, cancel };
}
