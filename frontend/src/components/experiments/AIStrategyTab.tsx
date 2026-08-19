import { useState } from 'react';
import { 
  Sparkles, RefreshCw, AlertCircle, ChevronDown, ChevronUp, 
  TrendingUp, Sliders, AlertTriangle, ArrowRight, CheckCircle2 
} from 'lucide-react';
import { generateExperimentStrategy } from '../../services/experiment-strategy.service';
import type { ExperimentStrategy, RecommendedNextExperiment } from '../../types/experiment-strategy.types';

interface AIStrategyTabProps {
  experimentId: string;
}

// ─── Skeleton Loader ──────────────────────────────────────────────────────────

function StrategySkeleton() {
  return (
    <div className="space-y-6 animate-pulse pb-12">
      <div className="h-16 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-4" />
      <div className="h-48 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-6" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="h-40 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)]" />
        <div className="h-40 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)]" />
        <div className="h-40 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)]" />
        <div className="h-40 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)]" />
      </div>
    </div>
  );
}

// ─── Helpers for Text Shaping & Formatting ────────────────────────────────────

function renderListItems(items: string[] | string | any[] | undefined): string[] {
  if (!items) return [];
  if (Array.isArray(items)) {
    return items.map(item => (typeof item === 'string' ? item : JSON.stringify(item)));
  }
  return items.split('\n').map(s => s.replace(/^[*-]\s*/, '').trim()).filter(Boolean);
}

function getShortSentence(text: string | undefined, maxLen = 230): string {
  if (!text) return 'Active experiment evaluation running normally.';
  // Split on periods followed by whitespace or end of string so decimals (like 0.813 or 81.3%) are not treated as ends of sentences!
  const sentences = text.split(/\.(?=\s|$)/);
  if (sentences[0] && sentences[0].length > 20 && sentences[0].length <= maxLen) {
    // Check if adding the second sentence still fits nicely
    if (sentences[1] && (sentences[0].length + sentences[1].length + 2) <= maxLen) {
      return `${sentences[0].trim()}. ${sentences[1].trim()}.`;
    }
    return `${sentences[0].trim()}.`;
  }
  if (text.length <= maxLen) return text;
  return text.substring(0, maxLen).trim() + '...';
}

function parseBestRunInfo(strongestModel: string | undefined): { title: string; subtitle: string } {
  if (!strongestModel || strongestModel === 'N/A' || strongestModel === 'None') {
    return { title: 'No champion yet', subtitle: 'Awaiting run evaluations' };
  }
  const matchRun = strongestModel.match(/(Run\s*#?\s*\d+)/i);
  if (matchRun) {
    const title = matchRun[1];
    let remainder = strongestModel.replace(matchRun[1], '').replace(/^[-(:]+|[-):]+$/g, '').trim();
    remainder = remainder.replace(/random_forest/i, 'Random Forest').replace(/logistic_regression/i, 'Logistic Regression').replace(/xgboost/i, 'XGBoost');
    remainder = remainder.replace(/\s*with parameters\s*\{[^}]+\}/i, '');
    remainder = remainder.replace(/\b0\.(\d{2,4})\b/g, (m) => {
      const val = parseFloat(m) * 100;
      return `${val.toFixed(1)}%`;
    });
    if (remainder.length > 55) remainder = remainder.substring(0, 52) + '...';
    return { title, subtitle: remainder || 'Top performing metric' };
  }
  let sub = strongestModel.replace(/random_forest/i, 'Random Forest').replace(/logistic_regression/i, 'Logistic Regression').replace(/xgboost/i, 'XGBoost').replace(/\s*with parameters\s*\{[^}]+\}/i, '');
  if (sub.length > 55) sub = sub.substring(0, 52) + '...';
  return { title: 'Best Run', subtitle: sub };
}

