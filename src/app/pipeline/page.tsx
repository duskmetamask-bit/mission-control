'use client';

import { useEffect, useState, useCallback } from 'react';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';
import type { PipelineJob, AgentStatus, PipelineStage, AgentName } from '@/lib/types';

const STAGES: PipelineStage[] = ['INBOUND', 'PRE-CALL RESEARCH', 'CALL', 'AUDIT', 'BUILD', 'DONE'];

const STAGE_COLORS: Record<PipelineStage, string> = {
  'INBOUND': 'bg-indigo-500',
  'PRE-CALL RESEARCH': 'bg-purple-500',
  'CALL': 'bg-pink-500',
  'AUDIT': 'bg-amber-500',
  'BUILD': 'bg-emerald-500',
  'DONE': 'bg-green-600',
};

function getTimeInStage(stageEnteredAt: string): { text: string; color: string } {
  const diff = Date.now() - new Date(stageEnteredAt).getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  
  let text = '';
  if (hours > 0) text += `${hours}h `;
  text += `${minutes}m`;
  
  let color = 'text-gray-400';
  if (hours >= 24) color = 'text-red-500 font-bold';
  else if (hours >= 4) color = 'text-amber-400';
  
  return { text, color };
}

function getAgentStatus(lastHeartbeat: string): { status: string; color: string; bgColor: string } {
  const diff = Date.now() - new Date(lastHeartbeat).getTime();
  const minutes = Math.floor(diff / (1000 * 60));
  
  if (minutes < 5) return { status: 'Active', color: 'text-green-400', bgColor: 'bg-green-500' };
  if (minutes < 30) return { status: 'Idle', color: 'text-yellow-400', bgColor: 'bg-yellow-500' };
  return { status: 'Stuck', color: 'text-red-400', bgColor: 'bg-red-500' };
}

function AgentCard({ agent }: { agent: AgentStatus }) {
  const { status, color, bgColor } = getAgentStatus(agent.last_heartbeat);
  const lastBeat = new Date(agent.last_heartbeat).toLocaleTimeString('en-AW', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Australia/Perth'
  });
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 flex flex-col items-center">
      <div className={`w-3 h-3 rounded-full ${bgColor} mb-2 animate-pulse`} />
      <span className="font-bold capitalize">{agent.agent_name}</span>
      <span className={`text-sm ${color}`}>{status}</span>
      <span className="text-xs text-gray-500 mt-1">Last: {lastBeat}</span>
    </div>
  );
}

function ClientCard({ job }: { job: PipelineJob }) {
  const { text: timeText, color: timeColor } = getTimeInStage(job.stage_entered_at);
  const agentColor = job.agent_working ? 'text-blue-400' : 'text-gray-500';
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-bold text-lg">{job.client_name}</h3>
        <span className={`text-xs ${timeColor}`}>{timeText}</span>
      </div>
      <p className="text-gray-400 text-sm mb-3">{job.business_type}</p>
      <div className="flex items-center justify-between">
        <span className={`${STAGE_COLORS[job.stage]} px-2 py-1 rounded text-xs font-medium text-white`}>
          {job.stage}
        </span>
        {job.agent_working && (
          <span className={`text-sm capitalize ${agentColor}`}>
            👤 {job.agent_working}
          </span>
        )}
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Updated: {new Date(job.last_updated).toLocaleString('en-AW', {
          hour: '2-digit',
          minute: '2-digit',
          timeZone: 'Australia/Perth'
        })}
      </p>
    </div>
  );
}

function StageColumn({ stage, jobs }: { stage: PipelineStage; jobs: PipelineJob[] }) {
  return (
    <div className="flex-1 min-w-[280px]">
      <div className={`${STAGE_COLORS[stage]} text-white text-center py-2 rounded-t-lg font-medium text-sm`}>
        {stage}
        <span className="ml-2 opacity-75">({jobs.length})</span>
      </div>
      <div className="bg-gray-900 rounded-b-lg p-3 space-y-3 min-h-[200px]">
        {jobs.length === 0 ? (
          <p className="text-gray-600 text-sm text-center py-8">No clients</p>
        ) : (
          jobs.map(job => <ClientCard key={job.id} job={job} />)
        )}
      </div>
    </div>
  );
}

async function checkAndSendAlerts(jobs: PipelineJob[], agents: AgentStatus[]) {
  // Check for stuck clients (>24h in stage)
  for (const job of jobs) {
    if (job.stage === 'DONE') continue;
    const hoursInStage = (Date.now() - new Date(job.stage_entered_at).getTime()) / (1000 * 60 * 60);
    
    if (hoursInStage > 24) {
      await fetch('/api/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'stuck_client',
          message: `⚠️ ${job.client_name} stuck in "${job.stage}" for ${Math.floor(hoursInStage)}h`,
          job_id: job.id,
        }),
      });
    }
  }
  
  // Check for missing agents (>30min heartbeat)
  for (const agent of agents) {
    const minutesSinceHeartbeat = (Date.now() - new Date(agent.last_heartbeat).getTime()) / (1000 * 60);
    
    if (minutesSinceHeartbeat > 30) {
      await fetch('/api/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'missing_agent',
          message: `🚨 ${agent.agent_name} missing heartbeat (${Math.floor(minutesSinceHeartbeat)}m ago)`,
          agent_name: agent.agent_name,
        }),
      });
    }
  }
}

