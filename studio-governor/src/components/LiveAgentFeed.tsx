import { useEffect, useState, useRef, useCallback } from "react";
import {
  Activity,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Clock,
  MessageSquare,
} from "lucide-react";
import { api } from "../lib/api";

interface FeedEvent {
  id: string;
  text: string;
  type: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

interface TaskEvent {
  id: string;
  text: string;
  status: string;
  assignee: string;
  created_at: string;
}

export function LiveAgentFeed() {
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [tasks, setTasks] = useState<TaskEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const feedRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket connection for real-time updates
  const connectWebSocket = useCallback(() => {
    try {
      // For now, fall back to polling since WS may not be available
      setIsConnected(true);
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      setIsConnected(false);
    }
  }, []);

  // Fast polling for real-time feel (1 second)
  const fetchFeed = useCallback(async () => {
    try {
      const [feedData, tasksData] = await Promise.all([
        api.getFeed(30),
        api.getTasks({}), // Fetch all for summary, or limit if API supported it
      ]);

      setEvents((prev) => {
        // Only update if there's new data
        if (JSON.stringify(prev) !== JSON.stringify(feedData)) {
          return feedData;
        }
        return prev;
      });

      setTasks(tasksData.tasks || []);

      setIsConnected(true);
      setLastUpdate(new Date());
    } catch (err) {
      console.error("Feed fetch error:", err);
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    connectWebSocket();
    fetchFeed();

    // Fast polling for real-time updates
    const interval = setInterval(fetchFeed, 1000);
    return () => {
      clearInterval(interval);
      wsRef.current?.close();
    };
  }, [connectWebSocket, fetchFeed]);

  // Auto-scroll to bottom on new events
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [events]);

  const formatTime = (ts: number | string) => {
    const date = typeof ts === "number" ? new Date(ts * 1000) : new Date(ts);
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const getEventIcon = (text: string, type: string) => {
    if (text.includes("Error") || text.includes("Failed")) {
      return <AlertTriangle className="w-3 h-3 text-[var(--accent-red)]" />;
    }
    if (
      text.includes("Complete") ||
      text.includes("Success") ||
      type.includes("complete")
    ) {
      return <CheckCircle2 className="w-3 h-3 text-[var(--accent-green)]" />;
    }
    if (text.includes("claimed") || text.includes("Executing")) {
      return <Zap className="w-3 h-3 text-[var(--accent-cyan)]" />;
    }
    return <MessageSquare className="w-3 h-3 text-[var(--accent-purple)]" />;
  };

  return (
    <div className="flex flex-col h-full glass-panel">
      {/* Header */}
      <div className="p-4 border-b border-[var(--border-default)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[var(--accent-cyan)]" />
          <span className="text-xs font-bold uppercase tracking-wider">
            Live Activity
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? "status-online" : "status-offline"
            }`}
          ></span>
          <span className="text-[10px] text-[var(--text-muted)]">
            {isConnected ? "LIVE" : "OFFLINE"}
          </span>
          <span className="text-[10px] bg-[var(--bg-tertiary)] px-1.5 py-0.5 rounded text-[var(--text-muted)]">
            {events.length} events
          </span>
        </div>
      </div>

      {/* Recent Tasks Quick View */}
      {tasks.length > 0 && (
        <div className="p-3 border-b border-[var(--border-default)] bg-[var(--bg-tertiary)]/50">
          <div className="text-[10px] text-[var(--text-muted)] mb-2 uppercase tracking-wider">
            Recent Tasks
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {tasks.slice(0, 5).map((task) => (
              <div
                key={task.id}
                className="flex-shrink-0 px-2 py-1 rounded text-[10px] bg-[var(--bg-secondary)] border border-[var(--border-default)]"
              >
                <span
                  className={`inline-block w-1.5 h-1.5 rounded-full mr-1 ${
                    task.status === "completed"
                      ? "bg-[var(--accent-green)]"
                      : task.status === "in_progress"
                      ? "bg-[var(--accent-cyan)]"
                      : "bg-[var(--accent-amber)]"
                  }`}
                ></span>
                <span className="text-[var(--text-secondary)] truncate max-w-[120px] inline-block align-middle">
                  {task.text.substring(0, 25)}...
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Event Feed */}
      <div ref={feedRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {events.length === 0 && (
          <div className="text-center text-xs text-[var(--text-muted)] mt-10">
            <Clock className="w-5 h-5 mx-auto mb-2 opacity-50" />
            Waiting for activity...
          </div>
        )}

        {events.map((event, index) => (
          <div
            key={event.id || index}
            className="feed-item-enter group relative pl-4 border-l-2 border-[var(--border-default)] hover:border-[var(--accent-cyan)] transition-all duration-200"
          >
            {/* Timeline dot */}
            <div className="absolute -left-[5px] top-0 w-2 h-2 bg-[var(--bg-tertiary)] border border-[var(--border-default)] rounded-full group-hover:border-[var(--accent-cyan)] group-hover:bg-[var(--accent-cyan)] transition-colors"></div>

            {/* Time and icon */}
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-mono text-[var(--text-muted)]">
                {formatTime(event.timestamp)}
              </span>
              {getEventIcon(event.text, event.type)}
            </div>

            {/* Event text */}
            <div className="text-[11px] text-[var(--text-secondary)] leading-relaxed font-mono">
              {event.text}
            </div>

            {/* Metadata tags */}
            {event.metadata && Object.keys(event.metadata).length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {event.metadata.new_state && (
                  <span className="text-[9px] px-1.5 py-0.5 bg-[var(--accent-cyan)]/10 text-[var(--accent-cyan)] rounded border border-[var(--accent-cyan)]/20">
                    → {String(event.metadata.new_state)}
                  </span>
                )}
                {event.metadata.agent_id && (
                  <span className="text-[9px] px-1.5 py-0.5 bg-[var(--bg-tertiary)] text-[var(--text-muted)] rounded">
                    @{String(event.metadata.agent_id)}
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="p-2 border-t border-[var(--border-default)] text-[9px] text-[var(--text-muted)] text-center">
        Last update: {lastUpdate.toLocaleTimeString()}
      </div>
    </div>
  );
}
