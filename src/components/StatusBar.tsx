'use client';

import { useEffect, useState } from 'react';
import { isSupabaseConfigured } from '@/lib/supabase';

export default function StatusBar() {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-AW', { 
        hour: '2-digit', 
        minute: '2-digit',
        timeZone: 'Australia/Perth'
      }) + ' AWST');
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-4 text-sm text-gray-400">
      <span>{time}</span>
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isSupabaseConfigured ? 'bg-green-500' : 'bg-yellow-500'}`} />
        <span>Supabase {isSupabaseConfigured ? 'Connected' : 'Not Configured'}</span>
      </div>
    </div>
  );
}
