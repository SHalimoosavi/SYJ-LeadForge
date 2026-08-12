import type { Metadata, Viewport } from 'next';
import './globals.css';
import { Shell } from '@/components/Shell';
import { ServiceWorkerRegister } from '@/components/ServiceWorkerRegister';
import { withBasePath } from '@/lib/basePath';

export const metadata: Metadata = {
  title: 'SYJ LeadForge',
  description: 'Find website opportunities, qualify leads, and grow your freelance business.',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#0F141B',
};

// Runs before paint, in the <head>, so the correct theme class is on
// <html> before React hydrates — avoids a flash of the wrong theme.
// Wrapped in try/catch because localStorage can throw in some
// locked-down browsing contexts.
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = localStorage.getItem('leadforge.theme');
    var theme = stored === 'light' ? 'light' : 'dark';
    document.documentElement.classList.add(theme);
  } catch (e) {
    document.documentElement.classList.add('dark');
  }
})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
        <link rel="manifest" href={withBasePath('/manifest.json')} />
        <link rel="icon" href={withBasePath('/icons/icon-48.png')} sizes="48x48" />
        <link rel="apple-touch-icon" href={withBasePath('/icons/icon-192.png')} />
      </head>
      <body>
        <ServiceWorkerRegister />
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
