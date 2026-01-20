import { useEffect, useState } from 'react';
import { Folder, FileText, RefreshCw } from 'lucide-react';

interface FileNode {
  name: string;
  type: 'file' | 'directory';
  path: string;
}

interface FileExplorerProps {
  refreshTrigger: number;
  onFileSelect?: (path: string) => void;
}

export const FileExplorer: React.FC<FileExplorerProps> = ({ refreshTrigger, onFileSelect }) => {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/fs/list');
      if (res.ok) {
        const data = await res.json();
        setFiles(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [refreshTrigger]);

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between px-6 mb-4">
        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Workspace</div>
        <RefreshCw 
            className={`w-3 h-3 text-gray-500 cursor-pointer hover:text-white ${loading ? 'animate-spin' : ''}`}
            onClick={fetchFiles}
        />
      </div>
      <div className="space-y-1 px-6">
        {files.length === 0 && !loading && (
            <div className="text-[10px] text-gray-600 italic">Empty workspace</div>
        )}
        {files.map((file) => (
          <div 
            key={file.path} 
            className="flex items-center space-x-2 text-xs text-gray-300 py-1 px-2 hover:bg-white/5 rounded cursor-pointer group"
            onClick={() => file.type === 'file' && onFileSelect?.(file.path)}
          >
            {file.type === 'directory' ? (
                <Folder className="w-3 h-3 text-accent" />
            ) : (
                <FileText className="w-3 h-3 text-gray-400 group-hover:text-white" />
            )}
            <span>{file.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
