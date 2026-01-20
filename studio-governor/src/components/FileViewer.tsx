import React from 'react';
import { X, FileText } from 'lucide-react';

interface FileViewerProps {
  path: string;
  content: string;
  onClose: () => void;
}

export const FileViewer: React.FC<FileViewerProps> = ({ path, content, onClose }) => {
  return (
    <div className="flex flex-col h-full bg-black/40 rounded-xl border border-border overflow-hidden backdrop-blur-sm">
      <div className="flex items-center justify-between p-3 border-b border-border bg-white/5">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-primary" />
          <span className="text-xs font-mono text-gray-300">{path}</span>
        </div>
        <X 
          className="w-4 h-4 text-gray-500 hover:text-white cursor-pointer transition-colors" 
          onClick={onClose}
        />
      </div>
      <div className="flex-1 p-4 overflow-auto">
        <pre className="text-xs font-mono text-gray-300 whitespace-pre-wrap">
          {content}
        </pre>
      </div>
    </div>
  );
};
