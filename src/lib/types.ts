export type PipelineStage = 'INBOUND' | 'PRE-CALL RESEARCH' | 'CALL' | 'AUDIT' | 'BUILD' | 'DONE';
export type AgentName = 'callie' | 'atlas' | 'executioner';
export type AgentStatusType = 'active' | 'idle' | 'stuck';
export type WorkStatus = 'active' | 'blocked' | 'done';
export type ProjectOwner = 'mew' | 'yuki' | 'claude-code';

export interface PipelineJob {
  id: string;
  client_name: string;
  business_type: string;
  stage: PipelineStage;
  stage_entered_at: string;
  agent_working: AgentName | null;
  last_updated: string;
  created_at: string;
}

export interface AgentStatus {
  id: string;
  agent_name: AgentName;
  last_heartbeat: string;
  status: AgentStatusType;
  current_job_id: string | null;
}

export interface CurrentWork {
  id: string;
  project_name: string;
  owner: ProjectOwner;
  status: WorkStatus;
  notes: string;
  last_updated: string;
}

export interface KnowledgeBaseStats {
  id: string;
  agent_name: string;
  category: string;
  item_count: number;
  last_updated: string;
}

export interface AlertHistory {
  id: string;
  alert_type: string;
  message: string;
  sent_at: string;
  acknowledged: boolean;
}

export type View = 'pipeline' | 'current-work' | 'knowledge' | 'actions';
