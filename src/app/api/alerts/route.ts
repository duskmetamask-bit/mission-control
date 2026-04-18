import { NextResponse } from 'next/server';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';

const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;

async function sendDiscordAlert(message: string) {
  if (!DISCORD_WEBHOOK_URL) {
    console.log('Discord webhook not configured, skipping alert:', message);
    return false;
  }

  try {
    const res = await fetch(DISCORD_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: message,
        username: 'Mission Control',
      }),
    });
    return res.ok;
  } catch (error) {
    console.error('Discord alert error:', error);
    return false;
  }
}

export async function GET() {
  if (!isSupabaseConfigured || !supabase) {
    return NextResponse.json({ alerts: [], demo: true });
  }

  const { data } = await supabase
    .from('alert_history')
    .select('*')
    .order('sent_at', { ascending: false })
    .limit(50);

  return NextResponse.json({ alerts: data || [] });
}

export async function POST(request: Request) {
  try {
    const { type, message, job_id, agent_name } = await request.json();
    const now = new Date().toISOString();

    // Check for duplicate alerts (same type, same target, within last hour)
    if (isSupabaseConfigured && supabase) {
      const cutoff = new Date(Date.now() - 60 * 60 * 1000).toISOString();
      const { data: existing } = await supabase
        .from('alert_history')
        .select('id')
        .eq('alert_type', type)
        .eq('message', message)
        .gt('sent_at', cutoff)
        .limit(1);

      if (existing && existing.length > 0) {
        return NextResponse.json({ success: true, duplicate: true });
      }

      // Save to alert history
      await supabase.from('alert_history').insert({
        alert_type: type,
        message,
        sent_at: now,
        acknowledged: false,
      });
    }

    // Send Discord alert
    const sent = await sendDiscordAlert(message);

    return NextResponse.json({ success: sent, alert_sent: sent });
  } catch (error) {
    console.error('Alert error:', error);
    return NextResponse.json({ success: false, error: 'Failed to send alert' }, { status: 500 });
  }
}
