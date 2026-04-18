import { NextResponse } from 'next/server';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';

export async function POST(request: Request) {
  try {
    const { name, business, stage } = await request.json();

    if (!isSupabaseConfigured || !supabase) {
      return NextResponse.json({ success: true, demo: true });
    }

    const now = new Date().toISOString();
    const { data, error } = await supabase
      .from('pipeline_jobs')
      .insert({
        client_name: name,
        business_type: business,
        stage,
        stage_entered_at: now,
        agent_working: null,
        last_updated: now,
        created_at: now,
      })
      .select()
      .single();

    if (error) throw error;

    return NextResponse.json({ success: true, data });
  } catch (error) {
    console.error('Create client error:', error);
    return NextResponse.json({ success: false, error: 'Failed to create client' }, { status: 500 });
  }
}
