'use client';

import { useEffect, useState } from 'react';
import { CheckCircle2, Save, XCircle } from 'lucide-react';
import { Button } from '@/components/Button';
import { checkHealth } from '@/lib/api';
import { DEFAULT_API_BASE } from '@/lib/apiBase';
import { useApiBase } from '@/lib/useApiBase';

export default function SettingsPage() {
  const { apiBase, setApiBase, ready } = useApiBase();
  const [draft, setDraft] = useState(apiBase);
  const [testState, setTestState] = useState<'idle' | 'testing' | 'ok' | 'fail'>('idle');
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Sync the editable draft from the async-loaded (localStorage) API
    // base exactly once it's ready. `draft` is intentionally separate,
    // user-editable state after that — not something useMemo could
    // derive — so this one-time sync-on-ready is the correct pattern.
    if (ready) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDraft(apiBase);
    }
  }, [ready, apiBase]);

  function handleSave() {
    setApiBase(draft);
    setSaved(true);
    setTestState('idle');
    setTimeout(() => setSaved(false), 2000);
  }

  async function handleTest() {
    setTestState('testing');
    setTestMessage(null);
    try {
      const health = await checkHealth(draft.trim().replace(/\/+$/, '') || DEFAULT_API_BASE);
      setTestState('ok');
      setTestMessage(`Connected — API version ${health.version}`);
    } catch (err) {
      setTestState('fail');
      setTestMessage(err instanceof Error ? err.message : 'Could not reach the API.');
    }
  }

  return (
    <div className="space-y-8 max-w-xl">
      <div>
        <p className="eyebrow">Configuration</p>
        <h1 className="font-display text-2xl font-semibold text-fg mt-1">Settings</h1>
      </div>

      <section className="plate p-5 space-y-4">
        <div>
          <h2 className="font-display text-sm font-semibold text-fg">API URL</h2>
          <p className="mt-1 text-xs text-fg-muted leading-relaxed">
            This dashboard is a static app with no server of its own — it talks directly to your
            SYJ LeadForge API from your browser. Point it at wherever that API is running, e.g.{' '}
            <code className="font-data">http://127.0.0.1:8000</code> for a local instance.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-2">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={DEFAULT_API_BASE}
            className="flex-1 rounded border border-edge bg-surface-2 px-3 py-2 text-sm font-data text-fg placeholder:text-fg-faint focus:border-signal/50"
          />
          <div className="flex gap-2">
            <Button icon={<Save size={14} />} onClick={handleSave}>
              {saved ? 'Saved' : 'Save'}
            </Button>
            <Button
              variant="primary"
              loading={testState === 'testing'}
              onClick={handleTest}
            >
              Test
            </Button>
          </div>
        </div>

        {testState === 'ok' && (
          <p className="flex items-center gap-2 text-xs text-circuit">
            <CheckCircle2 size={14} /> {testMessage}
          </p>
        )}
        {testState === 'fail' && (
          <p className="flex items-center gap-2 text-xs text-alert">
            <XCircle size={14} /> {testMessage}
          </p>
        )}
      </section>

      <section className="plate p-5 space-y-2">
        <h2 className="font-display text-sm font-semibold text-fg">About</h2>
        <p className="text-xs text-fg-muted leading-relaxed">
          SYJ LeadForge is local-first and privacy-respecting: your business data lives in your
          own SQLite database on your own machine (or wherever you host the API), not in this
          dashboard or in any third-party service. This dashboard itself stores only your API URL
          and theme preference, in your browser&apos;s local storage.
        </p>
      </section>
    </div>
  );
}
