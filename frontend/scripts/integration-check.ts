/**
 * Integration check: exercises the ACTUAL frontend data layer
 * (lib/api.ts, unmodified — not a reimplementation) against a real,
 * running SYJ LeadForge backend. Complements unit-level type checking
 * with proof that the two sides of the contract actually agree.
 *
 * Requires a running backend. Typical usage:
 *   # terminal 1
 *   cd ../..  && LEADFORGE_HOME=/tmp/lf_demo uvicorn backend.main:app --port 8000
 *   # terminal 2
 *   cd frontend && API_BASE=http://127.0.0.1:8000 npm run test:integration
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import {
  ApiUnreachableError,
  checkHealth,
  exportLeadsUrl,
  getStats,
  importCsv,
  listBusinesses,
  listLeads,
  runAllScores,
} from '../lib/api';

const API_BASE = process.env.API_BASE || 'http://127.0.0.1:8000';
const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  console.log(`Testing lib/api.ts against live backend at ${API_BASE}\n`);

  const health = await checkHealth(API_BASE);
  assert.equal(health.status, 'ok');
  console.log(`  checkHealth() -> ${health.status}, v${health.version}`);

  // Build a real multipart File from the sample CSV, exactly like a
  // browser file input would produce.
  const csvPath = path.join(__dirname, '..', '..', 'sample_data', 'businesses_sample.csv');
  const csvBuffer = readFileSync(csvPath);
  const file = new File([csvBuffer], 'businesses_sample.csv', { type: 'text/csv' });

  const imported = await importCsv(API_BASE, file);
  assert.equal(imported.imported, 6);
  console.log(`  importCsv() -> imported ${imported.imported} businesses`);

  const businesses = await listBusinesses(API_BASE);
  assert.equal(businesses.length, 6);
  console.log(`  listBusinesses() -> ${businesses.length} businesses`);

  const scored = await runAllScores(API_BASE);
  assert.equal(scored.scored, 6);
  console.log(`  runAllScores() -> scored ${scored.scored} businesses`);

  const leads = await listLeads(API_BASE);
  assert.equal(leads.length, 6);
  const scores = leads.map((l) => l.score?.opportunity_score ?? 0);
  assert.deepEqual(scores, [...scores].sort((a, b) => b - a));
  console.log(`  listLeads() -> ${leads.length} leads, correctly sorted descending`);

  const excludedLeads = await listLeads(API_BASE, { tier: 'Excluded' });
  assert.ok(excludedLeads.every((l) => l.score?.tier === 'Excluded'));
  console.log(`  listLeads({tier: 'Excluded'}) -> ${excludedLeads.length} correctly filtered`);

  const stats = await getStats(API_BASE);
  assert.equal(stats.total_businesses, 6);
  assert.equal(stats.scored, 6);
  console.log(`  getStats() -> total=${stats.total_businesses} avg=${stats.average_score}`);

  const csvUrl = exportLeadsUrl(API_BASE, 'csv');
  const csvResp = await fetch(csvUrl);
  assert.equal(csvResp.status, 200);
  const csvText = await csvResp.text();
  assert.ok(csvText.includes('opportunity_score'));
  console.log(`  exportLeadsUrl('csv') -> fetched real CSV, ${csvText.split('\n').length} lines`);

  try {
    await checkHealth('http://127.0.0.1:1'); // nothing listens here
    throw new Error('expected ApiUnreachableError');
  } catch (err) {
    assert.ok(err instanceof ApiUnreachableError, `expected ApiUnreachableError, got ${err}`);
    console.log('  unreachable API correctly throws ApiUnreachableError');
  }

  const badBusinessResp = await fetch(`${API_BASE}/businesses/999999`);
  assert.equal(badBusinessResp.status, 404);
  console.log('  GET /businesses/999999 correctly 404s');

  console.log('\nAll frontend <-> backend integration checks passed.');
}

main().catch((err) => {
  console.error('\nFAILED:', err);
  process.exit(1);
});
