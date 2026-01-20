import React, { useEffect, useState } from 'react';
import { CheckCircle2, Circle, Clock, User, AlertCircle } from 'lucide-react';

interface Task {
  id: string;
  text: string;
  assignee: string;
  claimed_by: string | null;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  priority: string;
  updated_at: number;
}

export const TaskBoard: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      const res = await fetch('http://localhost:8000/tasks/list');
      if (res.ok) {
        const data = await res.json();
        setTasks(data.tasks);
      }
    } catch (err) {
      console.error('Failed to fetch tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 3000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-3 h-3 text-secondary" />;
      case 'in_progress': return <Clock className="w-3 h-3 text-primary animate-pulse" />;
      case 'failed': return <AlertCircle className="w-3 h-3 text-red-500" />;
      default: return <Circle className="w-3 h-3 text-gray-500" />;
    }
  };

  if (loading && tasks.length === 0) return null;

  const groupedTasks = {
    pending: tasks.filter(t => t.status === 'pending'),
    active: tasks.filter(t => t.status === 'in_progress'),
    done: tasks.filter(t => t.status === 'completed' || t.status === 'failed')
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Task Registry</div>
        <div className="flex space-x-2">
           <span className="text-[9px] px-1.5 py-0.5 bg-white/5 rounded text-gray-400 font-mono">
            {tasks.length} TOTAL
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {/* Active Column */}
        {groupedTasks.active.length > 0 && (
          <div className="space-y-2">
            <div className="text-[9px] font-bold text-primary/70 uppercase px-1">Active Now</div>
            {groupedTasks.active.map(task => (
              <div key={task.id} className="p-3 rounded-lg bg-primary/5 border border-primary/20 shadow-lg shadow-primary/5">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(task.status)}
                    <span className="text-[11px] font-bold text-primary">{task.assignee.toUpperCase()}</span>
                  </div>
                  <span className="text-[8px] text-primary/50 font-mono">ID: {task.id.slice(0,8)}</span>
                </div>
                <p className="text-[10px] text-gray-200 mb-2 leading-tight">{task.text}</p>
                <div className="flex items-center space-x-2 text-[9px] text-primary/60 italic">
                  <User className="w-2 h-2" />
                  <span>Claimed by: {task.claimed_by || 'Unknown'}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pending Column */}
        <div className="space-y-2">
          <div className="text-[9px] font-bold text-gray-500 uppercase px-1">Backlog</div>
          {groupedTasks.pending.length === 0 ? (
            <div className="p-4 rounded-lg border border-dashed border-white/10 text-[10px] text-gray-600 text-center italic">
              All clear. No pending tasks.
            </div>
          ) : (
            groupedTasks.pending.map(task => (
              <div key={task.id} className="p-3 rounded-lg bg-white/5 border border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(task.status)}
                    <span className="text-[11px] font-bold text-gray-400">{task.assignee.toUpperCase()}</span>
                  </div>
                  <div className={`px-1 rounded text-[8px] font-bold ${
                    task.priority === 'high' ? 'bg-red-500/20 text-red-400' : 'bg-white/10 text-gray-500'
                  }`}>
                    {task.priority.toUpperCase()}
                  </div>
                </div>
                <p className="text-[10px] text-gray-400 leading-tight">{task.text}</p>
              </div>
            ))
          )}
        </div>

        {/* Recently Completed */}
        {groupedTasks.done.length > 0 && (
          <div className="space-y-2 pt-2 border-t border-white/5">
             <div className="text-[9px] font-bold text-gray-600 uppercase px-1">Archive</div>
             {groupedTasks.done.slice(0, 3).map(task => (
               <div key={task.id} className="flex items-center justify-between p-2 rounded bg-white/5 border border-transparent opacity-60">
                 <div className="flex items-center space-x-3 overflow-hidden">
                   {getStatusIcon(task.status)}
                   <span className="text-[10px] text-gray-400 truncate">{task.text}</span>
                 </div>
                 <span className="text-[8px] text-gray-600 font-mono">OK</span>
               </div>
             ))}
          </div>
        )}
      </div>
    </div>
  );
};
