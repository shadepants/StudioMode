/**
 * Studio Mode - Centralized API Client
 * ====================================
 * Single source of truth for all API calls to the backend.
 * Replaces hardcoded URLs in components.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface Task {
  id: string;
  text: string;
  assignee: string;
  status: "pending" | "in_progress" | "completed" | "failed" | "review";
  priority: "low" | "normal" | "high";
  created_at: number;
  updated_at: number;
  claimed_by?: string;
  metadata?: any;
}

export interface Agent {
  agent_id: string;
  agent_type: string;
  status: "online" | "offline";
  last_heartbeat: number;
  capabilities: string[];
}

export const api = {
  // --- System State ---
  checkServiceHealth: async (port: number) => {
    // Allow checking specific service ports directly
    const baseUrl = API_BASE.replace(/:\d+$/, `:${port}`);
    try {
      const res = await fetch(`${baseUrl}/state`, {
        signal: AbortSignal.timeout(2000),
      });
      if (res.ok) return await res.json();
    } catch {
      // Fallback to health endpoint
      const res = await fetch(`${baseUrl}/health`, {
        signal: AbortSignal.timeout(1000),
      });
      if (res.ok) return { current_state: "online" };
    }
    throw new Error("Service unreachable");
  },

  getState: async () => {
    const res = await fetch(`${API_BASE}/state`);
    return res.json();
  },

  updateState: async (newState: string) => {
    const res = await fetch(`${API_BASE}/state/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_state: newState }),
    });
    return res.json();
  },

  // --- Tasks ---
  getTasks: async (filters: { status?: string; assignee?: string } = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append("status", filters.status);
    if (filters.assignee) params.append("assignee", filters.assignee);

    const res = await fetch(`${API_BASE}/tasks/list?${params.toString()}`);
    return res.json();
  },

  createTask: async (task: {
    text: string;
    assignee: string;
    priority?: string;
  }) => {
    const res = await fetch(`${API_BASE}/tasks/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(task),
    });
    return res.json();
  },

  // --- Sources ---
  getSources: async (limit: number = 50) => {
    const res = await fetch(`${API_BASE}/sources?limit=${limit}`);
    return res.json();
  },

  addSource: async (source: any) => {
    const res = await fetch(`${API_BASE}/sources/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(source),
    });
    return res.json();
  },

  getGraph: async () => {
    const res = await fetch(`${API_BASE}/knowledge/graph`);
    return res.json();
  },

  // --- Agents ---
  getAgents: async () => {
    const res = await fetch(`${API_BASE}/agents/list`);
    return res.json();
  },

  // --- Memory / Feed ---
  getFeed: async (limit: number = 20) => {
    const res = await fetch(`${API_BASE}/memory/feed?limit=${limit}`);
    return res.json();
  },

  // --- Metrics ---
  getMetrics: async () => {
    const res = await fetch(`${API_BASE}/metrics`);
    return res.json();
  },

  // --- File System ---
  readDir: async (path: string = "") => {
    const res = await fetch(
      `${API_BASE}/fs/list?path=${encodeURIComponent(path)}`
    );
    return res.json();
  },

  readFile: async (path: string) => {
    const res = await fetch(
      `${API_BASE}/fs/read?path=${encodeURIComponent(path)}`
    );
    return res.json();
  },
};
