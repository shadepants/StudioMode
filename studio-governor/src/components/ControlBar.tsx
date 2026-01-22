import { useState, useCallback } from "react";
import {
  Play,
  Square,
  Plus,
  RefreshCw,
  Terminal,
  Settings,
} from "lucide-react";
import { api } from "../lib/api";

interface ControlBarProps {
  onRefresh?: () => void;
}

export function ControlBar({ onRefresh }: ControlBarProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [showAddTask, setShowAddTask] = useState(false);
  const [taskText, setTaskText] = useState("");
  const [statusMessage, setStatusMessage] = useState<{
    text: string;
    type: "success" | "error";
  } | null>(null);

  const showStatus = (text: string, type: "success" | "error") => {
    setStatusMessage({ text, type });
    setTimeout(() => setStatusMessage(null), 3000);
  };

  const handleStart = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.updateState("EXECUTING");
      if (res.ok) {
        showStatus("Hive started!", "success");
      } else {
        showStatus("Failed to start", "error");
      }
    } catch {
      showStatus("Connection failed", "error");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleStop = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.updateState("IDLE");
      if (res.ok) {
        showStatus("Hive stopped", "success");
      } else {
        showStatus("Failed to stop", "error");
      }
    } catch {
      showStatus("Connection failed", "error");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleAddTask = useCallback(async () => {
    if (!taskText.trim()) return;

    setIsLoading(true);
    try {
      const res = await api.createTask({
        text: taskText,
        assignee: "gemini-cli",
        priority: "normal",
      });
      if (res.ok) {
        showStatus("Task created!", "success");
        setTaskText("");
        setShowAddTask(false);
        onRefresh?.();
      } else {
        showStatus("Failed to create task", "error");
      }
    } catch {
      showStatus("Connection failed", "error");
    } finally {
      setIsLoading(false);
    }
  }, [taskText, onRefresh]);

  return (
    <div className="glass-panel p-3">
      <div className="flex items-center gap-3 flex-wrap">
        {/* Control Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleStart}
            disabled={isLoading}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            <span>Start</span>
          </button>

          <button
            onClick={handleStop}
            disabled={isLoading}
            className="btn-secondary flex items-center gap-2 disabled:opacity-50"
          >
            <Square className="w-4 h-4" />
            <span>Stop</span>
          </button>
        </div>

        {/* Divider */}
        <div className="w-px h-6 bg-[var(--border-default)]"></div>

        {/* Add Task */}
        {!showAddTask ? (
          <button
            onClick={() => setShowAddTask(true)}
            className="btn-secondary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>Add Task</span>
          </button>
        ) : (
          <div className="flex items-center gap-2 flex-1 max-w-md">
            <input
              type="text"
              value={taskText}
              onChange={(e) => setTaskText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddTask()}
              placeholder="Describe the task..."
              className="flex-1 px-3 py-1.5 text-sm bg-[var(--bg-tertiary)] border border-[var(--border-default)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:border-[var(--accent-cyan)] focus:outline-none transition-colors"
              autoFocus
            />
            <button
              onClick={handleAddTask}
              disabled={isLoading || !taskText.trim()}
              className="btn-primary px-3 disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                setShowAddTask(false);
                setTaskText("");
              }}
              className="btn-secondary px-2"
            >
              ✕
            </button>
          </div>
        )}

        {/* Spacer */}
        <div className="flex-1"></div>

        {/* Right Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="btn-secondary p-2"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button className="btn-secondary p-2" title="Open Terminal">
            <Terminal className="w-4 h-4" />
          </button>

          <button className="btn-secondary p-2" title="Settings">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Status Message */}
      {statusMessage && (
        <div
          className={`mt-2 text-xs px-3 py-1.5 rounded-lg ${
            statusMessage.type === "success"
              ? "bg-[var(--accent-green)]/10 text-[var(--accent-green)] border border-[var(--accent-green)]/20"
              : "bg-[var(--accent-red)]/10 text-[var(--accent-red)] border border-[var(--accent-red)]/20"
          }`}
        >
          {statusMessage.text}
        </div>
      )}
    </div>
  );
}
