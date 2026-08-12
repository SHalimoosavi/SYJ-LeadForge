'use client';

import { useState } from 'react';
import { Building2, Search, TrendingUp } from 'lucide-react';
import { Button } from '@/components/Button';
import { EmptyBlock, ErrorBlock, LoadingBlock } from '@/components/StateBlocks';
import { auditBusiness, listBusinesses, scoreBusiness } from '@/lib/api';
import { useApiBase } from '@/lib/useApiBase';
import { useAsync } from '@/lib/useAsync';

export default function BusinessesPage() {
  const { apiBase, ready } = useApiBase();
  const [category, setCategory] = useState('');
  const [city, setCity] = useState('');
  const [rowBusy, setRowBusy] = useState<Record<number, 'audit' | 'score' | null>>({});
  const [rowMessage, setRowMessage] = useState<Record<number, string>>({});

  const {
    data: businesses,
    error,
    loading,
    refresh,
  } = useAsync(() => listBusinesses(apiBase, { category, city }), [apiBase, category, city], ready);

  async function handleAudit(id: number) {
    setRowBusy((s) => ({ ...s, [id]: 'audit' }));
    try {
      const result = await auditBusiness(apiBase, id);
      setRowMessage((s) => ({
        ...s,
        [id]: result.reachable ? `Audited: ${result.overall_score}/100` : `Unreachable: ${result.error}`,
      }));
    } catch (err) {
      setRowMessage((s) => ({ ...s, [id]: err instanceof Error ? err.message : 'Audit failed' }));
    } finally {
      setRowBusy((s) => ({ ...s, [id]: null }));
    }
  }

  async function handleScore(id: number) {
    setRowBusy((s) => ({ ...s, [id]: 'score' }));
    try {
      const result = await scoreBusiness(apiBase, id);
      setRowMessage((s) => ({ ...s, [id]: `Scored: ${result.opportunity_score}/100 (${result.tier})` }));
    } catch (err) {
      setRowMessage((s) => ({ ...s, [id]: err instanceof Error ? err.message : 'Scoring failed' }));
    } finally {
      setRowBusy((s) => ({ ...s, [id]: null }));
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="eyebrow">Records</p>
        <h1 className="font-display text-2xl font-semibold text-fg mt-1">Businesses</h1>
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Filter by category"
          className="rounded border border-edge bg-surface-2 px-3 py-2 text-sm text-fg placeholder:text-fg-faint focus:border-signal/50"
        />
        <input
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="Filter by city"
          className="rounded border border-edge bg-surface-2 px-3 py-2 text-sm text-fg placeholder:text-fg-faint focus:border-signal/50"
        />
      </div>

      {loading && <LoadingBlock label="Loading businesses…" />}
      {error && <ErrorBlock message={error} onRetry={refresh} />}

      {businesses && !loading && !error && businesses.length === 0 && (
        <EmptyBlock
          icon={<Building2 size={28} />}
          title="No businesses match yet. Import a CSV to get started, or clear your filters."
        />
      )}

      {businesses && businesses.length > 0 && (
        <div className="plate overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-edge text-left eyebrow">
                <th className="px-4 py-3 font-normal">Name</th>
                <th className="px-4 py-3 font-normal">Category</th>
                <th className="px-4 py-3 font-normal">City</th>
                <th className="px-4 py-3 font-normal">Website</th>
                <th className="px-4 py-3 font-normal text-right">Rating</th>
                <th className="px-4 py-3 font-normal text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {businesses.map((b) => (
                <tr key={b.id} className="border-b border-edge/60 last:border-0">
                  <td className="px-4 py-3 text-fg font-medium">{b.name}</td>
                  <td className="px-4 py-3 text-fg-muted">{b.category || '—'}</td>
                  <td className="px-4 py-3 text-fg-muted">{b.city || '—'}</td>
                  <td className="px-4 py-3 text-fg-muted">
                    {b.website ? (
                      <a
                        href={b.website}
                        target="_blank"
                        rel="noreferrer"
                        className="text-circuit hover:underline"
                      >
                        {b.website.replace(/^https?:\/\//, '')}
                      </a>
                    ) : (
                      <span className="text-fg-faint">none</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-data text-fg-muted tabular-nums">
                    {b.rating > 0 ? `${b.rating}★ (${b.review_count})` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1.5">
                      <Button
                        variant="ghost"
                        icon={<Search size={13} />}
                        loading={rowBusy[b.id] === 'audit'}
                        disabled={!b.website || rowBusy[b.id] === 'score'}
                        onClick={() => handleAudit(b.id)}
                        title={b.website ? 'Audit this website' : 'No website to audit'}
                      >
                        Audit
                      </Button>
                      <Button
                        variant="ghost"
                        icon={<TrendingUp size={13} />}
                        loading={rowBusy[b.id] === 'score'}
                        disabled={rowBusy[b.id] === 'audit'}
                        onClick={() => handleScore(b.id)}
                      >
                        Score
                      </Button>
                    </div>
                    {rowMessage[b.id] && (
                      <p className="mt-1 text-right text-[11px] text-fg-faint font-data">
                        {rowMessage[b.id]}
                      </p>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
