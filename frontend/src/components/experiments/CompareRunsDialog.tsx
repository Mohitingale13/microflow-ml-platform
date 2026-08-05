/**
 * CompareRunsDialog.tsx
 *
 * Modal dialog that allows users to select two completed runs from an
 * experiment and generate an AI-powered comparison report.
 *
 * Props:
 *   isOpen        — controls dialog visibility
 *   onClose       — callback when the dialog should be dismissed
 *   experimentId  — the experiment whose completed runs are selectable
 *   runs          — list of all runs in the experiment (pre-fetched by parent)
 */

import { useState } from 'react';
import {
  X,
  Sparkles,
  ChevronDown,
  TrendingUp,
  TrendingDown,
  Minus,
  Trophy,
  Lightbulb,
  AlertTriangle,
  Settings,
  Loader2,
  RotateCcw,
} from 'lucide-react';
import { compareRuns } from '@/services/ai.service';
import type { AIComparisonResponse, MetricDelta } from '@/types/ai.types';
import type { RunListItem } from '@/types/experiment.types';

interface CompareRunsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  experimentId: string;
  runs: RunListItem[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatMetricValue(val: number | null, metric: string): string {
  if (val === null) return 'N/A';
  if (metric === 'Execution Time (s)') return `${val.toFixed(2)}s`;
  return `${(val * 100).toFixed(2)}%`;
}

function formatDelta(delta: MetricDelta): string {
  if (delta.delta === null) return '—';
  const metric = delta.metric;
  if (metric === 'Execution Time (s)') {
    return `${delta.delta >= 0 ? '+' : ''}${delta.delta.toFixed(2)}s`;
  }
  return `${delta.delta >= 0 ? '+' : ''}${(delta.delta * 100).toFixed(2)}%`;
}

function MetricRow({ d, isTime }: { d: MetricDelta; isTime: boolean }) {
  // For execution time, "down" means faster (better)
  const isPositive =
    d.direction === 'unavailable'
      ? null
      : isTime
      ? d.direction === 'down'
      : d.direction === 'up';

  const directionIcon =
    d.direction === 'up' ? (
      <TrendingUp className="w-4 h-4" />
    ) : d.direction === 'down' ? (
      <TrendingDown className="w-4 h-4" />
    ) : (
      <Minus className="w-4 h-4" />
    );

  const colorClass =
    isPositive === null
      ? 'text-text-muted'
      : isPositive
      ? 'text-emerald-400'
      : 'text-red-400';

  return (
    <tr className="border-b border-border/50 last:border-0">
      <td className="py-2.5 pr-4 text-xs text-text-muted font-medium whitespace-nowrap">
        {d.metric}
      </td>
      <td className="py-2.5 pr-4 text-xs font-mono text-text-secondary text-center">
        {formatMetricValue(d.run_a_value, d.metric)}
      </td>
      <td className="py-2.5 pr-4 text-xs font-mono text-text-secondary text-center">
        {formatMetricValue(d.run_b_value, d.metric)}
      </td>
      <td className={`py-2.5 text-xs font-mono font-semibold text-right ${colorClass}`}>
        <span className="inline-flex items-center justify-end gap-1">
          {directionIcon}
          {formatDelta(d)}
        </span>
      </td>
    </tr>
  );
}

function Section({
  icon,
  title,
  children,
  accent,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
  accent?: string;
}) {
  return (
    <div className={`bg-surface border rounded-lg p-4 ${accent || 'border-border'}`}>
      <div className="flex items-center gap-2 mb-3">
        <div className="text-text-muted">{icon}</div>
        <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider">
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function CompareRunsDialog({
  isOpen,
  onClose,
  runs,
}: CompareRunsDialogProps) {
  const completedRuns = runs.filter((r) => r.status === 'completed');

  const [runAId, setRunAId] = useState<string>('');
  const [runBId, setRunBId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIComparisonResponse | null>(null);

  if (!isOpen) return null;

  const canGenerate = runAId && runBId && runAId !== runBId && !isLoading;

  const runLabel = (id: string) => {
    const r = completedRuns.find((r) => r.id === id);
    if (!r) return '—';
    return `Run #${r.run_number} · ${r.model_type ?? 'Unknown model'}`;
  };

  const handleGenerate = async () => {
    if (!canGenerate) return;
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await compareRuns(runAId, runBId);
      if (response.success && response.data) {
        setResult(response.data);
      } else {
        setError(response.message || 'Comparison failed. Please try again.');
      }
    } catch (err: any) {
      const detail =
        err?.response?.data?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        'An unexpected error occurred. Please try again.';
      setError(detail);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  const handleClose = () => {
    setRunAId('');
    setRunBId('');
    setResult(null);
    setError(null);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="compare-dialog-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Panel */}
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-surface-dark border border-border rounded-2xl shadow-2xl flex flex-col overflow-hidden">

        {/* ── Header ── */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent-blue/10 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-accent-blue" />
            </div>
            <div>
              <h2 id="compare-dialog-title" className="text-sm font-bold text-text-primary">
                AI Run Comparison
              </h2>
              <p className="text-xs text-text-muted">
                AI Powered · Select two completed runs
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* ── Scrollable body ── */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          {/* ── Run selectors ── */}
          {!result && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Run A */}
              <div>
                <label
                  htmlFor="run-a-select"
                  className="block text-xs font-semibold text-text-muted uppercase tracking-wider mb-1.5"
                >
                  Run A — Baseline
                </label>
                <div className="relative">
                  <select
                    id="run-a-select"
                    value={runAId}
                    onChange={(e) => setRunAId(e.target.value)}
                    disabled={isLoading}
                    className="w-full appearance-none bg-surface border border-border text-text-primary text-sm rounded-lg px-3 py-2.5 pr-8 focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue/50 transition-colors disabled:opacity-50"
                  >
                    <option value="">Select a completed run…</option>
                    {completedRuns.map((r) => (
                      <option key={r.id} value={r.id} disabled={r.id === runBId}>
                        Run #{r.run_number} · {r.model_type ?? 'Unknown model'}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
                </div>
              </div>

              {/* Run B */}
              <div>
                <label
                  htmlFor="run-b-select"
                  className="block text-xs font-semibold text-text-muted uppercase tracking-wider mb-1.5"
                >
                  Run B — Challenger
                </label>
                <div className="relative">
                  <select
                    id="run-b-select"
                    value={runBId}
                    onChange={(e) => setRunBId(e.target.value)}
                    disabled={isLoading}
                    className="w-full appearance-none bg-surface border border-border text-text-primary text-sm rounded-lg px-3 py-2.5 pr-8 focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue/50 transition-colors disabled:opacity-50"
                  >
                    <option value="">Select a completed run…</option>
                    {completedRuns.map((r) => (
                      <option key={r.id} value={r.id} disabled={r.id === runAId}>
                        Run #{r.run_number} · {r.model_type ?? 'Unknown model'}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
                </div>
              </div>
            </div>
          )}

          {/* ── Generate button ── */}
          {!result && (
            <button
              id="generate-comparison-btn"
              onClick={handleGenerate}
              disabled={!canGenerate}
              className="w-full py-2.5 px-4 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all
                bg-accent-blue text-white hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing run comparison…
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Generate Comparison
                </>
              )}
            </button>
          )}

          {/* ── Error state ── */}
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
              <p className="font-semibold mb-1">Comparison Failed</p>
              <p className="text-xs opacity-90">{error}</p>
              <button
                onClick={handleGenerate}
                className="mt-3 text-xs font-medium text-red-400 hover:text-red-300 underline"
              >
                Retry
              </button>
            </div>
          )}

          {/* ── Results ── */}
          {result && (
            <div className="space-y-4">
              {/* Run pair header */}
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="text-xs text-text-muted">
                  <span className="font-semibold text-text-secondary">{runLabel(result.run_a_id)}</span>
                  <span className="mx-2 text-text-muted/50">vs</span>
                  <span className="font-semibold text-text-secondary">{runLabel(result.run_b_id)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleReset}
                    className="text-xs text-text-muted hover:text-text-primary flex items-center gap-1 transition-colors"
                  >
                    <RotateCcw className="w-3 h-3" /> New comparison
                  </button>
                </div>
              </div>

              {/* Overall Summary */}
              <Section
                icon={<Sparkles className="w-4 h-4" />}
                title="Overall Summary"
                accent="border-accent-blue/20 bg-accent-blue/5"
              >
                <p className="text-sm text-text-secondary leading-relaxed">
                  {result.overall_summary}
                </p>
              </Section>

              {/* Winner */}
              <Section
                icon={<Trophy className="w-4 h-4 text-amber-400" />}
                title="Better Run"
                accent="border-amber-500/20 bg-amber-500/5"
              >
                <p className="text-sm text-text-secondary leading-relaxed">
                  {result.better_run}
                </p>
              </Section>

              {/* Metric Comparison Table */}
              <Section
                icon={<TrendingUp className="w-4 h-4" />}
                title="Metric Comparison"
              >
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[360px]">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="pb-2 pr-4 text-left text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                          Metric
                        </th>
                        <th className="pb-2 pr-4 text-center text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                          Run A
                        </th>
                        <th className="pb-2 pr-4 text-center text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                          Run B
                        </th>
                        <th className="pb-2 text-right text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                          Delta
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.metric_deltas.map((d) => (
                        <MetricRow
                          key={d.metric}
                          d={d}
                          isTime={d.metric === 'Execution Time (s)'}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              </Section>

              {/* Key Improvements */}
              <Section
                icon={<TrendingUp className="w-4 h-4 text-emerald-400" />}
                title="Key Improvements"
                accent="border-emerald-500/20"
              >
                <p className="text-sm text-text-secondary leading-relaxed">
                  {result.key_improvements}
                </p>
              </Section>

              {/* Tradeoffs */}
              <Section
                icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
                title="Tradeoffs"
                accent="border-amber-500/20"
              >
                <p className="text-sm text-text-secondary leading-relaxed">
                  {result.tradeoffs}
                </p>
              </Section>

              {/* Configuration Analysis */}
              <Section
                icon={<Settings className="w-4 h-4" />}
                title="Configuration Analysis"
              >
                <p className="text-sm text-text-secondary leading-relaxed">
                  {result.configuration_analysis}
                </p>
              </Section>

              {/* Next Recommendation */}
              <Section
                icon={<Lightbulb className="w-4 h-4 text-accent-blue" />}
                title="Next Recommendation"
                accent="border-accent-blue/20 bg-accent-blue/5"
              >
                <p className="text-sm text-text-secondary leading-relaxed">
                  {result.next_recommendation}
                </p>
              </Section>
            </div>
          )}
        </div>

        {/* ── Footer ── */}
        <div className="px-6 py-3 border-t border-border bg-surface shrink-0 flex items-center justify-between">
          <p className="text-[10px] text-text-muted">
            AI Powered Comparison
          </p>
          <button
            onClick={handleClose}
            className="text-sm text-text-muted hover:text-text-primary transition-colors font-medium px-3 py-1.5 rounded-md hover:bg-surface-2"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
