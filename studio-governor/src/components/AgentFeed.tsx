import { useEffect, useState } from 'react';
import { Activity, Brain, Radio, CheckCircle2, AlertTriangle } from 'lucide-react';

interface MemoryItem {
  id: string;
  text: string;
  type: string;
  metadata: string; // JSON string
  timestamp: number;
}

export function AgentFeed() {
  const [feed, setFeed] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFeed = async () => {
      try {
        const res = await fetch('http://localhost:8000/memory/feed?limit=50');
        if (res.ok) {
          const data = await res.json();
          setFeed(data);
        }
      } catch (err) {
        console.error("Feed fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchFeed();
    const interval = setInterval(fetchFeed, 3000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (ts: number) => {
    return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const getIcon = (text: string) => {
    if (text.includes("Error") || text.includes("Failed")) return <AlertTriangle className="w-3 h-3 text-red-400" />;
    if (text.includes("Complete") || text.includes("Success")) return <CheckCircle2 className="w-3 h-3 text-secondary" />;
    if (text.includes("Thinking") || text.includes("Planning")) return <Brain className="w-3 h-3 text-purple-400" />;
    return <Radio className="w-3 h-3 text-primary" />;
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-primary" />
          <span className="text-xs font-bold uppercase tracking-wider">Neural Feed</span>
        </div>
        <div className="flex items-center space-x-2">
           <span className="text-[10px] text-gray-500 animate-pulse">LIVE</span>
           <span className="text-[10px] bg-border px-1.5 py-0.5 rounded text-gray-400">{feed.length} events</span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading && feed.length === 0 && (
          <div className="text-center text-xs text-gray-500 mt-10">Connecting to Cortex...</div>
        )}
        
        {feed.map((item) => {
           let meta = {};
           try { meta = JSON.parse(item.metadata); } catch {}
           
           return (
            <div key={item.id} className="group relative pl-4 border-l border-border hover:border-primary transition-colors">
              <div className="absolute -left-[5px] top-0 w-2.5 h-2.5 bg-surface border border-border rounded-full flex items-center justify-center group-hover:border-primary">
                 <div className="w-1 h-1 bg-gray-500 rounded-full group-hover:bg-primary" />
              </div>
              
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-[10px] font-mono text-gray-500">{formatTime(item.timestamp)}</span>
                {getIcon(item.text)}
              </div>
              
              <div className="text-[11px] text-gray-300 leading-relaxed font-mono">
                {item.text}
              </div>
              
              {/* Render select metadata if useful */}
              {/* @ts-ignore */}
              {meta.new_state && (
                 <div className="mt-1 flex items-center space-x-2">
                    {/* @ts-ignore */}
                    <span className="text-[9px] px-1.5 py-0.5 bg-white/5 rounded text-gray-400">Old: {meta.old_state}</span>
                    <span className="text-[9px] text-gray-600">→</span>
                    {/* @ts-ignore */}
                    <span className="text-[9px] px-1.5 py-0.5 bg-primary/10 text-primary rounded border border-primary/20">{meta.new_state}</span>
                 </div>
              )}
            </div>
           );
        })}
      </div>
    </div>
  );
}
