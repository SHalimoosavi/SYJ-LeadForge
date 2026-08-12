'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Download, Flag } from 'lucide-react';
import { Button } from '@/components/Button';
import { ScoreMeter } from '@/components/ScoreMeter';
import { EmptyBlock, ErrorBlock, LoadingBlock } from '@/components/StateBlocks';
import { TierBadge } from '@/components/TierBadge';
import { exportLeadsUrl, listLeads } from '@/lib/api';
import { TIER_ORDER } from '@/lib/types';
import { useApiBase } from '@/lib/useApiBase';
import { useAsync } from '@/lib/useAsync';

export default function LeadsPage() {
  const { apiBase, ready } = useApiBase();
  const [tier, setTier] = useState('');
  const [minScore, setMinScore] = useState('');
  const [expanded, setExpanded] = useState<number | null>(null);

  const params = {
    tier: tier || undefined,
    min_score: minScore ? Number(minScore) : undefined,
  };

  const {
    data: leads,
    error,
    loading,
    refresh,
  } = useAsync(() => listLeads(apiBase, params), [apiBase, tier, minScore], ready);

  function handleExport(format: 'csv' | 'json' | 'markdown') {
    const url = exportLeadsUrl(apiBase, format, params);
    const a = document.createElement('a');
    a.href = url;
    a.download = '';
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Ranked</p>
          <h1 className="font-display text-2xl font-semibold text-fg mt-1">Leads</h1>
        </div>
        <div className="flex gap-2">
          <Button icon={<Download size={14} />} onClick={() => handleExport('csv')}>
            CSV
          </Button>
          <Button icon={<Download size={14} />} onClick={() => handleExport('json')}>
            JSON
          </Button>
          <Button icon={<Download size={14} />} onClick={() => handleExport('markdown')}>
            Markdown
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          value={tier}
          onChange={(e) => setTier(e.target.value)}
          className="rounded border border-edge bg-surface-2 px-3 py-2 text-sm text-fg focus:border-signal/50"
        >
          <option value="">All tiers</option>
          {TIER_ORDER.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <input
          value={minScore}
          onChange={(e) => setMinScore(e.target.value.replace(/[^0-9]/g, ''))}
          placeholder="Min. score"
          inputMode="numeric"
          className="w-32 rounded border border-edge bg-surface-2 px-3 py-2 text-sm text-fg placeholder:text-fg-faint focus:border-signal/50"
        />
      </div>

      {loading && <LoadingBlock label="Loading leads…" />}
      {error && <ErrorBlock message={error} onRetry={refresh} />}

      {leads && !loading && !error && leads.length === 0 && (
        <EmptyBlock
          icon={<Flag size={28} />}
          title="No leads match these filters yet. Import businesses and run scoring from the Dashboard."
        />
      )}

      {leads && leads.length > 0 && (
        <div className="plate divide-y divide-edge/60">
          {leads.map((lead) => {
            const isOpen = expanded === lead.id;
            return (
              <div key={lead.id}>
                <button
                  type="button"
                  onClick={() => setExpanded(isOpen ? null : lead.id)}
                  className="w-full flex items-center gap-4 px-4 py-3.5 text-left hover:bg-surface transition-colors"
                >
                  <span className="text-fg-faint">
                    {isOpen ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-fg truncate">{lead.name}</p>
                    <p className="text-xs text-fg-muted truncate">
                      {[lead.category, lead.city].filter(Boolean).join(' · ') || 'No category or city on file'}
                    </p>
                  </div>
                  {lead.score ? (
                    <>
                      <TierBadge tier={lead.score.tier} />
                      <ScoreMeter score={lead.score.opportunity_score} stars={lead.score.stars} />
                    </>
                  ) : (
                    <span className="text-xs text-fg-faint font-data">not scored</span>
                  )}
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 pl-11 space-y-3">
                    {lead.score && (
                      <div>
                        <p className="eyebrow mb-1.5">Why this score</p>
                        <ul className="space-y-1">
                          {lead.score.reasons.map((reason, i) => (
                            <li key={i} className="text-xs text-fg-muted flex gap-2">
                              <span className="text-signal">·</span>
                              {reason}
                            </li>
                          ))}
                        </ul>
                        <p className="mt-2 text-xs text-fg-muted font-data">
                          Est. value: {lead.score.currency} {lead.score.estimated_value_low.toLocaleString()}
                          –{lead.score.estimated_value_high.toLocaleString()}
                        </p>
                      </div>
                    )}
                    {lead.audit && lead.audit.issues.length > 0 && (
                      <div>
                        <p className="eyebrow mb-1.5">Website issues</p>
                        <ul className="space-y-1">
                          {lead.audit.issues.map((issue, i) => (
                            <li key={i} className="text-xs text-fg-muted flex gap-2">
                              <span className="text-alert">·</span>
                              {issue}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {lead.website && (
                      <a
                        href={lead.website}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-block text-xs text-circuit hover:underline"
                      >
                        Visit website ↗
                      </a>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
