
import React, { useEffect, useState } from "react";

export default function MonitoringDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  async function loadMonitor() {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/monitor`);
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      console.error("Monitor error:", err);
      setError("Monitoring unavailable");
    }
  }

  useEffect(() => {
    loadMonitor();

    // Auto-refresh every 30 seconds
    const interval = setInterval(loadMonitor, 30000);
    return () => clearInterval(interval);
  }, []);

  if (error) return <p style={{ color: "red" }}>{error}</p>;
  if (!data) return <p>Loading monitor...</p>;

  const scanner = data.scanner;

  const statusColor =
    data.overall_status === "healthy"
      ? "lime"
      : data.overall_status === "degraded"
      ? "orange"
      : "red";

  return (
    <div
      style={{
        background: "#111",
        color: "white",
        padding: "1rem",
        borderRadius: "12px",
        marginTop: "2rem",
      }}
    >
      <h3>🧠 System Monitor</h3>

      <p>
        Overall Status:{" "}
        <strong style={{ color: statusColor }}>
          {data.overall_status}
        </strong>
      </p>

      <hr />

      <p>Last Scan Result: {scanner.last_result}</p>
      <p>Last Duration: {scanner.last_duration}s</p>
      <p>Scan Failures: {scanner.failure_count}</p>
      <p>API Failure Count: {data.api_failures}</p>

      <hr />

      <p>AI Engine Status: {data.ai_engine.status}</p>
      <p>OpenAI Key Present: {data.ai_engine.openai_key ? "Yes" : "No"}</p>

      <hr />

      <p style={{ fontSize: "0.8rem", opacity: 0.6 }}>
        Updated: {new Date(data.timestamp).toLocaleString()}
      </p>
    </div>
  );
}
