'use client';

import { useEffect, useState, useCallback } from 'react';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';
import type { KnowledgeBaseStats } from '@/lib/types';

interface AgentKnowledge {
  name: string;
  emoji: string;
  categories: {
    name: string;
    count: number;
    lastUpdated: string;
  }[];
  recentAdditions: string[];
}

function KnowledgeCard({ agent }: { agent: AgentKnowledge }) {
  const totalItems = agent.categories.reduce((sum, c) => sum + c.count, 0);
  
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-4xl">{agent.emoji}</span>
        <div>
          <h3 className="font-bold text-xl">{agent.name}</h3>
          <p className="text-sm text-gray-400">{totalItems} items total</p>
        </div>
      </div>
      
      <div className="space-y-3 mb-4">
        {agent.categories.map((cat, i) => (
          <div key={i} className="flex justify-between items-center bg-gray-900 rounded p-2">
            <span className="text-gray-300 text-sm">{cat.name}</span>
            <div className="text-right">
              <span className="font-bold text-blue-400">{cat.count}</span>
              <span className="text-xs text-gray-500 ml-2">
                {new Date(cat.lastUpdated).toLocaleDateString('en-AW')}
              </span>
            </div>
          </div>
        ))}
      </div>
      
      <div>
        <h4 className="text-xs font-medium text-gray-500 mb-2 uppercase">Recent Additions</h4>
        <ul className="space-y-1">
          {agent.recentAdditions.map((item, i) => (
            <li key={i} className="text-sm text-gray-400 flex items-start gap-2">
              <span className="text-green-400">+</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default function KnowledgePage() {
  const [knowledge, setKnowledge] = useState<KnowledgeBaseStats[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!isSupabaseConfigured || !supabase) {
      setKnowledge(DEMO_KNOWLEDGE);
      setLoading(false);
      return;
    }

    const { data } = await supabase
      .from('knowledge_base_stats')
      .select('*')
      .order('agent_name');

    if (data) setKnowledge(data);
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();

    if (!isSupabaseConfigured || !supabase) return;

    const channel = supabase
      .channel('knowledge_base_stats')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'knowledge_base_stats' }, () => {
        loadData();
      })
      .subscribe();

    return () => {
      if (supabase) supabase.removeChannel(channel);
    };
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  // Build agent knowledge objects from stats
  const agents: AgentKnowledge[] = [
    {
      name: 'Atlas',
      emoji: '🗺️',
      categories: knowledge.filter(k => k.agent_name === 'atlas').map(k => ({
        name: k.category,
        count: k.item_count,
        lastUpdated: k.last_updated,
      })),
      recentAdditions: [
        'SaaS pricing frameworks',
        'E-commerce automation patterns',
        'Restaurant lead qualifiers',
      ],
    },
    {
      name: 'Gandalf',
      emoji: '🧙',
      categories: knowledge.filter(k => k.agent_name === 'gandalf').map(k => ({
        name: k.category,
        count: k.item_count,
        lastUpdated: k.last_updated,
      })),
      recentAdditions: [
        'Supabase integration guide',
        'Vercel deployment checklist',
        'OpenAI API recipes',
      ],
    },
    {
      name: 'Executioner',
      emoji: '⚔️',
      categories: knowledge.filter(k => k.agent_name === 'executioner').map(k => ({
        name: k.category,
        count: k.item_count,
        lastUpdated: k.last_updated,
      })),
      recentAdditions: [
        'Next.js app templates',
        'Render deployment patterns',
        'Bug fix playbook v3',
      ],
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-gray-900 rounded-lg p-4">
        <p className="text-sm text-gray-400">
          Each agent maintains a knowledge base that grows with every task. Stats update automatically as agents learn.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map(agent => (
          <KnowledgeCard key={agent.name} agent={agent} />
        ))}
      </div>

      {agents.every(a => a.categories.length === 0) && !loading && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-4xl mb-4">🧠</p>
          <p>No knowledge base data yet</p>
          <p className="text-sm mt-2">Agents populate this as they work</p>
        </div>
      )}
    </div>
  );
}

const DEMO_KNOWLEDGE: KnowledgeBaseStats[] = [
  { id: '1', agent_name: 'atlas', category: 'Question Library', item_count: 47, last_updated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() },
  { id: '2', agent_name: 'atlas', category: 'Audit Frameworks', item_count: 12, last_updated: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString() },
  { id: '3', agent_name: 'gandalf', category: 'Tool Database', item_count: 89, last_updated: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString() },
  { id: '4', agent_name: 'gandalf', category: 'Integration Guides', item_count: 23, last_updated: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString() },
  { id: '5', agent_name: 'executioner', category: 'Build Patterns', item_count: 34, last_updated: new Date(Date.now() - 30 * 60 * 1000).toISOString() },
  { id: '6', agent_name: 'executioner', category: 'Mistake Log', item_count: 156, last_updated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() },
];
