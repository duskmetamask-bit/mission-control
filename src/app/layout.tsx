import type { Metadata } from 'next';
import './globals.css';
import Nav from '@/components/Nav';
import StatusBar from '@/components/StatusBar';

export const metadata: Metadata = {
  title: 'Mission Control',
  description: 'EMVY Crew Operations Dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <header className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🎯</span>
              <h1 className="text-2xl font-bold">Mission Control</h1>
            </div>
            <StatusBar />
          </header>
          <Nav />
          <main className="mt-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