export default function PipelinePage() {
  const [jobs, setJobs] = useState<PipelineJob[]>([]);
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!isSupabaseConfigured || !supabase) {
      // Load demo data if Supabase not configured
      setJobs(DEMO_JOBS);
      setAgents(DEMO_AGENTS);
      setLoading(false);
      return;
    }

    const [jobsRes, agentsRes] = await Promise.all([
      supabase.from('pipeline_jobs').select('*').order('last_updated', { ascending: false }),
      supabase.from('agent_status').select('*'),
    ]);

    if (jobsRes.data) setJobs(jobsRes.data);
    if (agentsRes.data) setAgents(agentsRes.data);
    setLoading(false);

    // Check for alerts
    if (jobsRes.data && agentsRes.data) {
      await checkAndSendAlerts(jobsRes.data, agentsRes.data);
    }
  }, []);

  useEffect(() => {
    loadData();

    if (!isSupabaseConfigured || !supabase) return;

    // Realtime subscriptions
    const jobsChannel = supabase
      .channel('pipeline_jobs')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'pipeline_jobs' }, () => {
        loadData();
      })
      .subscribe();

    const agentsChannel = supabase
      .channel('agent_status')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'agent_status' }, () => {
        loadData();
      })
      .subscribe();

    return () => {
      if (supabase) {
        supabase.removeChannel(jobsChannel);
        supabase.removeChannel(agentsChannel);
      }
    };
  }, [loadData]);

  const jobsByStage = STAGES.reduce((acc, stage) => {
    acc[stage] = jobs.filter(j => j.stage === stage);
    return acc;
  }, {} as Record<PipelineStage, PipelineJob[]>);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Agent Status Row */}
      <div className="bg-gray-900 rounded-lg p-4">
        <h2 className="text-sm font-medium text-gray-400 mb-3">AGENT STATUS</h2>
        <div className="grid grid-cols-3 gap-4">
          {agents.length > 0 ? (
            agents.map(agent => <AgentCard key={agent.id} agent={agent} />)
          ) : (
            DEMO_AGENTS.map(agent => <AgentCard key={agent.id} agent={agent} />)
          )}
        </div>
      </div>

      {/* Pipeline Kanban */}
      <div className="overflow-x-auto pb-4">
        <div className="flex gap-3 min-w-max">
          {STAGES.map(stage => (
            <StageColumn key={stage} stage={stage} jobs={jobsByStage[stage]} />
          ))}
        </div>
      </div>

      {/* Last Updated */}
      <p className="text-xs text-gray-500">
        Last updated: {new Date().toLocaleString('en-AW', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          timeZone: 'Australia/Perth'
        })} AWST
        {isSupabaseConfigured && ' • Live via Supabase Realtime'}
      </p>
    </div>
  );
}

// Demo data for when Supabase isn't configured
const DEMO_JOBS: PipelineJob[] = [
  {
    id: '1',
    client_name: 'Coastal Coffee',
    business_type: 'Cafe & Restaurant',
    stage: 'PRE-CALL RESEARCH',
    stage_entered_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    agent_working: 'atlas',
    last_updated: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '2',
    client_name: 'Metro Fitness',
    business_type: 'Gym & Fitness',
    stage: 'CALL',
    stage_entered_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    agent_working: 'callie',
    last_updated: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '3',
    client_name: 'Bloom Florist',
    business_type: 'Retail & Floristry',
    stage: 'AUDIT',
    stage_entered_at: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(),
    agent_working: 'executioner',
    last_updated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '4',
    client_name: 'Summit Accounting',
    business_type: 'Accounting & Tax',
    stage: 'BUILD',
    stage_entered_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    agent_working: 'executioner',
    last_updated: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 96 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '5',
    client_name: 'Oceanview Dental',
    business_type: 'Dental Practice',
    stage: 'INBOUND',
    stage_entered_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    agent_working: null,
    last_updated: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  },
  {
    id: '6',
    client_name: 'Green Thumb Landscaping',
    business_type: 'Landscaping Services',
    stage: 'DONE',
    stage_entered_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
    agent_working: 'executioner',
    last_updated: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 120 * 60 * 60 * 1000).toISOString(),
  },
];

const DEMO_AGENTS: AgentStatus[] = [
  {
    id: '1',
    agent_name: 'callie' as AgentName,
    last_heartbeat: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    status: 'active',
    current_job_id: '2',
  },
  {
    id: '2',
    agent_name: 'atlas' as AgentName,
    last_heartbeat: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    status: 'idle',
    current_job_id: '1',
  },
  {
    id: '3',
    agent_name: 'executioner' as AgentName,
    last_heartbeat: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    status: 'stuck',
    current_job_id: '4',
  },
];
