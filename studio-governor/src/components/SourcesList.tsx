import React, { useEffect, useState } from "react";
import { FileText, Tag } from "lucide-react";
import { api } from "../lib/api";

interface Source {
  id: string;
  title: string;
  type: string;
  summary: string;
  tags: string; // JSON string
  created_at: number;
}

export const SourcesList: React.FC = () => {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSources = async () => {
    try {
      const data = await api.getSources();
      setSources(data);
    } catch (err) {
      console.error("Failed to fetch sources:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
    const interval = setInterval(fetchSources, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading && sources.length === 0) {
    return (
      <div className="flex items-center justify-center h-20 text-gray-500 text-[10px] animate-pulse">
        CONNECTING TO CORTEX...
      </div>
    );
  }

  return (
    <div className="space-y-4 overflow-y-auto pr-2">
      <div className="flex items-center justify-between">
        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">
          Research Corpus
        </div>
        <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-mono">
          {sources.length}
        </span>
      </div>

      {sources.length === 0 ? (
        <div className="text-[10px] text-gray-600 italic">
          No sources ingested. Drop files in workspace/incoming.
        </div>
      ) : (
        <div className="space-y-2">
          {sources.map((source) => {
            const tags = JSON.parse(source.tags || "[]");
            return (
              <div
                key={source.id}
                className="p-3 rounded-lg bg-white/5 border border-white/10 hover:border-primary/30 transition-all group cursor-default"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-3 h-3 text-primary" />
                    <span className="text-[11px] font-bold truncate max-w-[120px]">
                      {source.title}
                    </span>
                  </div>
                  <span className="text-[9px] text-gray-500 font-mono">
                    {new Date(source.created_at * 1000).toLocaleDateString([], {
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>

                <p className="text-[10px] text-gray-400 line-clamp-2 leading-relaxed mb-2 italic">
                  "{source.summary || "No summary available."}"
                </p>

                <div className="flex flex-wrap gap-1">
                  {tags.map((tag: string) => (
                    <div
                      key={tag}
                      className="flex items-center space-x-1 px-1.5 py-0.5 bg-primary/5 rounded border border-primary/10 text-[8px] text-primary/70"
                    >
                      <Tag className="w-2 h-2" />
                      <span>{tag}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
