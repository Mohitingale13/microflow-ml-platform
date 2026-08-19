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
  ChevronUp,
  TrendingUp,
  TrendingDown,
  Minus,
  Trophy,
  Lightbulb,
  AlertTriangle,
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

function cleanCompareSentence(text: string | undefined, maxLen = 150): string {
  if (!text) return 'Minimal architectural divergence detected.';
  let cleaned = text.replace(/^(Overall|Better|Winner|Key|Tradeoff|Next)[:-]\s*/i, '');
  const match = cleaned.match(/^.*?\.(?=\s|$)/);
  if (match && match[0].length > 25 && match[0].length <= maxLen) return match[0].trim();
  if (cleaned.length <= maxLen) return cleaned;
  return cleaned.substring(0, maxLen).trim() + '...';
}

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
      ? 'text-[var(--color-text-muted)]'
      : isPositive
      ? 'text-emerald-600'
      : 'text-red-400';

  return (
    <tr className="border-b border-[var(--color-border)]/50 last:border-0">
      <td className="py-2.5 pr-4 text-xs text-[var(--color-text-muted)] font-medium whitespace-nowrap">
        {d.metric}
      </td>
      <td className="py-2.5 pr-4 text-xs font-mono text-[var(--color-text-secondary)] text-center">
        {formatMetricValue(d.run_a_value, d.metric)}
      </td>
      <td className="py-2.5 pr-4 text-xs font-mono text-[var(--color-text-secondary)] text-center">
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
  const [showFullComparison, setShowFullComparison] = useState(false);

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
    setShowFullComparison(false);
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
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl shadow-2xl flex flex-col overflow-hidden">

        {/* ── Header ── */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-teal-100 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 id="compare-dialog-title" className="text-sm font-bold text-[var(--color-text-primary)]">
                AI Run Comparison
              </h2>
              <p className="text-xs text-[var(--color-text-muted)]">
                AI Powered · Select two completed runs
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-2)] transition-colors"
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
                  className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5"
                >
                  Run A — Baseline
                </label>
                <div className="relative">
                  <select
                    id="run-a-select"
                    value={runAId}
                    onChange={(e) => setRunAId(e.target.value)}
                    disabled={isLoading}
                    className="w-full appearance-none bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm rounded-lg px-3 py-2.5 pr-8 focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue/50 transition-colors disabled:opacity-50"
                  >
                    <option value="">Select a completed run…</option>
                    {completedRuns.map((r) => (
                      <option key={r.id} value={r.id} disabled={r.id === runBId}>
                        Run #{r.run_number} · {r.model_type ?? 'Unknown model'}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)] pointer-events-none" />
                </div>
              </div>

              {/* Run B */}
              <div>
                <label
                  htmlFor="run-b-select"
                  className="block text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5"
                >
                  Run B — Challenger
                </label>
                <div className="relative">
                  <select
                    id="run-b-select"
                    value={runBId}
                    onChange={(e) => setRunBId(e.target.value)}
                    disabled={isLoading}
                    className="w-full appearance-none bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm rounded-lg px-3 py-2.5 pr-8 focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue/50 transition-colors disabled:opacity-50"
                  >
                    <option value="">Select a completed run…</option>
                    {completedRuns.map((r) => (
                      <option key={r.id} value={r.id} disabled={r.id === runAId}>
                        Run #{r.run_number} · {r.model_type ?? 'Unknown model'}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)] pointer-events-none" />
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
            <div className="space-y-6 animate-in fade-in duration-200 text-[var(--color-text-primary)]">
              
              {/* Run pair header */}
              <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-[var(--color-border)]">
                <div className="text-xs text-[var(--color-text-muted)] font-medium">
                  <span className="font-bold text-[var(--color-text-primary)] bg-[var(--color-surface-2)] px-2.5 py-1 rounded-md border border-[var(--color-border)]">{runLabel(result.run_a_id)}</span>
                  <span className="mx-2 font-black text-purple-400">VS</span>
                  <span className="font-bold text-[var(--color-text-primary)] bg-[var(--color-surface-2)] px-2.5 py-1 rounded-md border border-[var(--color-border)]">{runLabel(result.run_b_id)}</span>
                </div>
                <button
                  onClick={handleReset}
                  className="text-xs font-bold text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] flex items-center gap-1.5 bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-2)] border border-[var(--color-border)] px-3 py-1.5 rounded-lg transition-all cursor-pointer shadow-sm"
                >
                  <RotateCcw className="w-3 h-3" /> New comparison
                </button>
              </div>

              {/* Hero Champion Verdict Card */}
              <div className="rounded-2xl border border-amber-500/40 bg-gradient-to-br from-amber-500/15 via-purple-500/10 to-transparent p-6 shadow-2xl relative flex flex-col md:flex-row md:items-center justify-between gap-5">
                <div className="space-y-2 flex-1">
                  <span className="text-xs font-black tracking-widest uppercase text-amber-300 block bg-amber-500/20 px-2.5 py-0.5 rounded border border-amber-400/30 w-fit flex items-center gap-1.5">
                    <Trophy size={14} className="text-amber-300" /> Champion Verdict
                  </span>
                  <h3 className="text-lg sm:text-xl font-extrabold text-[var(--color-text-primary)] tracking-tight leading-snug">
                    {result.better_run || 'Both runs achieved equivalent statistical performance.'}
                  </h3>
                  <p className="text-sm text-[var(--color-text-secondary)] font-medium leading-relaxed">
                    {cleanCompareSentence(result.overall_summary, 190)}
                  </p>
                </div>
                <div className="shrink-0 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-xl p-4 max-w-xs space-y-2 shadow-inner text-xs">
                  <span className="font-bold text-[var(--color-text-primary)] uppercase text-[11px] tracking-wider block flex items-center gap-1.5">
                    <Lightbulb size={13} className="text-indigo-600" /> Next Iteration Goal:
                  </span>
                  <p className="text-[var(--color-text-secondary)] font-medium leading-relaxed">
                    {cleanCompareSentence(result.next_recommendation, 130)}
                  </p>
                </div>
              </div>

              {/* Metric Comparison Table */}
              <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-5 shadow-md">
                <div className="flex items-center gap-2 mb-3 text-[var(--color-text-primary)] font-bold text-sm uppercase tracking-wider border-b border-[var(--color-border)] pb-2">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  <span>Metric Differentials</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[360px]">
                    <thead>
                      <tr className="border-b border-[var(--color-border)]">
                        <th className="pb-2 pr-4 text-left text-xs font-extrabold text-[var(--color-text-muted)] uppercase tracking-wider">
                          Metric Name
                        </th>
                        <th className="pb-2 pr-4 text-center text-xs font-extrabold text-[var(--color-text-muted)] uppercase tracking-wider">
                          Run A (Base)
                        </th>
                        <th className="pb-2 pr-4 text-center text-xs font-extrabold text-[var(--color-text-muted)] uppercase tracking-wider">
                          Run B (Challenger)
                        </th>
                        <th className="pb-2 text-right text-xs font-extrabold text-[var(--color-text-muted)] uppercase tracking-wider">
                          Net Delta
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--color-border)] font-medium">
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
              </div>

              {/* 2-Column Concise Developer Pros/Cons Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-4 flex flex-col justify-between shadow-md hover:bg-gray-50 transition-all">
                  <div className="space-y-1.5">
                    <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4 text-emerald-600" /> Key Architectural Gains
                    </span>
                    <p className="text-xs sm:text-sm font-medium text-[var(--color-text-secondary)] leading-relaxed">
                      {cleanCompareSentence(result.key_improvements, 150)}
                    </p>
                  </div>
                </div>
                <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-4 flex flex-col justify-between shadow-md hover:bg-gray-50 transition-all">
                  <div className="space-y-1.5">
                    <span className="text-xs font-bold text-amber-600 uppercase tracking-wider flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-600" /> Latency & Tradeoffs
                    </span>
                    <p className="text-xs sm:text-sm font-medium text-[var(--color-text-secondary)] leading-relaxed">
                      {cleanCompareSentence(result.tradeoffs, 150)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Toggle Complete Breakdown Drawer */}
              <div className="flex justify-center pt-2">
                <button
                  onClick={() => setShowFullComparison(!showFullComparison)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-[var(--color-border)] bg-[var(--color-surface-2)] text-xs sm:text-sm font-bold text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-white/15 transition-all shadow-md cursor-pointer"
                >
                  <span>{showFullComparison ? 'Hide Full Comparative Analysis' : 'Show Full Comparative Analysis'}</span>
                  {showFullComparison ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                </button>
              </div>

              {showFullComparison && (
                <div className="pt-5 border-t border-[var(--color-border)] space-y-4 animate-in slide-in-from-top-2 duration-200 text-sm">
                  <div className="bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-2xl p-5 space-y-4">
                    <div>
                      <span className="text-xs font-extrabold uppercase text-[var(--color-text-muted)] tracking-wider block mb-1">Full Executive Summary:</span>
                      <p className="text-[var(--color-text-secondary)] leading-relaxed font-normal">{result.overall_summary}</p>
                    </div>
                    <div className="pt-3 border-t border-[var(--color-border)]">
                      <span className="text-xs font-extrabold uppercase text-purple-600 tracking-wider block mb-1">Configuration Divergence Analysis:</span>
                      <p className="text-[var(--color-text-secondary)] leading-relaxed font-normal">{result.configuration_analysis}</p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-[var(--color-border)]">
                      <div>
                        <span className="text-xs font-extrabold uppercase text-emerald-600 tracking-wider block mb-1">Complete Improvements:</span>
                        <p className="text-[var(--color-text-secondary)] leading-relaxed font-normal">{result.key_improvements}</p>
                      </div>
                      <div>
                        <span className="text-xs font-extrabold uppercase text-amber-600 tracking-wider block mb-1">Complete Tradeoffs:</span>
                        <p className="text-[var(--color-text-secondary)] leading-relaxed font-normal">{result.tradeoffs}</p>
                      </div>
                    </div>
                    <div className="pt-3 border-t border-[var(--color-border)]">
                      <span className="text-xs font-extrabold uppercase text-blue-600 tracking-wider block mb-1">Next Step Strategy:</span>
                      <p className="text-[var(--color-text-secondary)] leading-relaxed font-normal">{result.next_recommendation}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Footer ── */}
        <div className="px-6 py-3 border-t border-[var(--color-border)] bg-[var(--color-surface)] shrink-0 flex items-center justify-between">
          <p className="text-[10px] text-[var(--color-text-muted)]">
            AI Powered Comparison
          </p>
          <button
            onClick={handleClose}
            className="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors font-medium px-3 py-1.5 rounded-md hover:bg-[var(--color-surface-2)]"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
