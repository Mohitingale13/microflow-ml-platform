import { useState, useEffect } from 'react';
import { 
  Sparkles, Brain, TrendingUp, AlertTriangle, Target, Layers, 
  BarChart2, ShieldAlert, ArrowRightCircle, RefreshCw, Clock, Cpu, AlertCircle 
} from 'lucide-react';
import { analyzeDataset } from '../../services/dataset-ai.service';
import type { DatasetAIAnalysis, RecommendedModel, FeatureObservation } from '../../types/dataset-ai.types';

interface AIInsightsTabProps {
  datasetId: string;
}

// ─── Skeleton Loader ──────────────────────────────────────────────────────────

function InsightsSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 lg:col-span-1">
          <div className="h-4 w-36 rounded bg-white/10 mb-4" />
          <div className="h-16 w-16 rounded-full bg-white/10 mb-4" />
          <div className="h-3 w-full rounded bg-white/10 mb-2" />
          <div className="h-3 w-3/4 rounded bg-white/10" />
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 lg:col-span-2">
          <div className="h-4 w-44 rounded bg-white/10 mb-4" />
          <div className="space-y-2">
            <div className="h-3 w-full rounded bg-white/10" />
            <div className="h-3 w-11/12 rounded bg-white/10" />
            <div className="h-3 w-5/6 rounded bg-white/10" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 h-40" />
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 h-40" />
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 p-6 h-64" />
    </div>
  );
}

// ─── Helper for formatting arrays or strings ─────────────────────────────────

