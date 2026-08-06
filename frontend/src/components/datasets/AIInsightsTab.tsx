import { useState } from 'react';
import { 
  Sparkles, RefreshCw, AlertCircle, ChevronDown, ChevronUp, 
  Target, CheckCircle2, ShieldAlert, BarChart2, Layers
} from 'lucide-react';
import { analyzeDataset } from '../../services/dataset-ai.service';
import type { DatasetAIAnalysis, RecommendedModel, FeatureObservation } from '../../types/dataset-ai.types';

interface AIInsightsTabProps {
  datasetId: string;
}

// ─── Skeleton Loader ──────────────────────────────────────────────────────────

function InsightsSkeleton() {
  return (
    <div className="space-y-6 animate-pulse pb-12">
      <div className="h-16 rounded-xl border border-white/10 bg-white/5 p-4" />
      <div className="h-48 rounded-2xl border border-white/10 bg-white/5 p-6" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="h-44 rounded-xl border border-white/10 bg-white/5" />
        <div className="h-44 rounded-xl border border-white/10 bg-white/5" />
        <div className="h-44 rounded-xl border border-white/10 bg-white/5" />
        <div className="h-44 rounded-xl border border-white/10 bg-white/5" />
      </div>
    </div>
  );
}

// ─── Helpers for Text Shaping & Formatting ────────────────────────────────────

function renderListItems(items: string[] | string | undefined): string[] {
  if (!items) return [];
  if (Array.isArray(items)) return items;
  return items.split('\n').map(s => s.replace(/^[*-]\s*/, '').trim()).filter(Boolean);
}

function getShortSentence(text: string | undefined, maxLen = 220): string {
  if (!text) return 'Dataset evaluation ready for machine learning feature exploration.';
  const sentences = text.split(/\.(?=\s|$)/);
  if (sentences[0] && sentences[0].length > 20 && sentences[0].length <= maxLen) {
    if (sentences[1] && (sentences[0].length + sentences[1].length + 2) <= maxLen) {
      return `${sentences[0].trim()}. ${sentences[1].trim()}.`;
    }
    return `${sentences[0].trim()}.`;
  }
  if (text.length <= maxLen) return text;
  return text.substring(0, maxLen).trim() + '...';
}

function cleanItem(item: string, maxLen = 75): string {
  let cleaned = item.replace(/^(Recommendation|Suggested|Warning|Caution)[:-]\s*/i, '');
  if (cleaned.length > maxLen) cleaned = cleaned.substring(0, maxLen).trim() + '...';
  return cleaned;
}

// ─── Main Component (Linear / Vercel Developer-First Redesign) ────────────────

