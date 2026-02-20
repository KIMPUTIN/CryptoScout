import React, { useEffect, useState, useCallback, useRef } from "react";

export default function MonitoringDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // Use ref to prevent multiple simultaneous requests
  const isMounted = useRef(true);
  const abortControllerRef = useRef(null);

  // =====================================
  // LOAD MONITORING DATA
  // =====================================
  const loadMonitor = useCallback(async () => {
    // Cancel previous request if still pending
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      setLoading(true);
      
      const apiUrl = import.meta.env.VITE_API_URL;
      if (!apiUrl) {
        throw new Error("API URL is not configured");
      }

      const res = await fetch(`${apiUrl}/monitor`, {
        signal: abortControllerRef.current.signal,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        // Add timeout
        cache: 'no-cache'
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status} - ${res.statusText}`);
      }

      const json = await res.json();
      
      // Validate response structure
      if (!json || typeof json !== 'object') {
        throw new Error("Invalid response format");
      }

      // Only update state if component is still mounted
      if (isMounted.current) {
        setData(json);
        setLastUpdated(new Date());
        setError(null);
      }
    } catch (err) {
      // Ignore abort errors
      if (err.name === 'AbortError') {
        console.log('Request was cancelled');
        return;
      }

      console.error("Monitor error:", err);
      
      if (isMounted.current) {
        setError(err.message || "Monitoring unavailable");
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, []);

  // =====================================
  // SETUP AUTO-REFRESH
  // =====================================
  useEffect(() => {
    // Set mounted flag
    isMounted.current = true;
    
    // Initial load
    loadMonitor();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      if (isMounted.current) {
        loadMonitor();
      }
    }, 30000);

    // Cleanup function
    return () => {
      isMounted.current = false;
      clearInterval(interval);
      
      // Abort any pending request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [loadMonitor]);

  // =====================================
  // MANUAL REFRESH HANDLER
  // =====================================
  const handleManualRefresh = useCallback(() => {
    loadMonitor();
  }, [loadMonitor]);

  // =====================================
  // HELPER FUNCTIONS
  // =====================================
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
        return '#4ade80'; // green-400
      case 'degraded':
        return '#fb923c'; // orange-400
      case 'unhealthy':
      case 'failed':
        return '#f87171'; // red-400
      default:
        return '#9ca3af'; // gray-400
    }
  };

  const getAiStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'operational':
        return '#4ade80';
      case 'degraded':
        return '#fb923c';
      case 'offline':
        return '#f87171';
      default:
        return '#9ca3af';
    }
  };

  const formatDuration = (seconds) => {
    if (seconds === undefined || seconds === null) return 'N/A';
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    return `${seconds.toFixed(2)}s`;
  };

  // =====================================
  // RENDER LOADING STATE
  // =====================================
  if (loading && !data) {
    return (
      <div
        style={{
          background: "#111",
          color: "white",
          padding: "1.5rem",
          borderRadius: "12px",
          marginTop: "2rem",
          fontFamily: "system-ui, -apple-system, sans-serif",
        }}
      >
        <h3 style={{ margin: "0 0 1rem 0", color: "#e5e7eb" }}>🧠 System Monitor</h3>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <div style={{ 
            width: "20px", 
            height: "20px", 
            border: "2px solid #374151", 
            borderTopColor: "#3b82f6", 
            borderRadius: "50%", 
            animation: "spin 1s linear infinite" 
          }} />
          <span style={{ color: "#9ca3af" }}>Loading monitoring data...</span>
        </div>
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // =====================================
  // RENDER ERROR STATE
  // =====================================
  if (error) {
    return (
      <div
        style={{
          background: "#111",
          color: "white",
          padding: "1.5rem",
          borderRadius: "12px",
          marginTop: "2rem",
          fontFamily: "system-ui, -apple-system, sans-serif",
        }}
      >
        <h3 style={{ margin: "0 0 1rem 0", color: "#e5e7eb" }}>🧠 System Monitor</h3>
        <div style={{ 
          background: "#2d1a1a", 
          borderLeft: "4px solid #ef4444", 
          padding: "1rem",
          borderRadius: "6px"
        }}>
          <p style={{ color: "#fca5a5", margin: "0 0 0.5rem 0" }}>
            <strong>⚠️ Error:</strong> {error}
          </p>
          <button
            onClick={handleManualRefresh}
            style={{
              background: "#374151",
              color: "white",
              border: "none",
              borderRadius: "6px",
              padding: "0.5rem 1rem",
              cursor: "pointer",
              fontSize: "0.9rem",
              marginTop: "0.5rem",
            }}
          >
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  // =====================================
  // RENDER DATA (WITH SAFE ACCESS)
  // =====================================
  const scanner = data?.scanner || {};
  const aiEngine = data?.ai_engine || {};
  const overallStatus = data?.overall_status || 'unknown';
  const apiFailures = data?.api_failures ?? 0;
  const timestamp = data?.timestamp || lastUpdated?.toISOString();

  return (
    <div
      style={{
        background: "#111",
        color: "white",
        padding: "1.5rem",
        borderRadius: "12px",
        marginTop: "2rem",
        fontFamily: "system-ui, -apple-system, sans-serif",
        boxShadow: "0 10px 25px -5px rgba(0,0,0,0.5)",
      }}
    >
      {/* Header with refresh button */}
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center",
        marginBottom: "1.5rem"
      }}>
        <h3 style={{ margin: 0, color: "#e5e7eb", fontSize: "1.25rem" }}>
          🧠 System Monitor
        </h3>
        <button
          onClick={handleManualRefresh}
          disabled={loading}
          style={{
            background: "transparent",
            border: "1px solid #374151",
            color: loading ? "#6b7280" : "#e5e7eb",
            borderRadius: "6px",
            padding: "0.4rem 0.8rem",
            cursor: loading ? "wait" : "pointer",
            fontSize: "0.85rem",
            display: "flex",
            alignItems: "center",
            gap: "0.3rem",
          }}
        >
          <span style={{ 
            display: "inline-block", 
            animation: loading ? "spin 1s linear infinite" : "none" 
          }}>↻</span>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {/* Overall Status */}
      <div style={{ 
        background: "#1a1a1a", 
        padding: "1rem", 
        borderRadius: "8px",
        marginBottom: "1rem"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ color: "#9ca3af" }}>Overall Status:</span>
          <strong style={{ 
            color: getStatusColor(overallStatus),
            textTransform: "uppercase",
            fontSize: "1.1rem"
          }}>
            {overallStatus}
          </strong>
          <span style={{ 
            marginLeft: "auto",
            width: "10px", 
            height: "10px", 
            borderRadius: "50%", 
            background: getStatusColor(overallStatus),
            boxShadow: `0 0 10px ${getStatusColor(overallStatus)}`
          }} />
        </div>
      </div>

      {/* Scanner Stats */}
      <div style={{ 
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "0.75rem",
        marginBottom: "1rem"
      }}>
        <StatCard 
          label="Last Scan Result" 
          value={scanner.last_result || 'N/A'}
          color={scanner.last_result === 'success' ? '#4ade80' : '#f87171'}
        />
        <StatCard 
          label="Last Duration" 
          value={formatDuration(scanner.last_duration)}
        />
        <StatCard 
          label="Scan Failures" 
          value={scanner.failure_count ?? 0}
          warning={(scanner.failure_count ?? 0) > 3}
        />
        <StatCard 
          label="API Failures" 
          value={apiFailures}
          warning={apiFailures > 5}
        />
      </div>

      {/* AI Engine Status */}
      <div style={{ 
        background: "#1a1a1a", 
        padding: "1rem", 
        borderRadius: "8px",
        marginBottom: "1rem"
      }}>
        <h4 style={{ margin: "0 0 0.75rem 0", color: "#d1d5db", fontSize: "1rem" }}>
          🤖 AI Engine
        </h4>
        <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
          <div>
            <span style={{ color: "#9ca3af" }}>Status: </span>
            <strong style={{ color: getAiStatusColor(aiEngine.status) }}>
              {aiEngine.status || 'Unknown'}
            </strong>
          </div>
          <div>
            <span style={{ color: "#9ca3af" }}>OpenAI Key: </span>
            <strong style={{ 
              color: aiEngine.openai_key ? "#4ade80" : "#f87171"
            }}>
              {aiEngine.openai_key ? '✓ Configured' : '✗ Missing'}
            </strong>
          </div>
        </div>
      </div>

      {/* Timestamp and Footer */}
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center",
        fontSize: "0.8rem",
        color: "#6b7280",
        borderTop: "1px solid #1f2937",
        paddingTop: "1rem",
        marginTop: "1rem"
      }}>
        <span>
          Last Updated: {timestamp ? new Date(timestamp).toLocaleString() : 'Never'}
        </span>
        {loading && (
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <div style={{ 
              width: "12px", 
              height: "12px", 
              border: "2px solid #374151", 
              borderTopColor: "#3b82f6", 
              borderRadius: "50%", 
              animation: "spin 1s linear infinite" 
            }} />
            Updating...
          </span>
        )}
      </div>
    </div>
  );
}

// =====================================
// STAT CARD COMPONENT
// =====================================
function StatCard({ label, value, color = "#e5e7eb", warning = false }) {
  return (
    <div style={{ 
      background: "#1a1a1a", 
      padding: "0.75rem", 
      borderRadius: "6px",
      borderLeft: warning ? "3px solid #f87171" : "none"
    }}>
      <div style={{ color: "#9ca3af", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
        {label}
      </div>
      <div style={{ 
        color: warning ? "#f87171" : color, 
        fontWeight: "600", 
        fontSize: "1.1rem" 
      }}>
        {value}
        {warning && <span style={{ marginLeft: "0.5rem", fontSize: "0.8rem" }}>⚠️</span>}
      </div>
    </div>
  );
}