function renderListItems(items: string[] | string | undefined): string[] {
  if (!items) return [];
  if (Array.isArray(items)) return items;
  return items.split('\n').map(s => s.replace(/^- /, '').trim()).filter(Boolean);
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function AIInsightsTab({ datasetId }: AIInsightsTabProps) {
  const [analysis, setAnalysis] = useState<DatasetAIAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInsights = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await analyzeDataset(datasetId);
      if (res.success && res.data) {
        setAnalysis(res.data);
      } else {
        setError(res.message || 'Failed to load AI Dataset Intelligence.');
      }
    } catch (err: any) {
      setError(err?.message || 'An unexpected error occurred while generating dataset intelligence.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, [datasetId]);

  // ── Loading state ─────────────────────────────────────────────────────────
  if (isLoading && !analysis) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3 bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 rounded-xl p-4">
          <Sparkles className="text-purple-400 animate-spin" size={20} />
          <div>
            <h3 className="text-sm font-medium text-text-primary">Analyzing Dataset Quality & Schema...</h3>
            <p className="text-xs text-text-muted">MicroFlow AI is evaluating features, target candidates, and algorithms.</p>
          </div>
        </div>
        <InsightsSkeleton />
      </div>
    );
  }

  // ── Error state ───────────────────────────────────────────────────────────
  if (error || (!analysis && !isLoading)) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center max-w-xl mx-auto">
        <AlertCircle className="mx-auto mb-4 text-red-400" size={32} />
        <h3 className="text-base font-semibold text-red-400 mb-2">Analysis Generation Failed</h3>
        <p className="text-sm text-text-muted mb-6">{error || 'Unable to analyze dataset.'}</p>
        <button
          onClick={fetchInsights}
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-2.5 text-sm font-medium text-white hover:bg-white/10 transition-all"
        >
          <RefreshCw size={14} />
          Retry Analysis
        </button>
      </div>
    );
  }

  if (!analysis) return null;

  // Extract Quality information safely
  const quality = analysis.dataset_quality || { score: 0, label: 'Unknown', explanation: '' };
  const qualityScore = typeof quality.score === 'number' ? quality.score : parseInt(quality.score, 10) || 75;
  const qualityLabel = quality.label || 'Good';

  // Determine accent color for quality gauge
  const getQualityStyle = (label: string) => {
    switch (label.toLowerCase()) {
      case 'excellent': return { color: 'text-emerald-400', border: 'border-emerald-500/30', bg: 'bg-emerald-500/10', bar: 'bg-emerald-400' };
      case 'good': return { color: 'text-blue-400', border: 'border-blue-500/30', bg: 'bg-blue-500/10', bar: 'bg-blue-400' };
      case 'fair': return { color: 'text-amber-400', border: 'border-amber-500/30', bg: 'bg-amber-500/10', bar: 'bg-amber-400' };
      default: return { color: 'text-red-400', border: 'border-red-500/30', bg: 'bg-red-500/10', bar: 'bg-red-400' };
    }
  };
  const qStyle = getQualityStyle(qualityLabel);

  const formattedDate = new Date(analysis.generated_at).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });

  const strengthsList = renderListItems(analysis.strengths);
  const issuesList = renderListItems(analysis.potential_issues);
  const preprocessingList = renderListItems(analysis.recommended_preprocessing);
  const nextStepsList = renderListItems(analysis.next_steps);

  const modelsList: RecommendedModel[] = Array.isArray(analysis.recommended_models)
    ? (analysis.recommended_models as RecommendedModel[])
    : [];

  const observationsList: FeatureObservation[] = Array.isArray(analysis.feature_observations)
    ? (analysis.feature_observations as FeatureObservation[])
    : [];

  return (
    <div className="space-y-6">
      {/* Header & Control Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-surface border border-border rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30">
            <Sparkles className="text-purple-400" size={20} />
          </div>
          <div>
            <h2 className="text-base font-semibold text-text-primary">AI Dataset Intelligence</h2>
            <p className="text-xs text-text-muted">Automated pre-training data auditing and engineering recommendations</p>
          </div>
        </div>
        <button
          onClick={fetchInsights}
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-text-muted hover:text-white hover:bg-white/10 transition-all self-start sm:self-center"
        >
          <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
          {isLoading ? 'Updating...' : 'Re-evaluate'}
        </button>
      </div>

      {/* Quality Gauge and Executive Summary Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dataset Quality Card */}
        <div className={`rounded-2xl border ${qStyle.border} ${qStyle.bg} p-6 flex flex-col justify-between`}>
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">Quality Score</span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${qStyle.border} ${qStyle.color} bg-white/5`}>
                {qualityLabel}
              </span>
            </div>
            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-5xl font-extrabold text-text-primary tracking-tight">{qualityScore}</span>
              <span className="text-text-muted text-sm font-medium">/ 100</span>
            </div>
            {/* Progress Bar */}
            <div className="w-full bg-black/30 h-2.5 rounded-full overflow-hidden mb-4 border border-white/5">
              <div 
                className={`h-full ${qStyle.bar} transition-all duration-1000 ease-out`} 
                style={{ width: `${Math.min(100, Math.max(0, qualityScore))}%` }}
              />
            </div>
          </div>
          <p className="text-xs text-text-muted leading-relaxed">
            {quality.explanation || 'Determined via missing value ratios, sample size adequacy, and dimensional richness.'}
          </p>
        </div>

        {/* Overall Summary Card */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3 text-purple-400">
              <Brain size={18} />
              <span className="text-xs uppercase tracking-[0.15em] font-semibold text-text-muted">Executive Summary</span>
            </div>
            <p className="text-sm text-text-primary leading-relaxed font-normal mb-6">
              {analysis.overall_summary}
            </p>
          </div>

          {/* Recommended Target Highlight Box */}
          <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-4">
            <div className="flex items-center gap-2 mb-1 text-blue-400">
              <Target size={16} />
              <span className="text-xs font-semibold uppercase tracking-wider">Recommended Target Variable</span>
            </div>
            <p className="text-sm font-medium text-white">
              {analysis.recommended_target}
            </p>
          </div>
        </div>
      </div>

      {/* Strengths & Potential Issues (Mobile-first stacked, Desktop side-by-side) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <div className="flex items-center gap-2 mb-4 text-emerald-400">
            <TrendingUp size={18} />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-primary">Key Data Strengths</h3>
          </div>
          <ul className="space-y-3">
            {strengthsList.map((str, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm text-gray-300">
                <span className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold mt-0.5">✓</span>
                <span>{str}</span>
              </li>
            ))}
            {strengthsList.length === 0 && <li className="text-sm text-text-muted">No specific strengths listed.</li>}
          </ul>
        </div>

        {/* Potential Issues */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <div className="flex items-center gap-2 mb-4 text-amber-400">
            <AlertTriangle size={18} />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-primary">Potential Issues & Risks</h3>
          </div>
          <ul className="space-y-3">
            {issuesList.map((issue, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm text-gray-300">
                <span className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-500/10 text-amber-400 text-xs font-bold mt-0.5">!</span>
                <span>{issue}</span>
              </li>
            ))}
            {issuesList.length === 0 && <li className="text-sm text-text-muted">No critical issues detected.</li>}
          </ul>
        </div>
      </div>

      {/* Suggested Models Grid */}
      {modelsList.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <div className="flex items-center gap-2 mb-4 text-blue-400">
            <Layers size={18} />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-primary">Recommended ML Models</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {modelsList.map((mod, idx) => {
              const suitability = mod.suitability?.toLowerCase() || '';
              const badgeColor = suitability === 'high' ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                : suitability === 'medium' ? 'text-blue-400 bg-blue-500/10 border-blue-500/30'
                : 'text-amber-400 bg-amber-500/10 border-amber-500/30';

              return (
                <div key={idx} className="rounded-xl border border-white/10 bg-black/20 p-4 flex flex-col justify-between hover:border-white/20 transition-colors">
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="font-semibold text-text-primary text-sm">{mod.model}</span>
                      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${badgeColor}`}>
                        {mod.suitability || 'Viable'}
                      </span>
                    </div>
                    <p className="text-xs text-text-muted leading-relaxed mt-2">{mod.reasoning}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommended Preprocessing Checklist */}
      {preprocessingList.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <div className="flex items-center gap-2 mb-4 text-purple-400">
            <BarChart2 size={18} />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-primary">Recommended Preprocessing</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {preprocessingList.map((prep, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-xl border border-white/5 bg-white/[0.02]">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-purple-500/20 text-purple-300 text-xs font-bold border border-purple-500/30">
                  {idx + 1}
                </span>
                <span className="text-sm text-gray-300 mt-0.5">{prep}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feature Observations Table */}
      {observationsList.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-primary flex items-center gap-2">
              <BarChart2 size={18} className="text-blue-400" /> Feature-Level Observations
            </h3>
            <span className="text-xs text-text-muted">{observationsList.length} features analyzed</span>
          </div>
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-2 border-b border-border">
                  <th className="px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider w-1/3">Feature Name</th>
                  <th className="px-4 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Engineering Observation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)] text-sm">
                {observationsList.map((obs, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="px-4 py-3 font-mono font-medium text-text-primary">{obs.feature}</td>
                    <td className="px-4 py-3 text-gray-300 leading-relaxed">{obs.observation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Risk Assessment & Next Steps Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Assessment */}
        {analysis.risk_assessment && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6 lg:col-span-1 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-3 text-red-400">
                <ShieldAlert size={18} />
                <span className="text-sm font-semibold uppercase tracking-wider">Risk Assessment</span>
              </div>
              <p className="text-sm text-gray-300 leading-relaxed">
                {analysis.risk_assessment}
              </p>
            </div>
          </div>
        )}

        {/* Recommended Next Steps */}
        <div className={`rounded-2xl border border-white/10 bg-white/5 p-6 ${analysis.risk_assessment ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          <div className="flex items-center gap-2 mb-4 text-emerald-400">
            <ArrowRightCircle size={18} />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-primary">Actionable Next Steps</h3>
          </div>
          <div className="space-y-3">
            {nextStepsList.map((step, idx) => (
              <div key={idx} className="flex items-center gap-3 p-3 rounded-xl bg-black/20 border border-white/5 text-sm text-gray-200">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold">
                  ➔
                </span>
                <span>{step.replace(/^\d+[\.\)]\s*/, '')}</span>
              </div>
            ))}
            {nextStepsList.length === 0 && <p className="text-sm text-text-muted">Ready for experimentation.</p>}
          </div>
        </div>
      </div>

      {/* Footer Metadata */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-xs text-text-muted">
        <div className="flex items-center gap-2">
          <Clock size={13} />
          <span>Report generated on {formattedDate}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="inline-flex items-center gap-1.5 font-medium text-emerald-400">
            <Cpu size={13} />
            Source of Truth
          </span>
        </div>
      </div>
    </div>
  );
}
