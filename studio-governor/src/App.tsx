import { useEffect, useRef, useState } from 'react';
import { WebContainer } from '@webcontainer/api';
import { Terminal } from 'xterm';
import { TerminalView } from './components/Terminal';
import { FileExplorer } from './components/FileExplorer';
import { FileViewer } from './components/FileViewer';
import { SourcesList } from './components/SourcesList';
import { TaskBoard } from './components/TaskBoard';
import { AgentFeed } from './components/AgentFeed';
import { CommandQueue } from './lib/Throttler';
import { 
  LayoutDashboard, 
  Terminal as TerminalIcon, 
  Files, 
  Activity, 
  Settings, 
  ShieldCheck,
  Cpu,
  Database,
  Search
} from 'lucide-react';

// @ts-ignore
import agentSource from './files/agent.js?raw';
// @ts-ignore
import packageJsonSource from './files/package.json?raw';
import './index.css';

function App() {
  const [status, setStatus] = useState<'booting' | 'installing' | 'ready' | 'error'>('booting');
  const [queueSize, setQueueSize] = useState(0);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedFile, setSelectedFile] = useState<{ path: string, content: string } | null>(null);
  const [activeTab, setActiveTab] = useState<'explorer' | 'research'>('explorer');
  
  const terminalRef = useRef<Terminal | null>(null);
  const containerRef = useRef<WebContainer | null>(null);
  const processRef = useRef<any>(null);
  const queueRef = useRef<CommandQueue | null>(null);

  const [memDaemonStatus, setMemDaemonStatus] = useState<'ONLINE' | 'OFFLINE'>('OFFLINE');
  
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/');
        if (res.ok) setMemDaemonStatus('ONLINE');
        else setMemDaemonStatus('OFFLINE');
      } catch {
        setMemDaemonStatus('OFFLINE');
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const addLog = (msg: string, type: 'info' | 'warn' | 'success' = 'info') => {
    console.log(`[${type}] ${msg}`);
    if (terminalRef.current) {
        const color = type === 'warn' ? '\x1b[31m' : type === 'success' ? '\x1b[32m' : '\x1b[90m';
        // Only write important logs to terminal to avoid clutter
        if (type !== 'info' || msg.includes('Booting') || msg.includes('Ready')) {
            terminalRef.current.write(`\r\n${color}[SYS] ${msg}\x1b[0m\r\n`);
        }
    }
  };

  const handleInput = (data: string) => {
    queueRef.current?.enqueue(data);
  };

  const handleFileSelect = async (path: string) => {
    try {
      addLog(`Reading ${path}...`, 'info');
      const res = await fetch(`http://localhost:8000/fs/read?path=${encodeURIComponent(path)}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedFile(data);
      } else {
        addLog(`Failed to read file: ${res.statusText}`, 'warn');
      }
    } catch (err) {
      addLog(`Error reading file: ${err}`, 'warn');
    }
  };

  useEffect(() => {
    queueRef.current = new CommandQueue(
      async (command: string) => {
        const process = processRef.current;
        if (!process) return;
        const writer = process.input.getWriter();
        await writer.write(command);
        writer.releaseLock();
      },
      (size) => setQueueSize(size),
      50
    );

    let isMounted = true;

    async function boot() {
      if (containerRef.current) return;
      
      // Allow terminal to mount
      await new Promise(r => setTimeout(r, 100));
      
      try {
        const term = terminalRef.current;
        if (!term || !isMounted) return;

        // --- PRE-FLIGHT CHECKS ---
        addLog('Starting Pre-flight Diagnostics...', 'info');
        const isIsolated = window.crossOriginIsolated;
        
        if (!isIsolated) {
          throw new Error("Security Headers Missing. Site must be Cross-Origin Isolated.");
        }

        addLog('Booting WebContainer...', 'info');
        const webcontainer = await WebContainer.boot();
        containerRef.current = webcontainer;
        
        addLog('Mounting file system...', 'info');
        await webcontainer.mount({
          'agent.js': { file: { contents: agentSource } },
          'package.json': { file: { contents: packageJsonSource } },
        });

        setStatus('installing');
        addLog('Running npm install...', 'info');
        
        const installProcess = await webcontainer.spawn('npm', ['install']);
        installProcess.output.pipeTo(new WritableStream({
          write(data) {
            term.write(`\x1b[2m${data}\x1b[0m`);
          }
        }));

        const exitCode = await installProcess.exit;
        if (exitCode !== 0) throw new Error(`npm install failed with code ${exitCode}`);

        addLog('Agent Environment Ready.', 'success');
        const process = await webcontainer.spawn('node', ['agent.js']);
        processRef.current = process;

        process.output.pipeTo(new WritableStream({
          write(data) {
            term.write(data);
            
            // --- SYNC INTERCEPTOR ---
            if (data.includes('<<SYS_FILE_SYNC>>')) {
              const payload = data.split('<<SYS_FILE_SYNC>>')[1].trim();
              try {
                const fileData = JSON.parse(payload);
                addLog(`Syncing ${fileData.path} to host...`, 'info');
                
                fetch('http://localhost:8000/fs/write', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(fileData)
                })
                .then(res => {
                  if (res.ok) {
                    addLog(`Saved: ${fileData.path}`, 'success');
                    setRefreshTrigger(prev => prev + 1);
                  }
                  else addLog(`Save Failed: ${res.statusText}`, 'warn');
                })
                .catch(err => addLog(`Network Error: ${err}`, 'warn'));
                
              } catch (e) {
                addLog('Sync Protocol Error', 'warn');
              }
            }
            // ------------------------

            if (data.includes('[AGENT]')) addLog(data.replace(/\x1b\[[0-9;]*m/g, ''), 'info');
          }
        }));

        setStatus('ready');
      } catch (err) {
        if (!isMounted) return;
        addLog(`FATAL: ${err}`, 'warn');
        setStatus('error');
        terminalRef.current?.write(`\r\n\x1b[31mFATAL ERROR:\r\n${err}\x1b[0m\r\n`);
      }
    }

    boot();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-white selection:bg-primary/30">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-surface flex flex-col z-10">
        <div className="p-6 border-b border-border flex items-center space-x-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <LayoutDashboard className="w-5 h-5 text-primary" />
          </div>
          <h2 className="text-sm font-bold tracking-tight uppercase">Studio Mode</h2>
        </div>
        
        <div className="flex-1 overflow-y-auto py-6">
          <div className="px-6 mb-8">
            <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4">Navigation</div>
            <nav className="space-y-1">
              {[ 
                { id: 'explorer', icon: Files, label: 'Explorer' },
                { id: 'research', icon: Search, label: 'Research' },
                { id: 'metrics', icon: Activity, label: 'Metrics' },
                { id: 'governance', icon: ShieldCheck, label: 'Governance' },
              ].map((item) => (
                <div 
                  key={item.id} 
                  onClick={() => setActiveTab(item.id as any)}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-md text-xs cursor-pointer transition-colors ${ 
                    activeTab === item.id ? 'bg-primary/10 text-primary' : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                > 
                  <item.icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
              ))}
            </nav>
          </div>

          <div className="px-6 h-1/2 flex flex-col">
            {activeTab === 'explorer' ? (
              <FileExplorer 
                refreshTrigger={refreshTrigger} 
                onFileSelect={handleFileSelect}
              />
            ) : activeTab === 'research' ? (
              <SourcesList />
            ) : activeTab === 'metrics' ? (
              <TaskBoard />
            ) : (
              <div className="text-[10px] text-gray-500 italic px-2">Panel under construction.</div>
            )}
          </div>
        </div>

        <div className="p-4 border-t border-border space-y-3">
          <div className="flex items-center justify-between text-[10px] text-gray-500">
            <span>MEM DAEMON</span>
            <span className={`${memDaemonStatus === 'ONLINE' ? 'text-secondary' : 'text-red-500'} font-bold transition-colors`}>
              {memDaemonStatus}
            </span>
          </div>
          <div className="h-1 bg-border rounded-full overflow-hidden">
            <div className={`h-full ${memDaemonStatus === 'ONLINE' ? 'bg-secondary opacity-50' : 'bg-red-500 opacity-20'} w-full`} />
          </div>
        </div>
      </aside>

      {/* Main Panel */}
      <main className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="h-16 border-b border-border bg-surface/50 backdrop-blur-md flex items-center justify-between px-8 z-10">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${ 
                status === 'ready' ? 'bg-secondary' : 
                status === 'error' ? 'bg-red-500' : 'bg-accent animate-pulse'
              }`} />
              <span className="text-xs font-bold uppercase tracking-wider">{status}</span>
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
                <span className="text-[10px] font-bold text-primary font-mono">THROTTLE: {queueSize}</span>
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
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-400">File Preview</span>
                  </>
                ) : (
                  <>
                    <TerminalIcon className="w-4 h-4 text-primary" />
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Governance Shell</span>
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
