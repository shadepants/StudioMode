import { Cpu, Zap } from "lucide-react";

interface MissionHeaderProps {
  systemState: "online" | "offline" | "executing" | "idle";
  uptime: string;
}

export function MissionHeader({ systemState, uptime }: MissionHeaderProps) {
  const stateConfig = {
    online: {
      label: "ONLINE",
      color: "var(--accent-green)",
      className: "status-online",
    },
    executing: {
      label: "EXECUTING",
      color: "var(--accent-cyan)",
      className: "status-executing",
    },
    idle: {
      label: "IDLE",
      color: "var(--accent-amber)",
      className: "status-idle",
    },
    offline: {
      label: "OFFLINE",
      color: "var(--accent-red)",
      className: "status-offline",
    },
  };

  const state = stateConfig[systemState];

  return (
    <header className="mission-header">
      <div className="mission-title">
        <Cpu className="w-6 h-6 text-[var(--accent-cyan)]" />
        <div>
          <h1>Mission Control</h1>
          <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-widest">
            The Governed HiVE
          </span>
        </div>
      </div>

      <div className="mission-status">
        <div className="flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${state.className}`}
          ></span>
          <span
            className="text-xs font-semibold uppercase tracking-wider"
            style={{ color: state.color }}
          >
            {state.label}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-[var(--text-muted)]">
          <Zap className="w-3.5 h-3.5" />
          <span className="uptime-display">{uptime}</span>
        </div>
      </div>
    </header>
  );
}
