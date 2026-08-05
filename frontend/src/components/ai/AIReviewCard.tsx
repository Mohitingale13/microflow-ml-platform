import { useState } from 'react';
import { Sparkles, Brain, TrendingUp, AlertTriangle, GitCompare, Lightbulb, RefreshCw, Clock, Cpu } from 'lucide-react';
import { useGenerateAIReview } from '../../hooks/useAIReview';
import type { AIReviewResponse } from '../../types/ai.types';

interface AIReviewCardProps {
  runId: string;
  runStatus: string;
}

// ─── Skeleton loader ──────────────────────────────────────────────────────────

function ReviewSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="rounded-xl border border-white/10 bg-white/5 p-5">
          <div className="h-3 w-32 rounded bg-white/10 mb-3" />
          <div className="space-y-2">
            <div className="h-3 w-full rounded bg-white/10" />
            <div className="h-3 w-5/6 rounded bg-white/10" />
            <div className="h-3 w-4/6 rounded bg-white/10" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Individual review section ─────────────────────────────────────────────

interface SectionProps {
  icon: React.ReactNode;
  title: string;
  content: string;
  accent?: string;
}

function ReviewSection({ icon, title, content, accent = 'text-blue-400' }: SectionProps) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-5 transition-all hover:bg-white/[0.07]">
      <div className={`flex items-center gap-2 mb-3 ${accent}`}>
        <span className="shrink-0">{icon}</span>
        <p className="text-[10px] uppercase tracking-[0.2em] font-semibold">{title}</p>
      </div>
      <p className="text-sm text-gray-300 leading-relaxed">{content}</p>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function AIReviewCard({ runId, runStatus }: AIReviewCardProps) {
  const [review, setReview] = useState<AIReviewResponse | null>(null);
  const mutation = useGenerateAIReview(runId);

  const isCompleted = runStatus === 'completed';

  const handleGenerate = async () => {
    try {
      const result = await mutation.mutateAsync();
      if (result.success && result.data) {
        setReview(result.data);
      }
    } catch {
      // Error is handled via mutation.isError
    }
  };

  const handleRetry = () => {
    mutation.reset();
    setReview(null);
  };

  // ── Not available for non-completed runs ─────────────────────────────────
  if (!isCompleted) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-center">
        <Sparkles className="mx-auto mb-3 text-gray-600" size={28} />
        <p className="text-sm text-gray-500">
          AI Run Review is only available for completed runs.
        </p>
      </div>
    );
  }

  // ── Generate button (initial state) ─────────────────────────────────────
  if (!review && !mutation.isPending && !mutation.isError) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-8 text-center">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30">
          <Sparkles className="text-purple-400" size={24} />
        </div>
        <h3 className="text-base font-semibold text-white mb-2">AI Run Review</h3>
        <p className="text-sm text-gray-400 mb-6 max-w-sm mx-auto leading-relaxed">
          Generate a professional ML engineer review of this run — including strengths, weaknesses, comparison to the best run, and a recommended next experiment.
        </p>
        <button
          id="generate-ai-review-btn"
          onClick={handleGenerate}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:from-purple-500 hover:to-blue-500 transition-all duration-200 shadow-lg shadow-purple-500/20"
        >
          <Sparkles size={15} />
          Generate AI Review
        </button>
      </div>
    );
  }

  // ── Skeleton loading ─────────────────────────────────────────────────────
  if (mutation.isPending) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="text-purple-400 animate-pulse" size={18} />
          <p className="text-sm text-gray-400">AI is reviewing this run…</p>
        </div>
        <ReviewSkeleton />
      </div>
    );
  }

  // ── Error state ──────────────────────────────────────────────────────────
  if (mutation.isError || (!review && !mutation.isPending)) {
    const errorMessage = mutation.error instanceof Error
      ? mutation.error.message
      : 'An unexpected error occurred while generating the review.';

    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6 text-center">
        <AlertTriangle className="mx-auto mb-3 text-red-400" size={28} />
        <p className="text-sm font-medium text-red-400 mb-1">Review Generation Failed</p>
        <p className="text-xs text-gray-500 mb-5 max-w-sm mx-auto">{errorMessage}</p>
        <button
          id="retry-ai-review-btn"
          onClick={handleRetry}
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-5 py-2 text-sm font-medium text-white hover:bg-white/10 transition-all"
        >
          <RefreshCw size={13} />
          Retry
        </button>
      </div>
    );
  }

  // ── Full review card ─────────────────────────────────────────────────────
  if (!review) return null;

  const formattedDate = new Date(review.generated_at).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Sparkles className="text-purple-400" size={16} />
          <span className="text-sm font-semibold text-white">AI Run Review</span>
        </div>
        <button
          id="regenerate-ai-review-btn"
          onClick={handleRetry}
          title="Generate a new review"
          className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-gray-400 hover:text-white hover:bg-white/10 transition-all"
        >
          <RefreshCw size={11} />
          Regenerate
        </button>
      </div>

      {/* Review sections */}
      <ReviewSection
        icon={<Brain size={14} />}
        title="Overall Assessment"
        content={review.overall_assessment}
        accent="text-purple-400"
      />
      <ReviewSection
        icon={<TrendingUp size={14} />}
        title="Strengths"
        content={review.strengths}
        accent="text-green-400"
      />
      <ReviewSection
        icon={<AlertTriangle size={14} />}
        title="Weaknesses"
        content={review.weaknesses}
        accent="text-yellow-400"
      />
      <ReviewSection
        icon={<GitCompare size={14} />}
        title="Comparison"
        content={review.comparison}
        accent="text-blue-400"
      />
      <ReviewSection
        icon={<Lightbulb size={14} />}
        title="Recommendation"
        content={review.recommendation}
        accent="text-orange-400"
      />

      {/* Footer metadata */}
      <div className="mt-2 flex flex-wrap items-center gap-4 rounded-xl border border-white/10 bg-white/5 px-4 py-3">
        <div className="flex items-center gap-1.5 text-[10px] text-gray-500">
          <Clock size={11} />
          <span>{formattedDate}</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-gray-500">
          <Cpu size={11} />
          <span>Source of Truth</span>
        </div>
      </div>
    </div>
  );
}
