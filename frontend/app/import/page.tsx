'use client';

import { useRef, useState } from 'react';
import { CheckCircle2, TrendingUp, Upload } from 'lucide-react';
import { Button } from '@/components/Button';
import { ErrorBlock } from '@/components/StateBlocks';
import { importCsv, runAllScores } from '@/lib/api';
import { useApiBase } from '@/lib/useApiBase';
import type { ImportResult } from '@/lib/types';

export default function ImportPage() {
  const { apiBase, ready } = useApiBase();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scoreMessage, setScoreMessage] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  function pickFile(file: File | undefined | null) {
    if (!file) return;
    setSelectedFile(file);
    setResult(null);
    setError(null);
    setScoreMessage(null);
  }

  async function handleImport() {
    if (!selectedFile || !ready) return;
    setImporting(true);
    setError(null);
    try {
      const res = await importCsv(apiBase, selectedFile);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed.');
    } finally {
      setImporting(false);
    }
  }

  async function handleScoreNow() {
    setScoring(true);
    setScoreMessage(null);
    try {
      const res = await runAllScores(apiBase);
      setScoreMessage(`Scored ${res.scored} business${res.scored === 1 ? '' : 'es'}. Check the Leads page.`);
    } catch (err) {
      setScoreMessage(err instanceof Error ? err.message : 'Scoring failed.');
    } finally {
      setScoring(false);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <p className="eyebrow">Bring your own list</p>
        <h1 className="font-display text-2xl font-semibold text-fg mt-1">Import businesses</h1>
        <p className="mt-2 text-sm text-fg-muted leading-relaxed">
          Upload a CSV of businesses you&apos;ve already compiled — your own research, a CRM export,
          or data from a source you&apos;re permitted to use. Only <code className="font-data text-xs">name</code> is
          required; <code className="font-data text-xs">category</code>, <code className="font-data text-xs">city</code>,{' '}
          <code className="font-data text-xs">website</code>, <code className="font-data text-xs">rating</code>, and{' '}
          <code className="font-data text-xs">review_count</code> are recognized if present.
        </p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          pickFile(e.dataTransfer.files?.[0]);
        }}
        className={`plate flex flex-col items-center justify-center gap-3 px-6 py-12 text-center transition-colors ${
          dragOver ? 'border-signal/60 bg-signal/5' : ''
        }`}
      >
        <Upload size={28} className="text-fg-faint" />
        <div>
          <p className="text-sm text-fg">
            {selectedFile ? (
              <span className="font-data text-signal">{selectedFile.name}</span>
            ) : (
              'Drag a .csv file here, or choose one'
            )}
          </p>
          <p className="mt-1 text-xs text-fg-faint">CSV files only</p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => pickFile(e.target.files?.[0])}
        />
        <Button onClick={() => fileInputRef.current?.click()}>Choose file</Button>
      </div>

      <Button
        variant="primary"
        icon={<Upload size={15} />}
        loading={importing}
        disabled={!selectedFile || !ready}
        onClick={handleImport}
      >
        Import
      </Button>

      {error && <ErrorBlock message={error} onRetry={handleImport} />}

      {result && (
        <div className="plate p-4 border-circuit/30 flex items-start gap-3">
          <CheckCircle2 size={18} className="text-circuit shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-fg">
              Imported {result.imported} business{result.imported === 1 ? '' : 'es'}.
            </p>
            <p className="mt-1 text-xs text-fg-muted">
              Next: run scoring so they show up ranked on the Leads page.
            </p>
            <Button
              className="mt-3"
              icon={<TrendingUp size={14} />}
              loading={scoring}
              onClick={handleScoreNow}
            >
              Score all businesses now
            </Button>
            {scoreMessage && <p className="mt-2 text-xs text-fg-muted font-data">{scoreMessage}</p>}
          </div>
        </div>
      )}
    </div>
  );
}