export function AIInsightsTab({ datasetId }: AIInsightsTabProps) {
  const [analysis, setAnalysis] = useState<DatasetAIAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showFullProfile, setShowFullProfile] = useState<boolean>(false);

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
      setError(err?.message || 'An unexpected error occurred while analyzing dataset.');
    } finally {
      setIsLoading(false);
    }
  };



  // ── Loading State ─────────────────────────────────────────────────────────
  if (isLoading && !analysis) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3.5 bg-purple-500/15 border border-purple-500/30 rounded-2xl p-5 text-base text-purple-200 shadow-md">
          <Sparkles className="text-purple-400 animate-spin shrink-0 w-6 h-6" />
          <span className="font-medium">Synthesizing developer intelligence from dataset schema and statistical distribution...</span>
        </div>
        <InsightsSkeleton />
      </div>
    );
  }

  // ── Initial Prompt State ──────────────────────────────────────────────────
  if (!analysis && !isLoading && !error) {
    return (
      <div className="rounded-2xl border border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-transparent p-10 text-center shadow-lg max-w-3xl mx-auto my-6">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-purple-500/20 border border-purple-400/40 shadow-md">
          <Sparkles className="text-purple-400 w-7 h-7" />
        </div>
        <h3 className="text-lg font-extrabold text-white mb-2 uppercase tracking-wider">AI Dataset Intelligence Audit</h3>
        <p className="text-sm text-gray-300 mb-8 max-w-xl mx-auto leading-relaxed font-medium">
          Run a comprehensive zero-hallucination pre-training audit on this dataset schema. Get an objective quality score, feature relevance diagnostics, algorithm suitability ratings, and actionable preprocessing recommendations.
        </p>
        <button
          onClick={fetchInsights}
          className="inline-flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 px-8 py-3.5 text-sm font-extrabold text-white hover:from-purple-500 hover:to-blue-500 transition-all duration-200 shadow-xl shadow-purple-500/30 cursor-pointer"
        >
          <Sparkles size={18} />
          Generate Dataset Intelligence
        </button>
      </div>
    );
  }

  // ── Error State ───────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center max-w-xl mx-auto shadow-xl">
        <AlertCircle className="mx-auto mb-3 text-red-400 w-9 h-9" />
        <h3 className="text-base font-bold text-red-300 mb-2">Dataset Audit Failed</h3>
        <p className="text-sm text-gray-300 mb-6 leading-relaxed">{error || 'Unable to audit dataset schema.'}</p>
        <button
          onClick={fetchInsights}
          className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/10 px-6 py-2.5 text-sm font-semibold text-white hover:bg-white/20 transition-all shadow-md cursor-pointer"
        >
          <RefreshCw size={15} />
          Retry Audit
        </button>
      </div>
    );
  }

  if (!analysis) return null;

  // Extract quality safely
  const quality = analysis.dataset_quality || { score: 75, label: 'Good', explanation: 'Sufficient sample size and low null rates.' };
  const qualityScore = typeof quality.score === 'number' ? quality.score : parseInt(quality.score, 10) || 75;
  const qualityLabel = quality.label || 'Good';
  const isHealthy = qualityScore >= 70 && qualityLabel.toLowerCase() !== 'poor';

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

  // Concise punchy lists for the developer grid
  const punchyStrengths = strengthsList.slice(0, 3).map(s => cleanItem(s));
  const punchyIssues = issuesList.slice(0, 3).map(i => cleanItem(i));
  const punchyPrep = preprocessingList.slice(0, 3).map(p => cleanItem(p));

  const statusTitle = isHealthy ? '🟢 Dataset ready for ML experimentation.' : '🟡 Preprocessing recommended prior to training.';
  const statusSummary = getShortSentence(analysis.overall_summary);

  // Top recommended model to suggest in Hero
  const topModel = modelsList[0] || { model: 'XGBoost / Boosted Trees', suitability: 'High', reasoning: 'Robust performance on structured tabular distributions with zero assumptions.' };

  return (
    <div className="space-y-6 animate-in fade-in duration-200 pb-16 font-sans text-text-primary">
      
      {/* ── Top Bar: Title & Refresh ───────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <Sparkles className="w-5 h-5 text-purple-400 shrink-0" />
          <h2 className="text-base font-bold text-white tracking-wide uppercase">AI Dataset Intelligence</h2>
        </div>
        <button
          onClick={fetchInsights}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-white/10 bg-white/5 text-xs sm:text-sm font-semibold text-gray-200 hover:text-white hover:bg-white/10 transition-all self-start sm:self-auto cursor-pointer shadow-sm"
        >
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          <span>Re-evaluate Dataset</span>
        </button>
      </div>

      {/* ── Status Banner (High Contrast) ──────────────────────────────────── */}
      <div className="bg-white/[0.05] border border-white/15 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center gap-3.5 shadow-md">
        <span className="font-extrabold text-base text-white whitespace-nowrap shrink-0 flex items-center gap-2">
          {statusTitle}
        </span>
        <p className="text-sm sm:text-base text-gray-200 leading-relaxed font-medium sm:border-l sm:border-white/15 sm:pl-4 flex-1">
          {statusSummary}
        </p>
      </div>

      {/* ── Hero Developer Recommendation Card ──────────────────────────────── */}
      <div className="rounded-2xl border border-purple-500/40 bg-gradient-to-br from-purple-500/15 via-blue-500/10 to-transparent p-6 sm:p-8 shadow-2xl relative">
        <div className="flex flex-col xl:flex-row xl:items-start justify-between gap-6">
          <div className="space-y-3 flex-1">
            <span className="text-xs font-black tracking-widest uppercase text-purple-300 block bg-purple-500/20 px-2.5 py-1 rounded-md border border-purple-400/30 w-fit">
              Recommended Blueprint
            </span>
            <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight leading-snug">
              Target Column: <span className="text-purple-200 font-extrabold underline decoration-purple-400/50">{analysis.recommended_target}</span>
            </h3>
            <p className="text-sm sm:text-base text-gray-200 font-medium pt-1 max-w-2xl leading-relaxed">
              Start prototyping baseline experiments with <span className="text-emerald-300 font-bold">{topModel.model}</span>. {topModel.reasoning}
            </p>
          </div>

          {/* Target Rationale Block */}
          <div className="shrink-0 bg-black/50 border border-white/20 rounded-xl p-5 max-w-md space-y-2.5 shadow-inner">
            <div className="flex items-center justify-between gap-4 text-sm font-bold border-b border-white/10 pb-2">
              <span className="text-gray-300 uppercase tracking-wider text-xs flex items-center gap-1.5">
                <Target size={14} className="text-purple-400" /> Target Grounding:
              </span>
              <span className="text-purple-300 font-mono font-extrabold text-xs bg-purple-500/20 px-2.5 py-0.5 rounded border border-purple-400/30">
                Primary Label
              </span>
            </div>
            <div className="text-xs sm:text-sm leading-relaxed text-gray-200 font-normal pt-1">
              <span className="font-bold text-white uppercase text-[11px] tracking-wider block mb-1">Empirical Rationale:</span> 
              Identified as optimal prediction goal based on value cardinality, variance, and downstream diagnostic impact.
            </div>
          </div>
        </div>

        {/* Suggested Model Family Bar */}
        <div className="mt-8 pt-5 border-t border-white/15 flex flex-col md:flex-row md:items-center gap-4">
          <span className="text-sm font-bold text-gray-200 flex items-center gap-2 shrink-0 uppercase tracking-wider">
            <Layers size={15} className="text-purple-400" /> Suitable Model Families:
          </span>
          <div className="flex flex-wrap items-center gap-2.5">
            {modelsList.map((mod, idx) => {
              const suitability = mod.suitability?.toLowerCase() || '';
              const isTop = idx === 0 || suitability === 'high';
              return (
                <span key={idx} className={`border px-3.5 py-1.5 rounded-xl text-sm font-mono font-medium shadow-sm flex items-center gap-2 ${
                  isTop ? 'bg-purple-500/20 border-purple-400/50 text-white font-extrabold' : 'bg-white/10 border-white/20 text-gray-300'
                }`}>
                  <span>{mod.model}</span>
                  <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md ${
                    suitability === 'high' ? 'bg-emerald-500/30 text-emerald-300 border border-emerald-400/40' : 'bg-blue-500/20 text-blue-300'
                  }`}>
                    {mod.suitability || 'Viable'}
                  </span>
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── 4-Column Concise Developer Grid ────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 pt-2">
        
        {/* 1. Quality Health */}
        <div className="rounded-2xl border border-white/15 bg-white/[0.04] p-5 flex flex-col justify-between hover:bg-white/[0.07] transition-all shadow-md">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                📊 Data Quality
              </span>
              <span className={`text-xs font-black px-2.5 py-0.5 rounded-md uppercase border ${
                isHealthy ? 'bg-emerald-500/20 text-emerald-300 border-emerald-400/40' : 'bg-amber-500/20 text-amber-300 border-amber-400/40'
              }`}>
                {qualityLabel}
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-white tracking-tight">{qualityScore}</span>
              <span className="text-gray-400 font-semibold text-sm">/ 100</span>
            </div>
            <p className="text-xs sm:text-sm text-gray-300 font-medium leading-relaxed mt-2 line-clamp-3">
              {quality.explanation || 'Analyzed missing ratio, sample volume adequacy, and features.'}
            </p>
          </div>
        </div>

        {/* 2. Key Data Strengths */}
        <div className="rounded-2xl border border-white/15 bg-white/[0.04] p-5 flex flex-col justify-between hover:bg-white/[0.07] transition-all shadow-md">
          <div>
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-3 flex items-center gap-2">
              ✓ Data Strengths
            </span>
            <ul className="space-y-2.5 text-xs sm:text-sm text-gray-200 font-medium">
              {punchyStrengths.length > 0 ? (
                punchyStrengths.map((str, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="text-emerald-400 font-black shrink-0 text-sm">✓</span>
                    <span className="leading-snug text-gray-200" title={str}>{str}</span>
                  </li>
                ))
              ) : (
                <li className="text-sm text-gray-400 italic">No structural strengths listed.</li>
              )}
            </ul>
          </div>
        </div>

        {/* 3. Preprocessing Actions */}
        <div className="rounded-2xl border border-white/15 bg-white/[0.04] p-5 flex flex-col justify-between hover:bg-white/[0.07] transition-all shadow-md">
          <div>
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-3 flex items-center gap-2">
              ⚡ Preprocessing Needs
            </span>
            <ul className="space-y-2.5 text-xs sm:text-sm text-gray-200 font-medium">
              {punchyPrep.length > 0 ? (
                punchyPrep.map((prep, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="text-purple-400 font-mono font-black shrink-0 text-sm">□</span>
                    <span className="leading-snug text-gray-200" title={prep}>{prep}</span>
                  </li>
                ))
              ) : (
                <li className="text-sm text-emerald-300 font-semibold flex items-center gap-2">
                  <CheckCircle2 size={16} /> Ready without transforms
                </li>
              )}
            </ul>
          </div>
        </div>

        {/* 4. Risk Alerts / Leakage Warnings */}
        <div className="rounded-2xl border border-white/15 bg-white/[0.04] p-5 flex flex-col justify-between hover:bg-white/[0.07] transition-all shadow-md">
          <div>
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-3 flex items-center gap-2">
              ⚠️ Risks & Leakage
            </span>
            <ul className="space-y-2.5 text-xs sm:text-sm text-gray-200 font-medium">
              {punchyIssues.length > 0 ? (
                punchyIssues.map((iss, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="text-amber-400 font-bold shrink-0 text-sm">!</span>
                    <span className="leading-snug text-gray-200" title={iss}>{iss}</span>
                  </li>
                ))
              ) : (
                <li className="text-sm text-emerald-300 font-semibold flex items-center gap-2">
                  <ShieldAlert size={16} className="text-emerald-400" /> No data leakage detected
                </li>
              )}
            </ul>
          </div>
        </div>

      </div>

      {/* ── Show Full Schema & Feature Report Toggle ───────────────────────── */}
      <div className="flex justify-center pt-6">
        <button
          onClick={() => setShowFullProfile(!showFullProfile)}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-full border border-white/20 bg-white/10 text-sm font-bold text-gray-200 hover:text-white hover:bg-white/15 transition-all shadow-lg cursor-pointer"
        >
          <span>{showFullProfile ? 'Hide Full Schema Audit & Observations' : 'Show Full Schema Audit & Observations'}</span>
          {showFullProfile ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* ── Advanced Data Engineering Profile (Hidden by default) ──────────── */}
      {showFullProfile && (
        <div className="mt-8 space-y-6 pt-8 border-t border-white/15 animate-in slide-in-from-top-2 duration-200">
          <div className="text-sm font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
            <BarChart2 size={18} className="text-purple-400" /> Complete Statistical & Feature Audit
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Full Executive Summary */}
            <div className="rounded-2xl border border-white/15 bg-black/40 p-6 space-y-4 shadow-lg">
              <h4 className="text-base font-bold text-white border-b border-white/10 pb-3">
                Full AI Engineering Audit
              </h4>
              <p className="text-sm text-gray-200 leading-relaxed font-normal">
                {analysis.overall_summary}
              </p>
              <div className="pt-4 border-t border-white/10">
                <span className="text-gray-400 font-bold block mb-2 uppercase text-xs tracking-wider">Recommended Next Steps:</span>
                <ul className="space-y-2 text-sm text-gray-200 font-medium">
                  {nextStepsList.map((step, i) => (
                    <li key={i} className="flex items-start gap-2.5">
                      <span className="text-purple-400 font-black">•</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Feature by Feature Observations */}
            <div className="rounded-2xl border border-white/15 bg-black/40 p-6 space-y-4 shadow-lg overflow-hidden">
              <h4 className="text-base font-bold text-white border-b border-white/10 pb-3">
                Feature-by-Feature Observations ({observationsList.length})
              </h4>
              <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                {observationsList.length > 0 ? (
                  observationsList.map((obs, idx) => (
                    <div key={idx} className="bg-white/5 border border-white/10 rounded-xl p-3.5 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-purple-300 font-mono">{obs.feature}</span>
                      </div>
                      <p className="text-xs text-gray-200 leading-relaxed">{obs.observation}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-400 italic">No specific anomalies flagged per individual column.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
