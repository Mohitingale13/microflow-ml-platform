import { useState } from 'react';
import { Sparkles, Brain, TrendingUp, AlertTriangle, GitCompare, Lightbulb, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import { useGenerateAIReview } from '../../hooks/useAIReview';
import type { AIReviewResponse } from '../../types/ai.types';

interface AIReviewCardProps {
  runId: string;
  runStatus: string;
}

// ─── Skeleton loader ──────────────────────────────────────────────────────────

function ReviewSkeleton() {
  return (
    <div className="space-y-4 animate-pulse p-4">
      <div className="h-24 rounded-xl border border-white/10 bg-white/5 p-5" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="h-32 rounded-xl border border-white/10 bg-white/5" />
        <div className="h-32 rounded-xl border border-white/10 bg-white/5" />
        <div className="h-32 rounded-xl border border-white/10 bg-white/5" />
      </div>
    </div>
  );
}

function cleanSentence(text: string | undefined, maxLen = 140): string {
  if (!text) return 'None detected.';
  let cleaned = text.replace(/^(Overall|Strength|Weakness|Recommendation|Comparison)[:-]\s*/i, '');
  const match = cleaned.match(/^.*?\.(?=\s|$)/);
  if (match && match[0].length > 20 && match[0].length <= maxLen) return match[0].trim();
  if (cleaned.length <= maxLen) return cleaned;
  return cleaned.substring(0, maxLen).trim() + '...';
}

// ─── Main component (Linear / Vercel Developer-First Redesign) ───────────────

export function AIReviewCard({ runId, runStatus }: AIReviewCardProps) {
  const [review, setReview] = useState<AIReviewResponse | null>(null);
  const [showFullReview, setShowFullReview] = useState<boolean>(false);
  const mutation = useGenerateAIReview(runId);

  const isCompleted = runStatus === 'completed';

  const handleGenerate = async () => {
    try {
      const result = await mutation.mutateAsync();
      if (result.success && result.data) {
        setReview(result.data);
      }
    } catch {
      // Error handled via mutation.isError
    }
  };

  const handleRetry = () => {
    mutation.reset();
    setReview(null);
  };

  if (!isCompleted) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-center shadow-sm">
        <Sparkles className="mx-auto mb-3 text-gray-500 w-7 h-7" />
        <p className="text-sm font-medium text-gray-400">
          AI Run Diagnostics & Engineering Reviews are available once the run finishes executing.
        </p>
      </div>
    );
  }

  // Initial prompt button
  if (!review && !mutation.isPending && !mutation.isError) {
    return (
      <div className="rounded-2xl border border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-transparent p-7 text-center shadow-lg">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-500/20 border border-purple-400/40 shadow-md">
          <Sparkles className="text-purple-400 w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-white mb-1.5 uppercase tracking-wider">AI Run Diagnostics</h3>
        <p className="text-sm text-gray-300 mb-6 max-w-md mx-auto leading-relaxed font-medium">
          Generate an instant ML engineer diagnostic: spot bottleneck oscillations, compare against the current best baseline, and get actionable parameter tweaks.
        </p>
        <button
          id="generate-ai-review-btn"
          onClick={handleGenerate}
          className="inline-flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 px-7 py-3 text-sm font-extrabold text-white hover:from-purple-500 hover:to-blue-500 transition-all duration-200 shadow-xl shadow-purple-500/30 cursor-pointer"
        >
          <Sparkles size={16} />
          Evaluate Run Intelligence
        </button>
      </div>
    );
  }

  if (mutation.isPending) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3 bg-purple-500/15 border border-purple-500/30 rounded-2xl p-4 text-sm text-purple-200 font-bold">
          <Brain className="text-purple-400 animate-spin shrink-0 w-5 h-5" />
          <span>MicroFlow AI is analyzing convergence curves, hyperparameter interactions, and run latency...</span>
        </div>
        <ReviewSkeleton />
      </div>
    );
  }

  if (mutation.isError || (!review && !mutation.isPending)) {
    const errorMessage = mutation.error instanceof Error
      ? mutation.error.message
      : 'An unexpected error occurred while diagnosing run.';

    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-center shadow-lg">
        <AlertTriangle className="mx-auto mb-3 text-red-400 w-8 h-8" />
        <p className="text-base font-bold text-red-300 mb-1">Diagnostic Evaluation Failed</p>
        <p className="text-sm text-gray-300 mb-5 max-w-sm mx-auto">{errorMessage}</p>
        <button
          id="retry-ai-review-btn"
          onClick={handleRetry}
          className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/10 px-6 py-2.5 text-sm font-bold text-white hover:bg-white/20 transition-all cursor-pointer"
        >
          <RefreshCw size={14} />
          Retry Diagnostic
        </button>
      </div>
    );
  }

  if (!review) return null;

  const punchyStrength = cleanSentence(review.strengths, 120);
  const punchyWeakness = cleanSentence(review.weaknesses, 120);
  const punchyComparison = cleanSentence(review.comparison, 120);

  return (
    <div className="space-y-5 rounded-2xl border border-purple-500/40 bg-gradient-to-br from-purple-500/15 via-black/40 to-transparent p-6 shadow-2xl">
      
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <Sparkles className="text-purple-400 w-5 h-5" />
          <span className="text-base font-bold text-white uppercase tracking-wide">AI Engineering Diagnostics</span>
        </div>
        <button
          id="regenerate-ai-review-btn"
          onClick={handleRetry}
          title="Re-evaluate run metrics"
          className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-bold text-gray-300 hover:text-white hover:bg-white/10 transition-all cursor-pointer shadow-sm"
        >
          <RefreshCw size={13} />
          Re-evaluate
        </button>
      </div>

      {/* Hero Action Recommendation Box */}
      <div className="bg-black/50 border border-purple-500/40 rounded-xl p-5 shadow-inner flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1.5 flex-1">
          <span className="text-[11px] font-black tracking-widest uppercase text-purple-300 bg-purple-500/20 px-2.5 py-0.5 rounded border border-purple-400/30 inline-block">
            Recommended Action
          </span>
          <div className="text-base sm:text-lg font-bold text-white leading-snug">
            {review.recommendation}
          </div>
        </div>
        <div className="shrink-0 bg-white/[0.04] border border-white/10 rounded-lg p-3.5 max-w-xs text-xs text-gray-300 font-medium">
          <span className="font-extrabold text-white block mb-1 uppercase text-[10px] tracking-wider flex items-center gap-1">
            <Lightbulb size={13} className="text-amber-400" /> Assessment Focus:
          </span>
          {cleanSentence(review.overall_assessment, 130)}
        </div>
      </div>

      {/* 3-Column Concise Scannable Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
        
        {/* Strength */}
        <div className="rounded-xl border border-white/15 bg-white/[0.04] p-4 flex flex-col justify-between shadow-md hover:bg-white/[0.07] transition-all">
          <div className="space-y-1.5">
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <TrendingUp size={15} className="text-emerald-400" /> Observed Gains
            </span>
            <p className="text-xs sm:text-sm font-medium text-gray-200 leading-relaxed">
              {punchyStrength}
            </p>
          </div>
        </div>

        {/* Weakness */}
        <div className="rounded-xl border border-white/15 bg-white/[0.04] p-4 flex flex-col justify-between shadow-md hover:bg-white/[0.07] transition-all">
          <div className="space-y-1.5">
            <span className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle size={15} className="text-amber-400" /> Bottlenecks & Risks
            </span>
            <p className="text-xs sm:text-sm font-medium text-gray-200 leading-relaxed">
              {punchyWeakness}
            </p>
          </div>
        </div>

        {/* Comparison */}
        <div className="rounded-xl border border-white/15 bg-white/[0.04] p-4 flex flex-col justify-between shadow-md hover:bg-white/[0.07] transition-all">
          <div className="space-y-1.5">
            <span className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
              <GitCompare size={15} className="text-blue-400" /> Vs. Baseline Benchmark
            </span>
            <p className="text-xs sm:text-sm font-medium text-gray-200 leading-relaxed">
              {punchyComparison}
            </p>
          </div>
        </div>

      </div>

      {/* Toggle Complete Review Drawer */}
      <div className="flex justify-center pt-3">
        <button
          onClick={() => setShowFullReview(!showFullReview)}
          className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-white/20 bg-white/10 text-xs sm:text-sm font-bold text-gray-200 hover:text-white hover:bg-white/15 transition-all shadow-md cursor-pointer"
        >
          <span>{showFullReview ? 'Hide Complete Diagnostic Log' : 'Show Complete Diagnostic Log'}</span>
          {showFullReview ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
        </button>
      </div>

      {showFullReview && (
        <div className="pt-5 border-t border-white/15 space-y-4 animate-in slide-in-from-top-2 duration-200 text-sm">
          <div className="bg-black/40 border border-white/15 rounded-xl p-5 space-y-4">
            <div>
              <span className="text-xs font-extrabold uppercase text-gray-400 tracking-wider block mb-1">Full Overall Assessment:</span>
              <p className="text-gray-200 leading-relaxed font-normal">{review.overall_assessment}</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-white/10">
              <div>
                <span className="text-xs font-extrabold uppercase text-emerald-400 tracking-wider block mb-1">All Strengths:</span>
                <p className="text-gray-200 leading-relaxed font-normal">{review.strengths}</p>
              </div>
              <div>
                <span className="text-xs font-extrabold uppercase text-amber-400 tracking-wider block mb-1">All Weaknesses:</span>
                <p className="text-gray-200 leading-relaxed font-normal">{review.weaknesses}</p>
              </div>
            </div>
            <div className="pt-3 border-t border-white/10">
              <span className="text-xs font-extrabold uppercase text-blue-400 tracking-wider block mb-1">Detailed Champion Comparison:</span>
              <p className="text-gray-200 leading-relaxed font-normal">{review.comparison}</p>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
