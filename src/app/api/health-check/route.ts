import { NextResponse } from 'next/server';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';

export async function POST() {
  try {
    if (!isSupabaseConfigured || !supabase) {
      return NextResponse.json({ 
        success: true, 
        demo: true,
        message: 'Demo mode - health check simulated'
      });
    }

    // Update all agent heartbeats to now (triggers a "ping" response in agents)
    const now = new Date().toISOString();
    
    // In a real system, agents would respond to a ping
    // This just confirms the system is reachable
    const { data, error } = await supabase
      .from('agent_status')
      .select('agent_name, last_heartbeat');

    if (error) throw error;

    return NextResponse.json({
      success: true,
      agents: data,
      timestamp: now,
    });
  } catch (error) {
    console.error('Health check error:', error);
    return NextResponse.json({ success: false, error: 'Health check failed' }, { status: 500 });
  }
}