function cleanListItem(item: string, maxLen = 85): string {
  let cleaned = item
    .replace(/^Run\s*#?\d+\s*[:-]\s*/i, '')
    .replace(/^(Unexplored|Unvisited|Untested)\s*model\s*family\s*[:-]\s*/i, '')
    .replace(/^(Unvisited|Unexplored)\s*.*?(parameter region|search space)\s*[:-]\s*/i, '')
    .replace(/\b0\.(\d{2,4})\b/g, (m) => `${(parseFloat(m) * 100).toFixed(1)}%`);
  if (cleaned.length > maxLen) cleaned = cleaned.substring(0, maxLen).trim() + '...';
  return cleaned;
}

function strVal(val: any): string {
  if (typeof val === 'string') return val;
  if (val === null || val === undefined) return 'None specified.';
  return JSON.stringify(val);
}

// ─── Main Component (Linear / Vercel Redesign) ────────────────────────────────

export function AIStrategyTab({ experimentId }: AIStrategyTabProps) {
  const [strategy, setStrategy] = useState<ExperimentStrategy | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showFullAnalysis, setShowFullAnalysis] = useState<boolean>(false);

  const fetchStrategy = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await generateExperimentStrategy(experimentId);
      if (res.success && res.data) {
        setStrategy(res.data);
      } else {
        setError(res.message || 'Failed to generate AI Experiment Strategy.');
      }
    } catch (err: any) {
      setError(err?.message || 'An unexpected error occurred while generating strategy.');
    } finally {
      setIsLoading(false);
    }
  };



  // ── Loading State ─────────────────────────────────────────────────────────
  if (isLoading && !strategy) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3.5 bg-indigo-500/15 border border-indigo-500/30 rounded-2xl p-5 text-base text-indigo-200 shadow-md">
          <Sparkles className="text-indigo-400 animate-spin shrink-0 w-6 h-6" />
          <span className="font-medium">Synthesizing concise strategy from historical run metrics and search space...</span>
        </div>
        <StrategySkeleton />
      </div>
    );
  }

  // ── Initial Prompt State ──────────────────────────────────────────────────
  if (!strategy && !isLoading && !error) {
    return (
      <div className="rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-500/10 to-transparent p-10 text-center shadow-lg max-w-3xl mx-auto my-6">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/20 border border-indigo-400/40 shadow-md">
          <Sparkles className="text-indigo-400 w-7 h-7" />
        </div>
        <h3 className="text-lg font-extrabold text-[var(--color-text-primary)] mb-2 uppercase tracking-wider">AI Experiment Strategy Co-Pilot</h3>
        <p className="text-sm text-[var(--color-text-muted)] mb-8 max-w-xl mx-auto leading-relaxed font-medium">
          Synthesize an evidence-driven ML strategy from your historical run telemetry, dataset quality metrics, and search space coverage. Discover unexplored algorithm architectures and receive high-impact hyperparameter recommendations.
        </p>
        <button
          onClick={fetchStrategy}
          className="inline-flex items-center gap-2.5 rounded-xl bg-indigo-100 px-8 py-3.5 text-sm font-extrabold text-indigo-700 hover:bg-indigo-200 transition-all duration-200 shadow-xl shadow-indigo-500/30 cursor-pointer"
        >
          <Sparkles size={18} />
          Generate Experiment Strategy
        </button>
      </div>
    );
  }

  // ── Error State ───────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center max-w-xl mx-auto shadow-xl">
        <AlertCircle className="mx-auto mb-3 text-red-400 w-9 h-9" />
        <h3 className="text-base font-bold text-red-300 mb-2">Strategy Evaluation Failed</h3>
        <p className="text-sm text-[var(--color-text-muted)] mb-6 leading-relaxed">{error || 'Unable to evaluate experiment history.'}</p>
        <button
          onClick={fetchStrategy}
          className="inline-flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-6 py-2.5 text-sm font-semibold text-[var(--color-text-primary)] hover:bg-white/20 transition-all shadow-md cursor-pointer"
        >
          <RefreshCw size={15} />
          Retry Evaluation
        </button>
      </div>
    );
  }

  if (!strategy) return null;

  // ── Extract and Normalize Data ────────────────────────────────────────────
  const rec = (typeof strategy.recommended_next_experiment === 'object' && strategy.recommended_next_experiment !== null
    ? strategy.recommended_next_experiment
    : { action: strVal(strategy.recommended_next_experiment), rationale: 'Empirical analysis derived directly from run history.' }) as RecommendedNextExperiment;

  const confidence = strVal(strategy.confidence).trim();
  const getConfidenceBadge = (c: string) => {
    switch (c.toLowerCase()) {
      case 'high': 
        return { dot: '•', text: 'High', class: 'text-emerald-700 bg-emerald-100 border-emerald-300' };
      case 'medium': 
        return { dot: '•', text: 'Medium', class: 'text-amber-700 bg-amber-100 border-amber-300' };
      case 'low': 
        return { dot: '•', text: 'Low', class: 'text-rose-700 bg-rose-100 border-rose-300' };
      default: 
        return { dot: '•', text: c, class: 'text-indigo-700 bg-indigo-100 border-indigo-300' };
    }
  };
  const conf = getConfidenceBadge(confidence);

  const isPlateaued = strategy.evidence_summary?.trend_and_plateau_analysis?.plateau_detected || 
                      strategy.current_experiment_status.toLowerCase().includes('plateau') ||
                      rec.action?.toLowerCase().includes('stop') || rec.action?.toLowerCase().includes('terminat');

  const statusTitle = isPlateaued ? '[Plateau] Model has likely plateaued.' : '[Active] Experiment is progressing well.';
  const statusSummary = getShortSentence(strategy.overall_assessment);

  const bestRun = parseBestRunInfo(strategy.strongest_model);
  const trendsList = renderListItems(strategy.observed_trends);
  const learnedList = renderListItems(strategy.what_has_been_learned);
  const searchSpaceList = renderListItems(strategy.remaining_search_space);
  const risksList = renderListItems(strategy.potential_risks);
  const evidenceList = renderListItems(strategy.evidence_used);

  // Take punchy top items for the concise grid
  const punchyTrend = trendsList[0] ? cleanListItem(trendsList[0], 90) : (isPlateaued ? 'Performance plateaued across recent iterations.' : 'Metric gains observing steady trajectory.');
  const punchyInsights = learnedList.slice(0, 3).map(i => cleanListItem(i, 75));
  const punchyUnexplored = searchSpaceList.slice(0, 3).map(i => cleanListItem(i, 65));

  // Check stopping guidance wording for expanded view
  const stoppingText = strategy.evidence_summary?.trend_and_plateau_analysis?.stopping_guidance || '';
  const isContinueJustified = stoppingText.toLowerCase().includes('continued exploration') || stoppingText.toLowerCase().includes('justified') || !isPlateaued;

  return (
    <div className="space-y-6 animate-in fade-in duration-200 pb-16 font-sans text-text-primary">
      
      {/* ── Top Bar: Title & Status Banner ─────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2.5">
          <Sparkles className="w-5 h-5 text-indigo-400 shrink-0" />
          <h2 className="text-base font-bold text-[var(--color-text-primary)] tracking-wide uppercase">AI Experiment Strategy</h2>
        </div>
        <button
          onClick={fetchStrategy}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-2)] text-xs sm:text-sm font-semibold text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-2)] transition-all self-start sm:self-auto cursor-pointer shadow-sm"
        >
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          <span>Refresh Strategy</span>
        </button>
      </div>

      {/* ── Overall Assessment Banner (Linear style, high contrast) ────────── */}
      <div className="bg-white/[0.05] border border-[var(--color-border)] rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center gap-3.5 shadow-md">
        <span className="font-extrabold text-base text-[var(--color-text-primary)] whitespace-nowrap shrink-0 flex items-center gap-2">
          {statusTitle}
        </span>
        <p className="text-sm sm:text-base text-[var(--color-text-secondary)] leading-relaxed font-medium sm:border-l sm:border-[var(--color-border)] sm:pl-4 flex-1">
          {statusSummary}
        </p>
      </div>

      {/* ── Hero Recommendation Card ───────────────────────────────────────── */}
      <div className="rounded-2xl border border-indigo-500/40 bg-gradient-to-br from-indigo-100 via-purple-50 to-transparent p-6 sm:p-8 relative">
        <div className="flex flex-col xl:flex-row xl:items-start justify-between gap-6">
          <div className="space-y-3 flex-1">
            <span className="text-xs font-black tracking-widest uppercase text-indigo-700 block bg-indigo-100 px-2.5 py-1 rounded-md border border-indigo-200 w-fit">
              Recommendation
            </span>
            <h3 className="text-xl sm:text-2xl font-bold text-[var(--color-text-primary)] tracking-tight leading-snug">
              Next experiment: <span className="text-indigo-700 font-medium">{rec.action || 'Evaluate alternative estimator baselines.'}</span>
            </h3>
          </div>

          {/* Confidence & Reason Block (High Contrast, Larger Font) */}
          <div className="shrink-0 bg-white/60 border border-[var(--color-border)] rounded-xl p-5 max-w-md space-y-2.5 shadow-inner">
            <div className="flex items-center justify-between gap-4 text-sm font-bold">
              <span className="text-[var(--color-text-muted)] uppercase tracking-wider text-xs">Confidence:</span>
              <span className={`px-3 py-1 rounded-full border text-xs sm:text-sm font-extrabold inline-flex items-center gap-1.5 shadow-sm ${conf.class}`}>
                <span>{conf.dot}</span>
                <span>{conf.text}</span>
              </span>
            </div>
            <div className="text-xs sm:text-sm leading-relaxed text-[var(--color-text-secondary)] font-normal pt-1 border-t border-[var(--color-border)]">
              <span className="font-bold text-[var(--color-text-primary)] uppercase text-[11px] tracking-wider block mb-1">Empirical Rationale:</span> 
              {rec.rationale || 'Derived from current search space completion and iteration metrics.'}
            </div>
          </div>
        </div>

        {/* Suggested Configuration Bar (Crisp parameter badges) */}
        <div className="mt-8 pt-5 border-t border-[var(--color-border)] flex flex-col md:flex-row md:items-center gap-4">
          <span className="text-sm font-bold text-[var(--color-text-secondary)] flex items-center gap-2 shrink-0 uppercase tracking-wider">
            <Sliders size={15} className="text-indigo-400" /> Suggested Configuration:
          </span>
          <div className="flex flex-wrap items-center gap-2.5">
            {rec.model_type && (
              <span className="bg-indigo-100 text-indigo-700 border border-indigo-300 px-3.5 py-1.5 rounded-xl text-sm font-mono font-extrabold shadow-md">
                Model: {rec.model_type}
              </span>
            )}
            {rec.hyperparameters && Object.keys(rec.hyperparameters).length > 0 ? (
              Object.entries(rec.hyperparameters).map(([k, v]) => (
                <span key={k} className="bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-text-primary)] px-3 py-1.5 rounded-xl text-sm font-mono font-medium shadow-sm flex items-center gap-1.5">
                  <span className="text-gray-400">{k}:</span>
                  <span className="text-emerald-300 font-extrabold">{strVal(v)}</span>
                </span>
              ))
            ) : (
              <span className="text-sm text-gray-400 italic font-medium">Default estimator parameters suggested for initial baseline.</span>
            )}
          </div>
        </div>
      </div>

      {/* ── Concise 4-Column Scannable Grid (Larger font, higher contrast) ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 pt-2">
        
        {/* 1. Best Run */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-5 flex flex-col justify-between hover:bg-white/40 hover:border-indigo-400/40 transition-all shadow-md group">
          <div className="space-y-2">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block flex items-center gap-2"> Current Best Run
            </span>
            <div className="text-xl font-extrabold text-[var(--color-text-primary)] tracking-tight">{bestRun.title}</div>
            <div className="text-xs sm:text-sm text-[var(--color-text-secondary)] font-semibold mt-1 line-clamp-3" title={bestRun.subtitle}>
              {bestRun.subtitle}
            </div>
          </div>
          <div onClick={() => { const btns = Array.from(document.querySelectorAll('button')); const btn = btns.find(b => b.textContent?.includes('Runs')); if (btn) btn.click(); }} className="mt-5 pt-3 border-t border-[var(--color-border)] flex items-center justify-end text-sm font-bold text-[var(--color-text-muted)] hover:text-indigo-500 transition-colors cursor-pointer" title="Switch to Runs tab to inspect">
            <span>View in Runs tab</span>
            <ArrowRight size={15} className="ml-1" />
          </div>
        </div>

        {/* 2. Trend */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-5 flex flex-col justify-between hover:bg-white/40 transition-all shadow-md">
          <div className="space-y-2">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block flex items-center gap-2"> Trend
            </span>
            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed font-medium mt-1">
              {punchyTrend}
            </p>
          </div>
          {isPlateaued ? (
            <div className="mt-4 pt-3 border-t border-[var(--color-border)] text-xs sm:text-sm font-bold text-amber-400 flex items-center gap-1.5">
              <span> Diminishing returns reached</span>
            </div>
          ) : (
            <div className="mt-4 pt-3 border-t border-[var(--color-border)] text-xs sm:text-sm font-bold text-emerald-400 flex items-center gap-1.5">
              <span>🟢 Active improvement trajectory</span>
            </div>
          )}
        </div>

        {/* 3. Insights */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-5 flex flex-col justify-between hover:bg-white/40 transition-all shadow-md">
          <div>
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-3 flex items-center gap-2"> Insights
            </span>
            <ul className="space-y-2.5 text-xs sm:text-sm text-[var(--color-text-secondary)] font-medium">
              {punchyInsights.length > 0 ? (
                punchyInsights.map((ins, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="text-emerald-600 font-bold shrink-0 text-sm">»</span>
                    <span className="leading-snug text-[var(--color-text-secondary)]" title={ins}>{ins}</span>
                  </li>
                ))
              ) : (
                <li className="text-sm text-gray-400 italic">Awaiting run variance analysis.</li>
              )}
            </ul>
          </div>
        </div>

        {/* 4. Not Yet Explored */}
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-5 flex flex-col justify-between hover:bg-white/40 transition-all shadow-md">
          <div>
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-3 flex items-center gap-2"> Not Yet Explored
            </span>
            <ul className="space-y-2.5 text-xs sm:text-sm text-[var(--color-text-secondary)] font-medium">
              {punchyUnexplored.length > 0 ? (
                punchyUnexplored.map((ux, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="text-indigo-600 font-mono font-black shrink-0 text-sm">-</span>
                    <span className="leading-snug text-[var(--color-text-secondary)]" title={ux}>{ux}</span>
                  </li>
                ))
              ) : (
                <li className="text-sm text-gray-400 italic">Search space extensively probed.</li>
              )}
            </ul>
          </div>
        </div>

      </div>

      {/* ── Show Full Analysis Toggle Button ───────────────────────────────── */}
      <div className="flex justify-center pt-6">
        <button
          onClick={() => setShowFullAnalysis(!showFullAnalysis)}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-full border border-[var(--color-border)] bg-[var(--color-surface-2)] text-sm font-bold text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-gray-100 transition-all shadow-lg cursor-pointer"
        >
          <span>{showFullAnalysis ? 'Hide Full Analysis' : 'Show Full Analysis'}</span>
          {showFullAnalysis ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* ── Advanced Engineering Analysis Drawer (Only shown when toggled) ─── */}
      {showFullAnalysis && (
        <div className="mt-8 space-y-6 pt-8 border-t border-[var(--color-border)] animate-in slide-in-from-top-2 duration-200">
          
          <div className="text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
            Advanced Engineering Breakdown
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Full Trajectory & Stability Analysis */}
            <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 space-y-5 shadow-lg">
              <h4 className="text-base font-bold text-[var(--color-text-primary)] flex items-center gap-2.5 border-b border-[var(--color-border)] pb-3">
                <TrendingUp size={18} className="text-blue-400" />
                <span>Complete Trajectory & Stability</span>
              </h4>
              
              <div className="space-y-4 text-sm">
                <div>
                  <span className="text-gray-400 font-bold block mb-1 uppercase text-xs tracking-wider">Overall Assessment:</span>
                  <p className="text-[var(--color-text-secondary)] leading-relaxed font-normal">{strategy.overall_assessment}</p>
                </div>
                
                <div className="pt-3 border-t border-[var(--color-border)]">
                  <span className="text-gray-400 font-bold block mb-1.5 uppercase text-xs tracking-wider">Most Stable Model (Low Variance):</span>
                  <code className="text-emerald-300 font-mono block bg-[var(--color-surface-2)] px-3 py-2 rounded-lg border border-[var(--color-border)] text-sm font-semibold">
                    {strategy.most_stable_model || 'None evaluated yet'}
                  </code>
                </div>

                {stoppingText && (
                  <div className="pt-3 border-t border-[var(--color-border)]">
                    {isContinueJustified ? (
                      <div>
                        <span className="text-emerald-400 font-bold block flex items-center gap-1.5 mb-1 text-sm">
                          <CheckCircle2 size={16} className="text-emerald-400 shrink-0" /> Exploration Status:
                        </span>
                        <p className="text-[var(--color-text-secondary)] leading-relaxed font-medium pl-6">
                          {stoppingText}
                        </p>
                      </div>
                    ) : (
                      <div>
                        <span className="text-amber-400 font-bold block flex items-center gap-1.5 mb-1 text-sm">
                          <AlertTriangle size={16} className="text-amber-400 shrink-0" /> Stopping Guidance:
                        </span>
                        <p className="text-[var(--color-text-secondary)] leading-relaxed font-medium pl-6">
                          {stoppingText}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Potential Risks & Empirical Evidence Sources */}
            <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 space-y-5 shadow-lg flex flex-col justify-between">
              <div>
                <h4 className="text-base font-bold text-[var(--color-text-primary)] flex items-center gap-2.5 border-b border-[var(--color-border)] pb-3 mb-4">
                  <AlertCircle size={18} className="text-rose-400" />
                  <span>Potential Risks & Hazards</span>
                </h4>
                <ul className="space-y-3 text-sm text-[var(--color-text-secondary)] font-medium">
                  {risksList.length > 0 ? (
                    risksList.map((risk, i) => (
                      <li key={i} className="flex items-start gap-3 leading-relaxed">
                        <span className="text-rose-600 font-black shrink-0">!</span>
                        <span className="text-[var(--color-text-secondary)]">{risk}</span>
                      </li>
                    ))
                  ) : (
                    <li className="italic text-gray-400">No operational risks identified.</li>
                  )}
                </ul>
              </div>

              {evidenceList.length > 0 && (
                <div className="pt-5 mt-5 border-t border-[var(--color-border)]">
                  <span className="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider block mb-3"> Empirical Evidence Sources Utilized
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {evidenceList.map((ev, idx) => (
                      <span key={idx} className="bg-[var(--color-surface-2)] px-3 py-1 rounded-lg border border-[var(--color-border)] text-xs text-[var(--color-text-secondary)] font-mono font-medium shadow-sm">
                        {ev}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

          </div>
          
        </div>
      )}

    </div>
  );
}
