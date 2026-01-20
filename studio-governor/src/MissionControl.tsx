import { useState, useEffect, useCallback } from "react";
import { MissionHeader } from "./components/MissionHeader";
import { ServiceStatusBar } from "./components/ServiceStatusBar";
import { LiveAgentFeed } from "./components/LiveAgentFeed";
import { MetricsPanel } from "./components/MetricsPanel";
import { ControlBar } from "./components/ControlBar";
import { TaskBoard } from "./components/TaskBoard";
import { WatchdogStatus } from "./components/WatchdogStatus";
import "./index.css";

type SystemState = "online" | "offline" | "executing" | "idle";

function MissionControl() {
  const [systemState, setSystemState] = useState<SystemState>("offline");
  const [uptime, setUptime] = useState("0h 0m");
  const [startTime] = useState<Date>(new Date());
  const [refreshKey, setRefreshKey] = useState(0);

  // Fetch system state
  const fetchSystemState = useCallback(async () => {
    try {
      const res = await fetch("http://localhost:8000/state");
      if (res.ok) {
        const data = await res.json();
        const state = data.current_state?.toUpperCase() || "IDLE";
        setSystemState(
          state === "EXECUTING"
            ? "executing"
            : state === "IDLE"
            ? "idle"
            : "online"
        );
      } else {
        setSystemState("offline");
      }
    } catch {
      setSystemState("offline");
    }
  }, []);

  // Calculate uptime
  const updateUptime = useCallback(() => {
    const now = new Date();
    const diff = now.getTime() - startTime.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    setUptime(`${hours}h ${minutes}m ${seconds}s`);
  }, [startTime]);

  useEffect(() => {
    // Initial fetch
    fetchSystemState();
    updateUptime();

    // Fast state polling (2 seconds)
    const stateInterval = setInterval(fetchSystemState, 2000);
    // Update uptime every second
    const uptimeInterval = setInterval(updateUptime, 1000);

    return () => {
      clearInterval(stateInterval);
      clearInterval(uptimeInterval);
    };
  }, [fetchSystemState, updateUptime]);

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
    fetchSystemState();
  };

  return (
    <div className="h-full flex flex-col bg-[var(--bg-primary)]">
      {/* Header */}
      <MissionHeader systemState={systemState} uptime={uptime} />

      {/* Service Status Bar */}
      <ServiceStatusBar />

      {/* Control Bar */}
      <div className="p-4 pb-0">
        <ControlBar onRefresh={handleRefresh} />
      </div>

      {/* Metrics Panel */}
      <div className="p-4 pb-0">
        <MetricsPanel key={`metrics-${refreshKey}`} />
      </div>

      {/* Watchdog Status */}
      <div className="px-4 pt-3">
        <WatchdogStatus />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-4 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
        {/* Left: Task Board */}
        <div className="min-h-0 overflow-hidden">
          <TaskBoard />
        </div>

        {/* Right: Live Agent Feed */}
        <div className="min-h-0 overflow-hidden">
          <LiveAgentFeed key={`feed-${refreshKey}`} />
        </div>
      </div>
    </div>
  );
}

export default MissionControl;
