import { useEffect, useState, useCallback, useRef } from "react";
import {
  TrendingUp,
  Clock,
  Zap,
  Hash,
  Activity,
  Users,
  AlertCircle,
} from "lucide-react";

interface ServerMetrics {
  tasks: {
    total: number;
    completed: number;
    in_progress: number;
    pending: number;
    failed: number;
  };
  agents: {
    total: number;
    active: number;
  };
  performance: {
    avg_duration_seconds: number;
    recent_activity: number;
  };
  system: {
    uptime_seconds: number;
    state: string;
  };
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  suffix?: string;
  trend?: "up" | "down" | "neutral";
  color?: string;
  subValue?: string;
}

function MetricCard({
  icon,
  label,
  value,
  suffix,
  color = "var(--accent-cyan)",
  subValue,
}: MetricCardProps) {
  const [isFlashing, setIsFlashing] = useState(false);
  const prevValueRef = useRef(value);

  useEffect(() => {
    if (value !== prevValueRef.current) {
      setIsFlashing(true);
      prevValueRef.current = value;
      const timer = setTimeout(() => setIsFlashing(false), 500);
      return () => clearTimeout(timer);
    }
  }, [value]);

  return (
    <div className="glass-panel p-4 flex flex-col gap-2 min-w-[120px] glass-panel-hover">
      <div className="flex items-center gap-2 text-[var(--text-muted)]">
        {icon}
        <span className="text-[10px] uppercase tracking-wider">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span
          className={`text-xl font-bold font-mono ${
            isFlashing ? "metric-flash" : ""
          }`}
          style={{ color }}
        >
          {typeof value === "number" ? value.toLocaleString() : value}
        </span>
        {suffix && (
          <span className="text-[10px] text-[var(--text-muted)]">{suffix}</span>
        )}
      </div>
      {subValue && (
        <span className="text-[9px] text-[var(--text-muted)]">{subValue}</span>
      )}
    </div>
  );
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

export function MetricsPanel() {
  const [metrics, setMetrics] = useState<ServerMetrics | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await fetch("http://localhost:8000/metrics");
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
        setIsConnected(true);
        setLastUpdate(new Date());
      } else {
        setIsConnected(false);
      }
    } catch {
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 2000); // Fast 2-second polling
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  // Fallback values if no connection
  const tasks = metrics?.tasks ?? {
    total: 0,
    completed: 0,
    in_progress: 0,
    pending: 0,
    failed: 0,
  };
  const agents = metrics?.agents ?? { total: 0, active: 0 };
  const performance = metrics?.performance ?? {
    avg_duration_seconds: 0,
    recent_activity: 0,
  };
  const system = metrics?.system ?? { uptime_seconds: 0, state: "OFFLINE" };

  return (
    <div className="glass-panel p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[var(--accent-cyan)]" />
          <span className="text-xs font-bold uppercase tracking-wider">
            System Metrics
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? "status-online" : "status-offline"
            }`}
          ></span>
          <span className="text-[10px] text-[var(--text-muted)]">
            {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-3">
        <MetricCard
          icon={<Hash className="w-3.5 h-3.5" />}
          label="Total Tasks"
          value={tasks.total}
          color="var(--accent-cyan)"
          subValue={`${tasks.pending} pending`}
        />
        <MetricCard
          icon={<Zap className="w-3.5 h-3.5" />}
          label="Completed"
          value={tasks.completed}
          color="var(--accent-green)"
          subValue={
            tasks.total > 0
              ? `${Math.round((tasks.completed / tasks.total) * 100)}%`
              : "0%"
          }
        />
        <MetricCard
          icon={<Activity className="w-3.5 h-3.5" />}
          label="In Progress"
          value={tasks.in_progress}
          color="var(--accent-amber)"
        />
        <MetricCard
          icon={<AlertCircle className="w-3.5 h-3.5" />}
          label="Failed"
          value={tasks.failed}
          color="var(--accent-red)"
        />
        <MetricCard
          icon={<Clock className="w-3.5 h-3.5" />}
          label="Avg Duration"
          value={performance.avg_duration_seconds.toFixed(1)}
          suffix="s"
          color="var(--accent-purple)"
        />
        <MetricCard
          icon={<Users className="w-3.5 h-3.5" />}
          label="Agents"
          value={agents.active}
          color="var(--accent-blue)"
          subValue={`${agents.total} total`}
        />
        <MetricCard
          icon={<TrendingUp className="w-3.5 h-3.5" />}
          label="Uptime"
          value={formatUptime(system.uptime_seconds)}
          color="var(--accent-green)"
          subValue={system.state}
        />
      </div>
    </div>
  );
}
