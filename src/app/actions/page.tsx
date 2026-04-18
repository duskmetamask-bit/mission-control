'use client';

import { useState } from 'react';
import { isSupabaseConfigured } from '@/lib/supabase';
import type { AlertHistory } from '@/lib/types';

type ActionState = 'idle' | 'loading' | 'success' | 'error';

function ActionCard({ 
  emoji, 
  title, 
  description, 
  onClick, 
  state,
  variant = 'default'
}: { 
  emoji: string; 
  title: string; 
  description: string; 
  onClick: () => void;
  state: ActionState;
  variant?: 'default' | 'danger';
}) {
  return (
    <button
      onClick={onClick}
      disabled={state === 'loading'}
      className={`w-full text-left p-6 rounded-lg border transition-all ${
        variant === 'danger' 
          ? 'bg-red-900 border-red-700 hover:bg-red-800' 
          : 'bg-gray-800 border-gray-700 hover:bg-gray-750'
      } disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      <div className="flex items-start gap-4">
        <span className="text-3xl">{emoji}</span>
        <div className="flex-1">
          <h3 className="font-bold text-lg mb-1">{title}</h3>
          <p className="text-gray-400 text-sm">{description}</p>
        </div>
        <div className="flex-shrink-0">
          {state === 'loading' && (
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          )}
          {state === 'success' && <span className="text-green-400 text-xl">✓</span>}
          {state === 'error' && <span className="text-red-400 text-xl">✗</span>}
          {state === 'idle' && <span className="text-gray-500">→</span>}
        </div>
      </div>
    </button>
  );
}

function AlertHistoryTable({ alerts }: { alerts: AlertHistory[] }) {
  if (alerts.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No alerts sent yet</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-400 border-b border-gray-700">
            <th className="pb-2">Type</th>
            <th className="pb-2">Message</th>
            <th className="pb-2">Time</th>
            <th className="pb-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map(alert => (
            <tr key={alert.id} className="border-b border-gray-800">
              <td className="py-2">
                <span className={`px-2 py-1 rounded text-xs ${
                  alert.alert_type === 'stuck_client' ? 'bg-amber-900 text-amber-300' :
                  alert.alert_type === 'missing_agent' ? 'bg-red-900 text-red-300' :
                  'bg-gray-700 text-gray-300'
                }`}>
                  {alert.alert_type.replace('_', ' ')}
                </span>
              </td>
              <td className="py-2 text-gray-300">{alert.message}</td>
              <td className="py-2 text-gray-500">
                {new Date(alert.sent_at).toLocaleString('en-AW', {
                  hour: '2-digit',
                  minute: '2-digit',
                  timeZone: 'Australia/Perth'
                })}
              </td>
              <td className="py-2">
                {alert.acknowledged ? (
                  <span className="text-green-400">✓ Ack'd</span>
                ) : (
                  <span className="text-yellow-400">Pending</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ActionsPage() {
  const [clientForm, setClientForm] = useState({ name: '', business: '', stage: 'INBOUND' });
  const [showClientForm, setShowClientForm] = useState(false);
  const [showAlerts, setShowAlerts] = useState(false);
  const [states, setStates] = useState<Record<string, ActionState>>({
    createClient: 'idle',
    healthCheck: 'idle',
    viewAlerts: 'idle',
    refresh: 'idle',
  });
  const [alerts, setAlerts] = useState<AlertHistory[]>(DEMO_ALERTS);

  const setState = (key: string, value: ActionState) => {
    setStates(prev => ({ ...prev, [key]: value }));
  };

  const handleCreateClient = async () => {
    if (!clientForm.name || !clientForm.business) return;
    setState('createClient', 'loading');

    try {
      if (isSupabaseConfigured) {
        const res = await fetch('/api/clients', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(clientForm),
        });
        if (!res.ok) throw new Error('Failed');
      }
      setState('createClient', 'success');
      setClientForm({ name: '', business: '', stage: 'INBOUND' });
      setTimeout(() => {
        setState('createClient', 'idle');
        setShowClientForm(false);
      }, 1500);
    } catch {
      setState('createClient', 'error');
      setTimeout(() => setState('createClient', 'idle'), 2000);
    }
  };

  const handleHealthCheck = async () => {
    setState('healthCheck', 'loading');
    try {
      await fetch('/api/health-check', { method: 'POST' });
      setState('healthCheck', 'success');
      setTimeout(() => setState('healthCheck', 'idle'), 2000);
    } catch {
      setState('healthCheck', 'error');
      setTimeout(() => setState('healthCheck', 'idle'), 2000);
    }
  };

  const handleViewAlerts = async () => {
    setState('viewAlerts', 'loading');
    try {
      if (isSupabaseConfigured) {
        const res = await fetch('/api/alerts');
        const data = await res.json();
        setAlerts(data.alerts || []);
      }
      setState('viewAlerts', 'success');
      setShowAlerts(true);
      setTimeout(() => setState('viewAlerts', 'idle'), 1000);
    } catch {
      setState('viewAlerts', 'error');
      setTimeout(() => setState('viewAlerts', 'idle'), 2000);
    }
  };

  const handleRefresh = () => {
    setState('refresh', 'loading');
    window.location.reload();
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ActionCard
          emoji="➕"
          title="Create New Client Job"
          description="Add a new client to the pipeline"
          onClick={() => setShowClientForm(!showClientForm)}
          state={showClientForm ? 'idle' : 'idle'}
        />
        <ActionCard
          emoji="💓"
          title="Trigger Agent Health Check"
          description="Ping all agents to confirm they're responding"
          onClick={handleHealthCheck}
          state={states.healthCheck}
        />
        <ActionCard
          emoji="📋"
          title="View Alert History"
          description="See all Discord alerts sent by the system"
          onClick={handleViewAlerts}
          state={states.viewAlerts}
        />
        <ActionCard
          emoji="🔄"
          title="Refresh All Data"
          description="Force refresh all views and subscriptions"
          onClick={handleRefresh}
          state={states.refresh}
        />
      </div>

      {/* Client Form */}
      {showClientForm && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="font-bold mb-4">New Client</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Client Name</label>
              <input
                type="text"
                value={clientForm.name}
                onChange={e => setClientForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Acme Corp"
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white placeholder-gray-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Business Type</label>
              <input
                type="text"
                value={clientForm.business}
                onChange={e => setClientForm(prev => ({ ...prev, business: e.target.value }))}
                placeholder="SaaS"
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white placeholder-gray-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Initial Stage</label>
              <select
                value={clientForm.stage}
                onChange={e => setClientForm(prev => ({ ...prev, stage: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white"
              >
                <option value="INBOUND">INBOUND</option>
                <option value="PRE-CALL RESEARCH">PRE-CALL RESEARCH</option>
                <option value="CALL">CALL</option>
                <option value="AUDIT">AUDIT</option>
                <option value="BUILD">BUILD</option>
                <option value="DONE">DONE</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleCreateClient}
              disabled={!clientForm.name || !clientForm.business}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded text-white font-medium"
            >
              {states.createClient === 'loading' ? 'Creating...' : 'Create Client'}
            </button>
            <button
              onClick={() => setShowClientForm(false)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-white"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Alert History */}
      {showAlerts && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold">Alert History</h3>
            <button
              onClick={() => setShowAlerts(false)}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>
          <AlertHistoryTable alerts={alerts} />
        </div>
      )}

      {/* System Info */}
      <div className="bg-gray-900 rounded-lg p-4 text-sm text-gray-400">
        <h4 className="font-medium text-gray-300 mb-2">System Configuration</h4>
        <div className="grid grid-cols-2 gap-2">
          <span>Supabase:</span>
          <span className={isSupabaseConfigured ? 'text-green-400' : 'text-yellow-400'}>
            {isSupabaseConfigured ? 'Configured' : 'Not Configured (Demo Mode)'}
          </span>
          <span>Discord Alerts:</span>
          <span className={process.env.DISCORD_WEBHOOK_URL ? 'text-green-400' : 'text-yellow-400'}>
            {process.env.DISCORD_WEBHOOK_URL ? 'Configured' : 'Not Configured'}
          </span>
        </div>
      </div>
    </div>
  );
}

const DEMO_ALERTS: AlertHistory[] = [
  {
    id: '1',
    alert_type: 'stuck_client',
    message: 'Bloom Florist stuck in AUDIT for 26h',
    sent_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    acknowledged: false,
  },
  {
    id: '2',
    alert_type: 'missing_agent',
    message: 'Executioner missing heartbeat (45m ago)',
    sent_at: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    acknowledged: true,
  },
];
