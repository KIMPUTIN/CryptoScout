
import React, { useEffect, useState, useCallback, useRef, memo } from "react";

// ==============================
// CONFIGURATION
// ==============================
const REFRESH_INTERVAL = 30000; // 30s
const REQUEST_TIMEOUT = 10000; // 10s
const SCAN_FAILURE_THRESHOLD = 3;
const API_FAILURE_THRESHOLD = 5;

// ==============================
// MAIN COMPONENT
// ==============================
export default function MonitoringDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const abortControllerRef = useRef(null);

  // ==============================
  // FETCH WITH TIMEOUT
  // ==============================
  const fetchWithTimeout = async (url) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    abortControllerRef.current = controller;

    try {
      const res = await fetch(url, {
        signal: controller.signal,
        headers: { Accept: "application/json" },
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status} - ${res.statusText}`);
      }

      const json = await res.json();

      // Stronger structural validation
      if (
        !json ||
        typeof json !== "object" ||
        !("overall_status" in json)
      ) {
        throw new Error("Unexpected API response structure");
      }

      return json;
    } finally {
      clearTimeout(timeoutId);
    }
  };

  // ==============================
  // LOAD MONITOR DATA
  // ==============================
  const loadMonitor = useCallback(async () => {
    const apiUrl = import.meta.env.VITE_API_URL;

    if (!apiUrl) {
      setError("API URL is not configured");
      return;
    }

    // Abort previous request
    abortControllerRef.current?.abort();

    setLoading(true);

    try {
      const json = await fetchWithTimeout(`${apiUrl}/monitor`);

      setData(json);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      if (err.name === "AbortError") return;
      console.error("Monitor error:", err);
      setError(err.message || "Monitoring unavailable");
    } finally {
      setLoading(false);
    }
  }, []);

  // ==============================
  // AUTO REFRESH (VISIBILITY AWARE)
  // ==============================
  useEffect(() => {
    loadMonitor();

    const interval = setInterval(() => {
      if (document.visibilityState === "visible") {
        loadMonitor();
      }
    }, REFRESH_INTERVAL);

    return () => {
      clearInterval(interval);
      abortControllerRef.current?.abort();
    };
  }, [loadMonitor]);

  // ==============================
  // HELPERS
  // ==============================
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case "healthy":
        return "#4ade80";
      case "degraded":
        return "#fb923c";
      case "unhealthy":
      case "failed":
        return "#f87171";
      default:
        return "#9ca3af";
    }
  };

  const getAiStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case "operational":
        return "#4ade80";
      case "degraded":
        return "#fb923c";
      case "offline":
        return "#f87171";
      default:
        return "#9ca3af";
    }
  };

  const formatDuration = (seconds) => {
    if (typeof seconds !== "number" || isNaN(seconds)) return "N/A";
    if (seconds < 0) return "0s";
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    return `${seconds.toFixed(2)}s`;
  };

  // ==============================
  // RENDER STATES
  // ==============================

  if (!data && loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={loadMonitor} />;
  }

  const scanner = data?.scanner ?? {};
  const aiEngine = data?.ai_engine ?? {};
  const overallStatus = data?.overall_status ?? "unknown";
  const apiFailures = data?.api_failures ?? 0;
  const timestamp =
    data?.timestamp ?? lastUpdated?.toISOString() ?? null;

  const overallColor = getStatusColor(overallStatus);

  return (
    <div style={containerStyle}>
      <GlobalSpinnerStyles />

      <Header loading={loading} onRefresh={loadMonitor} />

      {/* Overall Status */}
      <div style={sectionStyle}>
        <div style={rowStyle}>
          <span style={{ color: "#9ca3af" }}>Overall Status:</span>
          <strong
            style={{
              color: overallColor,
              textTransform: "uppercase",
              fontSize: "1.1rem",
            }}
          >
            {overallStatus}
          </strong>
          <span
            style={{
              marginLeft: "auto",
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: overallColor,
              boxShadow: `0 0 10px ${overallColor}`,
            }}
          />
        </div>
      </div>

      {/* Scanner Stats */}
      <div style={gridStyle}>
        <StatCard
          label="Last Scan Result"
          value={scanner.last_result || "N/A"}
          color={
            scanner.last_result === "success"
              ? "#4ade80"
              : "#f87171"
          }
        />
        <StatCard
          label="Last Duration"
          value={formatDuration(scanner.last_duration)}
        />
        <StatCard
          label="Scan Failures"
          value={scanner.failure_count ?? 0}
          warning={
            (scanner.failure_count ?? 0) >
            SCAN_FAILURE_THRESHOLD
          }
        />
        <StatCard
          label="API Failures"
          value={apiFailures}
          warning={apiFailures > API_FAILURE_THRESHOLD}
        />
      </div>

      {/* AI Engine */}
      <div style={sectionStyle}>
        <h4 style={{ marginBottom: "0.75rem", color: "#d1d5db" }}>
          🤖 AI Engine
        </h4>
        <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
          <div>
            <span style={{ color: "#9ca3af" }}>Status: </span>
            <strong style={{ color: getAiStatusColor(aiEngine.status) }}>
              {aiEngine.status || "Unknown"}
            </strong>
          </div>
          <div>
            <span style={{ color: "#9ca3af" }}>OpenAI Key: </span>
            <strong
              style={{
                color: aiEngine.openai_key_configured
                  ? "#4ade80"
                  : "#f87171",
              }}
            >
              {aiEngine.openai_key_configured
                ? "✓ Configured"
                : "✗ Missing"}
            </strong>
          </div>
        </div>
      </div>

      {/* Footer */}
      <Footer
        timestamp={timestamp}
        loading={loading}
      />
    </div>
  );
}

// ==============================
// SUB COMPONENTS
// ==============================

const StatCard = memo(function StatCard({
  label,
  value,
  color = "#e5e7eb",
  warning = false,
}) {
  return (
    <div
      style={{
        background: "#1a1a1a",
        padding: "0.75rem",
        borderRadius: 6,
        borderLeft: warning ? "3px solid #f87171" : "none",
      }}
    >
      <div style={{ color: "#9ca3af", fontSize: "0.85rem" }}>
        {label}
      </div>
      <div
        style={{
          color: warning ? "#f87171" : color,
          fontWeight: 600,
          fontSize: "1.1rem",
        }}
      >
        {value}
        {warning && (
          <span style={{ marginLeft: 6 }}>⚠️</span>
        )}
      </div>
    </div>
  );
});

function Header({ loading, onRefresh }) {
  return (
    <div style={headerStyle}>
      <h3 style={{ margin: 0, color: "#e5e7eb" }}>
        🧠 System Monitor
      </h3>
      <button
        type="button"
        onClick={onRefresh}
        disabled={loading}
        style={refreshButtonStyle(loading)}
      >
        <span
          style={{
            display: "inline-block",
            animation: loading
              ? "spin 1s linear infinite"
              : "none",
          }}
        >
          ↻
        </span>
        {loading ? "Refreshing..." : "Refresh"}
      </button>
    </div>
  );
}

function LoadingState() {
  return (
    <div style={containerStyle}>
      <GlobalSpinnerStyles />
      <h3>🧠 System Monitor</h3>
      <div role="status">Loading monitoring data...</div>
    </div>
  );
}

function ErrorState({ error, onRetry }) {
  return (
    <div style={containerStyle}>
      <h3>🧠 System Monitor</h3>
      <p style={{ color: "#f87171" }}>{error}</p>
      <button type="button" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}

function Footer({ timestamp, loading }) {
  return (
    <div style={footerStyle}>
      <span>
        Last Updated:{" "}
        {timestamp
          ? new Date(timestamp).toLocaleString()
          : "Never"}
      </span>
      {loading && <span>Updating...</span>}
    </div>
  );
}

function GlobalSpinnerStyles() {
  return (
    <style>
      {`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}
    </style>
  );
}

// ==============================
// STYLES
// ==============================
const containerStyle = {
  background: "#111",
  color: "white",
  padding: "1.5rem",
  borderRadius: 12,
  marginTop: "2rem",
  fontFamily: "system-ui, -apple-system, sans-serif",
};

const sectionStyle = {
  background: "#1a1a1a",
  padding: "1rem",
  borderRadius: 8,
  marginBottom: "1rem",
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
  gap: "0.75rem",
  marginBottom: "1rem",
};

const rowStyle = {
  display: "flex",
  alignItems: "center",
  gap: "0.5rem",
};

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "1.5rem",
};

const footerStyle = {
  display: "flex",
  justifyContent: "space-between",
  fontSize: "0.8rem",
  color: "#6b7280",
  borderTop: "1px solid #1f2937",
  paddingTop: "1rem",
};

const refreshButtonStyle = (loading) => ({
  background: "transparent",
  border: "1px solid #374151",
  color: loading ? "#6b7280" : "#e5e7eb",
  borderRadius: 6,
  padding: "0.4rem 0.8rem",
  cursor: loading ? "wait" : "pointer",
});
