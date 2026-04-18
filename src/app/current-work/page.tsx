'use client';

import { useEffect, useState, useCallback } from 'react';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';
import type { CurrentWork, WorkStatus, ProjectOwner } from '@/lib/types';

const STATUS_CONFIG: Record<WorkStatus, { color: string; label: string; bg: string }> = {
  active: { color: 'text-green-400', label: 'Active', bg: 'bg-green-500' },
  blocked: { color: 'text-red-400', label: 'Blocked', bg: 'bg-red-500' },
  done: { color: 'text-gray-400', label: 'Done', bg: 'bg-gray-500' },
};

const OWNER_EMOJI: Record<ProjectOwner, string> = {
  mew: '🔵',
  yuki: '🟡',
  'claude-code': '🤖',
};

function ProjectCard({ work, onUpdate }: { work: CurrentWork; onUpdate: (status: WorkStatus) => void }) {
  const config = STATUS_CONFIG[work.status];
  const lastUpdated = new Date(work.last_updated).toLocaleString('en-AW', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Australia/Perth'
  });

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-bold text-lg flex items-center gap-2">
          <span>{work.project_name}</span>
        </h3>
        <span className={`${config.color} text-xs font-medium px-2 py-1 rounded ${config.bg} bg-opacity-20`}>
          {config.label}
        </span>
      </div>
      
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-3">
        <span>{OWNER_EMOJI[work.owner]}</span>
        <span className="capitalize">{work.owner.replace('-', ' ')}</span>
      </div>
      
      {work.notes && (
        <p className="text-gray-300 text-sm mb-3 bg-gray-900 rounded p-2">{work.notes}</p>
      )}
      
      <div className="flex justify-between items-center">
        <span className="text-xs text-gray-500">Updated: {lastUpdated}</span>
        {work.status !== 'done' && (
          <select
            value={work.status}
            onChange={(e) => onUpdate(e.target.value as WorkStatus)}
            className="text-xs bg-gray-700 text-gray-300 rounded px-2 py-1 border border-gray-600"
          >
            <option value="active">Active</option>
            <option value="blocked">Blocked</option>
            <option value="done">Done</option>
          </select>
        )}
      </div>
    </div>
  );
}

export default function CurrentWorkPage() {
  const [works, setWorks] = useState<CurrentWork[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!isSupabaseConfigured || !supabase) {
      setWorks(DEMO_WORKS);
      setLoading(false);
      return;
    }

    const { data } = await supabase
      .from('current_work')
      .select('*')
      .order('last_updated', { ascending: false });

    if (data) setWorks(data);
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();

    if (!isSupabaseConfigured || !supabase) return;

    const channel = supabase
      .channel('current_work')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'current_work' }, () => {
        loadData();
      })
      .subscribe();

    return () => {
      if (supabase) supabase.removeChannel(channel);
    };
  }, [loadData]);

  const updateStatus = async (workId: string, status: WorkStatus) => {
    const updated = works.map(w => 
      w.id === workId ? { ...w, status, last_updated: new Date().toISOString() } : w
    );
    setWorks(updated);

    if (isSupabaseConfigured && supabase) {
      await supabase
        .from('current_work')
        .update({ status, last_updated: new Date().toISOString() })
        .eq('id', workId);
    }
  };

  const activeWorks = works.filter(w => w.status === 'active');
  const blockedWorks = works.filter(w => w.status === 'blocked');
  const doneWorks = works.filter(w => w.status === 'done');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-green-400">{activeWorks.length}</div>
          <div className="text-sm text-gray-400">Active</div>
        </div>
        <div className="bg-gray-900 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-red-400">{blockedWorks.length}</div>
          <div className="text-sm text-gray-400">Blocked</div>
        </div>
        <div className="bg-gray-900 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-gray-400">{doneWorks.length}</div>
          <div className="text-sm text-gray-400">Done</div>
        </div>
      </div>

      {/* Active Projects */}
      {activeWorks.length > 0 && (
        <div>
          <h2 className="text-lg font-medium text-green-400 mb-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            Active Projects
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeWorks.map(work => (
              <ProjectCard key={work.id} work={work} onUpdate={(s) => updateStatus(work.id, s)} />
            ))}
          </div>
        </div>
      )}

      {/* Blocked Projects */}
      {blockedWorks.length > 0 && (
        <div>
          <h2 className="text-lg font-medium text-red-400 mb-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            Blocked
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {blockedWorks.map(work => (
              <ProjectCard key={work.id} work={work} onUpdate={(s) => updateStatus(work.id, s)} />
            ))}
          </div>
        </div>
      )}

      {/* Done Projects */}
      {doneWorks.length > 0 && (
        <div>
          <h2 className="text-lg font-medium text-gray-400 mb-3">Recently Completed</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {doneWorks.slice(0, 6).map(work => (
              <ProjectCard key={work.id} work={work} onUpdate={(s) => updateStatus(work.id, s)} />
            ))}
          </div>
        </div>
      )}

      {works.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-4xl mb-4">📋</p>
          <p>No projects tracked yet</p>
          <p className="text-sm mt-2">Mew and Yuki can add projects via the API</p>
        </div>
      )}
    </div>
  );
}

const DEMO_WORKS: CurrentWork[] = [
  {
    id: '1',
    project_name: 'EMVY Landing Page v2',
    owner: 'mew',
    status: 'active',
    notes: 'Adding testimonials section + pricing FAQ',
    last_updated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '2',
    project_name: 'Lead Gen Automation',
    owner: 'yuki',
    status: 'active',
    notes: 'Serper API integration for finding leads',
    last_updated: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '3',
    project_name: 'Mission Control Dashboard',
    owner: 'claude-code',
    status: 'blocked',
    notes: 'Waiting on Supabase credentials from Dusk',
    last_updated: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '4',
    project_name: 'Newsletter Setup',
    owner: 'yuki',
    status: 'done',
    notes: 'Substack configured, first issue sent',
    last_updated: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  },
];
