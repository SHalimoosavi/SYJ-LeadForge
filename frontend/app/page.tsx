'use client';

import { useState } from 'react';
import { Play, Search } from 'lucide-react';
import { Button } from '@/components/Button';
import { ErrorBlock, LoadingBlock } from '@/components/StateBlocks';
import { StatCard } from '@/components/StatCard';
import { TierBreakdownChart } from '@/components/TierBreakdownChart';
import { getStats, runAllAudits, runAllScores } from '@/lib/api';
import { useApiBase } from '@/lib/useApiBase';
import { useAsync } from '@/lib/useAsync';

export default function DashboardPage() {
  const { apiBase, ready } = useApiBase();
  const { data: stats, error, loading, refresh } = useAsync(
    () => getStats(apiBase),
    [apiBase],
    ready
  );

  const [auditRunning, setAuditRunning] = useState(false);
  const [scoreRunning, setScoreRunning] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  async function handleRunAudits() {
    setAuditRunning(true);
    setActionMessage(null);
    try {
      const result = await runAllAudits(apiBase);
      setActionMessage(`Audited ${result.audited} website${result.audited === 1 ? '' : 's'}.`);
      refresh();
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Audit run failed.');
    } finally {
      setAuditRunning(false);
    }
  }

  async function handleRunScores() {
    setScoreRunning(true);
    setActionMessage(null);
    try {
      const result = await runAllScores(apiBase);
      setActionMessage(`Scored ${result.scored} business${result.scored === 1 ? '' : 'es'}.`);
      refresh();
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Scoring run failed.');
    } finally {
      setScoreRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="eyebrow">Overview</p>
        <h1 className="font-display text-2xl font-semibold text-fg mt-1">Dashboard</h1>
      </div>

      {loading && <LoadingBlock label="Loading stats…" />}
      {error && <ErrorBlock message={error} onRetry={refresh} />}

      {stats && !loading && !error && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Businesses" value={stats.total_businesses} />
            <StatCard label="Audited" value={stats.audited} accent="circuit" />
            <StatCard label="Scored" value={stats.scored} accent="circuit" />
            <StatCard
              label="Avg. score"
              value={stats.average_score}
              accent="signal"
              hint="out of 100"
            />
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="plate p-5">
              <h2 className="font-display text-sm font-semibold text-fg mb-4">Tier breakdown</h2>
              {Object.keys(stats.tier_breakdown).length === 0 ? (
                <p className="text-sm text-fg-muted">
                  No businesses scored yet — run scoring below once you&apos;ve imported some leads.
                </p>
              ) : (
                <TierBreakdownChart breakdown={stats.tier_breakdown} />
              )}
            </div>

            <div className="plate p-5">
              <h2 className="font-display text-sm font-semibold text-fg mb-1">Batch actions</h2>
              <p className="text-xs text-fg-muted mb-4">
                Audit every business with a website, then recompute opportunity scores for everyone.
              </p>
              <div className="flex flex-wrap gap-2.5">
                <Button
                  variant="primary"
                  icon={<Search size={15} />}
                  loading={auditRunning}
                  onClick={handleRunAudits}
                >
                  Audit all websites
                </Button>
                <Button icon={<Play size={15} />} loading={scoreRunning} onClick={handleRunScores}>
                  Score all businesses
                </Button>
              </div>
              {actionMessage && (
                <p className="mt-3 text-xs text-fg-muted font-data">{actionMessage}</p>
              )}
              <p className="mt-4 text-[11px] text-fg-faint leading-relaxed">
                Auditing makes one HTTP request per business website — this can take a moment for
                large lists.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
