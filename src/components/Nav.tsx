'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { View } from '@/lib/types';

const navItems: { view: View; label: string; emoji: string }[] = [
  { view: 'pipeline', label: 'Pipeline', emoji: '📊' },
  { view: 'current-work', label: 'Current Work', emoji: '⚡' },
  { view: 'knowledge', label: 'Knowledge', emoji: '🧠' },
  { view: 'actions', label: 'Actions', emoji: '🚀' },
];

export default function Nav() {
  const pathname = usePathname();
  const currentView = pathname.split('/')[1] || 'pipeline';

  return (
    <nav className="flex gap-2 overflow-x-auto pb-2">
      {navItems.map(({ view, label, emoji }) => (
        <Link
          key={view}
          href={`/${view}`}
          className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors ${
            currentView === view
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          }`}
        >
          <span className="mr-2">{emoji}</span>
          {label}
        </Link>
      ))}
    </nav>
  );
}
