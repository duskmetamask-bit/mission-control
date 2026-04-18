-- Mission Control Dashboard - Supabase Schema
-- Run this in your Supabase SQL Editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Pipeline Jobs ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_name TEXT NOT NULL,
  business_type TEXT NOT NULL,
  stage TEXT NOT NULL CHECK (stage IN ('INBOUND', 'PRE-CALL RESEARCH', 'CALL', 'AUDIT', 'BUILD', 'DONE')),
  stage_entered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  agent_working TEXT CHECK (agent_working IN ('callie', 'atlas', 'executioner')),
  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE pipeline_jobs ENABLE ROW LEVEL SECURITY;

-- Allow all operations (dashboard only, password protected)
CREATE POLICY "Allow all" ON pipeline_jobs FOR ALL USING (true);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE pipeline_jobs;

-- ─── Agent Status ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_status (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_name TEXT NOT NULL UNIQUE CHECK (agent_name IN ('callie', 'atlas', 'executioner')),
  last_heartbeat TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'idle', 'stuck')),
  current_job_id UUID REFERENCES pipeline_jobs(id)
);

-- Enable RLS
ALTER TABLE agent_status ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all" ON agent_status FOR ALL USING (true);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE agent_status;

-- Insert default agents
INSERT INTO agent_status (agent_name, last_heartbeat, status) VALUES
  ('callie', NOW(), 'active'),
  ('atlas', NOW(), 'active'),
  ('executioner', NOW(), 'active')
ON CONFLICT (agent_name) DO NOTHING;

-- ─── Current Work ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS current_work (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_name TEXT NOT NULL,
  owner TEXT NOT NULL CHECK (owner IN ('mew', 'yuki', 'claude-code')),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'blocked', 'done')),
  notes TEXT,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE current_work ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all" ON current_work FOR ALL USING (true);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE current_work;

-- ─── Knowledge Base Stats ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_base_stats (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_name TEXT NOT NULL CHECK (agent_name IN ('atlas', 'gandalf', 'executioner')),
  category TEXT NOT NULL,
  item_count INTEGER NOT NULL DEFAULT 0,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(agent_name, category)
);

-- Enable RLS
ALTER TABLE knowledge_base_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all" ON knowledge_base_stats FOR ALL USING (true);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE knowledge_base_stats;

-- Insert demo knowledge base data
INSERT INTO knowledge_base_stats (agent_name, category, item_count, last_updated) VALUES
  ('atlas', 'Question Library', 47, NOW()),
  ('atlas', 'Audit Frameworks', 12, NOW()),
  ('gandalf', 'Tool Database', 89, NOW()),
  ('gandalf', 'Integration Guides', 23, NOW()),
  ('executioner', 'Build Patterns', 34, NOW()),
  ('executioner', 'Mistake Log', 156, NOW())
ON CONFLICT (agent_name, category) DO NOTHING;

-- ─── Alert History ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alert_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  alert_type TEXT NOT NULL,
  message TEXT NOT NULL,
  sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  acknowledged BOOLEAN NOT NULL DEFAULT FALSE
);

-- Enable RLS
ALTER TABLE alert_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all" ON alert_history FOR ALL USING (true);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE alert_history;

-- ─── Helper Functions ─────────────────────────────────────────────────────────

-- Function to update agent heartbeat
CREATE OR REPLACE FUNCTION update_heartbeat(agent_name TEXT)
RETURNS VOID AS $$
BEGIN
  UPDATE agent_status 
  SET last_heartbeat = NOW(),
      status = CASE 
        WHEN EXTRACT(EPOCH FROM (NOW() - last_heartbeat)) < 300 THEN 'active'
        WHEN EXTRACT(EPOCH FROM (NOW() - last_heartbeat)) < 1800 THEN 'idle'
        ELSE 'stuck'
      END
  WHERE agent_status.agent_name = $1;
END;
$$ LANGUAGE plpgsql;

-- Function to move client to next stage
CREATE OR REPLACE FUNCTION advance_stage(job_id UUID, new_stage TEXT)
RETURNS VOID AS $$
BEGIN
  UPDATE pipeline_jobs 
  SET stage = new_stage,
      stage_entered_at = NOW(),
      last_updated = NOW()
  WHERE id = job_id;
END;
$$ LANGUAGE plpgsql;

-- ─── Cron Job for Status Updates (run every minute) ──────────────────────────
-- Note: Requires Supabase Pro plan for pg_cron
-- SELECT cron.schedule('update-agent-status', '* * * * *', 
--   'UPDATE agent_status SET status = CASE ...');

-- ─── Demo Data ────────────────────────────────────────────────────────────────
-- Insert some demo pipeline jobs
INSERT INTO pipeline_jobs (client_name, business_type, stage, stage_entered_at, agent_working, last_updated) VALUES
  ('Coastal Coffee', 'Cafe & Restaurant', 'PRE-CALL RESEARCH', NOW() - INTERVAL '2 hours', 'atlas', NOW() - INTERVAL '30 minutes'),
  ('Metro Fitness', 'Gym & Fitness', 'CALL', NOW() - INTERVAL '6 hours', 'callie', NOW() - INTERVAL '15 minutes'),
  ('Bloom Florist', 'Retail & Floristry', 'AUDIT', NOW() - INTERVAL '26 hours', 'executioner', NOW() - INTERVAL '2 hours'),
  ('Summit Accounting', 'Accounting & Tax', 'BUILD', NOW() - INTERVAL '12 hours', 'executioner', NOW() - INTERVAL '1 hour'),
  ('Oceanview Dental', 'Dental Practice', 'INBOUND', NOW() - INTERVAL '30 minutes', NULL, NOW() - INTERVAL '30 minutes')
ON CONFLICT DO NOTHING;
