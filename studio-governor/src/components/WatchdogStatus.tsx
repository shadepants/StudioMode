import { useEffect, useState, useCallback } from "react";
import { Shield, AlertTriangle, CheckCircle, RefreshCw } from "lucide-react";

interface HealthStatus {
  status: "healthy" | "degraded" | "critical";
  services_online: number;
  services_total: number;
  recent_alerts: Array<{
    timestamp: number;
    level: string;
    service: string;
    message: string;
  }>;
}

export function WatchdogStatus() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const runHealthCheck = useCallback(async () => {
    setIsLoading(true);
    try {
      // Call the watchdog check endpoint (we'll simulate with /metrics for now)
      const res = await fetch("http://localhost:8000/metrics");
      if (res.ok) {
        const data = await res.json();
        // Derive health from metrics
        setHealth({
          status:
            data.system.state === "EXECUTING"
              ? "healthy"
              : data.tasks.failed > 0
              ? "degraded"
              : "healthy",
          services_online: 1, // Memory server is online
          services_total: 4,
          recent_alerts: [],
        });
      }
    } catch {
      setHealth({
        status: "critical",
        services_online: 0,
        services_total: 4,
        recent_alerts: [
          {
            timestamp: Date.now() / 1000,
            level: "error",
            service: "Memory Server",
            message: "Connection failed",
          },
        ],
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    runHealthCheck();
    const interval = setInterval(runHealthCheck, 10000);
    return () => clearInterval(interval);
  }, [runHealthCheck]);

  const statusConfig = {
    healthy: {
      color: "var(--accent-green)",
      icon: <CheckCircle className="w-4 h-4" />,
      label: "All Systems Operational",
    },
    degraded: {
      color: "var(--accent-amber)",
      icon: <AlertTriangle className="w-4 h-4" />,
      label: "Some Issues Detected",
    },
    critical: {
      color: "var(--accent-red)",
      icon: <AlertTriangle className="w-4 h-4" />,
      label: "Critical Issues",
    },
  };

  const config = health ? statusConfig[health.status] : statusConfig.critical;

  return (
    <div className="glass-panel p-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Shield className="w-5 h-5" style={{ color: config.color }} />
        <div>
          <div className="flex items-center gap-2">
            {config.icon}
            <span
              className="text-sm font-medium"
              style={{ color: config.color }}
            >
              {config.label}
            </span>
          </div>
          {health && (
            <span className="text-[10px] text-[var(--text-muted)]">
              {health.services_online}/{health.services_total} services online
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {health?.recent_alerts && health.recent_alerts.length > 0 && (
          <span className="text-[10px] px-2 py-1 rounded bg-[var(--accent-amber)]/10 text-[var(--accent-amber)]">
            {health.recent_alerts.length} alerts
          </span>
        )}

        <button
          onClick={runHealthCheck}
          disabled={isLoading}
          className="btn-secondary p-2"
          title="Run Health Check"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>
    </div>
  );
}
