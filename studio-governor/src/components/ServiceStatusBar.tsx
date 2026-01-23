import { useEffect, useState, useCallback } from "react";
import { Database, Cpu, Search, Eye, RefreshCw } from "lucide-react";
import { api } from "../lib/api";

interface ServiceStatus {
  name: string;
  port: number;
  icon: React.ReactNode;
  status: "online" | "idle" | "offline" | "executing";
  responseTime?: number;
}

interface ServiceCardProps {
  service: ServiceStatus;
}

function ServiceCard({ service }: ServiceCardProps) {
  const statusColors = {
    online: "status-online",
    idle: "status-idle",
    offline: "status-offline",
    executing: "status-executing",
  };

  const statusLabels = {
    online: "Online",
    idle: "Idle",
    offline: "Offline",
    executing: "Executing",
  };

  return (
    <div className="service-card glass-panel-hover">
      <div className="icon-container">
        <span className="service-icon text-[var(--accent-cyan)]">
          {service.icon}
        </span>
        <span className="service-name">{service.name}</span>
      </div>
      <span className="port-badge">:{service.port}</span>
      <div className="status-row">
        <span className={`status-dot ${statusColors[service.status]}`}></span>
        <span
          className="status-text"
          style={{
            color:
              service.status === "online"
                ? "var(--accent-green)"
                : service.status === "executing"
                ? "var(--accent-cyan)"
                : service.status === "idle"
                ? "var(--accent-amber)"
                : "var(--accent-red)",
          }}
        >
          {statusLabels[service.status]}
        </span>
        {service.responseTime && (
          <span className="text-[10px] text-[var(--text-muted)] ml-auto">
            {service.responseTime}ms
          </span>
        )}
      </div>
    </div>
  );
}

export function ServiceStatusBar() {
  const [services, setServices] = useState<ServiceStatus[]>([
    {
      name: "Memory",
      port: 8000,
      icon: <Database className="w-5 h-5" />,
      status: "offline",
    },
    {
      name: "Engineer",
      port: 8001,
      icon: <Cpu className="w-5 h-5" />,
      status: "offline",
    },
    {
      name: "Critic",
      port: 8002,
      icon: <Eye className="w-5 h-5" />,
      status: "offline",
    },
    {
      name: "Scout",
      port: 8003,
      icon: <Search className="w-5 h-5" />,
      status: "offline",
    },
  ]);
  const [lastCheck, setLastCheck] = useState<Date>(new Date());

  const checkServices = useCallback(async () => {
    const updatedServices = await Promise.all(
      services.map(async (service) => {
        try {
          const checkStart = Date.now();
          const stateData = await api.checkServiceHealth(service.port);
          const responseTime = Date.now() - checkStart;

          const state = stateData.current_state?.toLowerCase() || "online";

          return {
            ...service,
            status:
              state === "executing"
                ? ("executing" as const)
                : state === "idle"
                ? ("idle" as const)
                : ("online" as const),
            responseTime,
          };
        } catch {
          return { ...service, status: "offline" as const };
        }
      })
    );

    setServices(updatedServices);
    setLastCheck(new Date());
  }, [services]);

  useEffect(() => {
    checkServices();
    const interval = setInterval(checkServices, 5000); // Check every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const onlineCount = services.filter((s) => s.status !== "offline").length;

  return (
    <div className="p-4 border-b border-[var(--border-default)] bg-[var(--bg-secondary)]">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
            Service Status
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
            {onlineCount}/{services.length} online
          </span>
        </div>
        <button
          onClick={checkServices}
          className="flex items-center gap-1 text-[10px] text-[var(--text-muted)] hover:text-[var(--accent-cyan)] transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          <span>{lastCheck.toLocaleTimeString()}</span>
        </button>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-2">
        {services.map((service) => (
          <ServiceCard key={service.name} service={service} />
        ))}
      </div>
    </div>
  );
}
