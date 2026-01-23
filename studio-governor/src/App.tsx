import { useEffect, useState, useCallback } from "react";
import { TerminalView } from "./components/Terminal";
import { FileExplorer } from "./components/FileExplorer";
import { FileViewer } from "./components/FileViewer";
import { SourcesList } from "./components/SourcesList";
import { TaskBoard } from "./components/TaskBoard";
import { AgentFeed } from "./components/AgentFeed";

import { api } from "./lib/api";
import { useWebContainer } from "./lib/useWebContainer";
import {
  LayoutDashboard,
  Terminal as TerminalIcon,
  Files,
  Activity,
  Settings,
  ShieldCheck,
  Cpu,
  Database,
  Search,
} from "lucide-react";
import "./index.css";

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedFile, setSelectedFile] = useState<{
    path: string;
    content: string;
  } | null>(null);
  const [activeTab, setActiveTab] = useState<
    "explorer" | "research" | "metrics" | "governance"
  >("explorer");
  const [memDaemonStatus, setMemDaemonStatus] = useState<"ONLINE" | "OFFLINE">(
    "OFFLINE"
  );

  // Use the extracted WebContainer hook
  const { status, queueSize, handleInput, terminalRef } = useWebContainer({
    onRefresh: () => setRefreshTrigger((prev) => prev + 1),
  });

  // Memory daemon status polling
  useEffect(() => {
    const checkStatus = async () => {
      try {
        await api.getState();
        setMemDaemonStatus("ONLINE");
      } catch {
        setMemDaemonStatus("OFFLINE");
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleFileSelect = useCallback(async (path: string) => {
    try {
      const data = await api.readFile(path);
      setSelectedFile(data);
    } catch (err) {
      console.error(`Error reading file: ${err}`);
    }
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-white selection:bg-primary/30">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-surface flex flex-col z-10">
        <div className="p-6 border-b border-border flex items-center space-x-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <LayoutDashboard className="w-5 h-5 text-primary" />
          </div>
          <h2 className="text-sm font-bold tracking-tight uppercase">
            Studio Mode
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto py-6">
          <div className="px-6 mb-8">
            <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4">
              Navigation
            </div>
            <nav className="space-y-1">
              {[
                { id: "explorer", icon: Files, label: "Explorer" },
                { id: "research", icon: Search, label: "Research" },
                { id: "metrics", icon: Activity, label: "Metrics" },
                { id: "governance", icon: ShieldCheck, label: "Governance" },
              ].map((item) => (
                <div
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-md text-xs cursor-pointer transition-colors ${
                    activeTab === item.id
                      ? "bg-primary/10 text-primary"
                      : "text-gray-400 hover:text-white hover:bg-white/5"
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
              ))}
            </nav>
          </div>

          <div className="px-6 h-1/2 flex flex-col">
            {activeTab === "explorer" ? (
              <FileExplorer
                refreshTrigger={refreshTrigger}
                onFileSelect={handleFileSelect}
              />
            ) : activeTab === "research" ? (
              <SourcesList />
            ) : activeTab === "metrics" ? (
              <TaskBoard />
            ) : (
              <div className="text-[10px] text-gray-500 italic px-2">
                Panel under construction.
              </div>
            )}
          </div>
        </div>

        <div className="p-4 border-t border-border space-y-3">
          <div className="flex items-center justify-between text-[10px] text-gray-500">
            <span>MEM DAEMON</span>
            <span
              className={`${
                memDaemonStatus === "ONLINE" ? "text-secondary" : "text-red-500"
              } font-bold transition-colors`}
            >
              {memDaemonStatus}
            </span>
          </div>
          <div className="h-1 bg-border rounded-full overflow-hidden">
            <div
              className={`h-full ${
                memDaemonStatus === "ONLINE"
                  ? "bg-secondary opacity-50"
                  : "bg-red-500 opacity-20"
              } w-full`}
            />
          </div>
        </div>
      </aside>

      {/* Main Panel */}
      <main className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="h-16 border-b border-border bg-surface/50 backdrop-blur-md flex items-center justify-between px-8 z-10">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  status === "ready"
                    ? "bg-secondary"
                    : status === "error"
                    ? "bg-red-500"
                    : "bg-accent animate-pulse"
                }`}
              />
              <span className="text-xs font-bold uppercase tracking-wider">
                {status}
              </span>
            </div>
            <div className="h-4 w-[1px] bg-border" />
            <div className="flex items-center space-x-4 text-[10px] font-mono text-gray-500">
              <div className="flex items-center space-x-1">
                <Cpu className="w-3 h-3" />
                <span>CPU: OK</span>
              </div>
              <div className="flex items-center space-x-1">
                <Database className="w-3 h-3" />
                <span>VFS: MOUNTED</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {queueSize > 0 && (
              <div className="flex items-center space-x-2 px-3 py-1 bg-primary/10 border border-primary/20 rounded-full">
                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-ping" />
                <span className="text-[10px] font-bold text-primary font-mono">
                  THROTTLE: {queueSize}
                </span>
              </div>
            )}
            <Settings className="w-4 h-4 text-gray-500 hover:text-white cursor-pointer transition-colors" />
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Terminal Section */}
          <section className="flex-1 flex flex-col p-6 overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                {selectedFile ? (
                  <>
                    <Files className="w-4 h-4 text-primary" />
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
                      File Preview
                    </span>
                  </>
                ) : (
                  <>
                    <TerminalIcon className="w-4 h-4 text-primary" />
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
                      Governance Shell
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-hidden">
              {selectedFile ? (
                <FileViewer
                  path={selectedFile.path}
                  content={selectedFile.content}
                  onClose={() => setSelectedFile(null)}
                />
              ) : (
                <div className="h-full bg-black/50 rounded-xl border border-border overflow-hidden p-4 shadow-2xl backdrop-blur-sm">
                  <TerminalView
                    onData={handleInput}
                    terminalRef={terminalRef}
                  />
                </div>
              )}
            </div>
          </section>

          {/* Activity/Logs Section */}
          <section className="w-80 border-l border-border bg-surface/30 backdrop-blur-sm flex flex-col">
            <AgentFeed />
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
