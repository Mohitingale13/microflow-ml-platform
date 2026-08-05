/**
 * Assistant.tsx — Dedicated Natural Language ML Assistant interface for MicroFlow.
 *
 * Features:
 *   - Glassmorphism search interface with immediate Enter-to-submit support
 *   - Interactive "Suggested Questions" chips for seamless exploration
 *   - Structured four-part engineering answer display (Answer, Reasoning, Data, Recommendation)
 *   - Real-time caching indicators (⚡ Cache Hit vs 🧠 Fresh Synthesis)
 *   - Session conversational memory for follow-up questions
 *   - Recent platform queries grid with single-click reloading
 */

import { useState, useEffect, type KeyboardEvent } from 'react';
import {
  Sparkles,
  Send,
  RefreshCw,
  Database,
  Lightbulb,
  Cpu,
  CheckCircle2,
  Clock,
  MessageSquare,
  AlertCircle,
  Trash2,
} from 'lucide-react';
import { askAssistant, getRecentQueries, getSuggestedQuestions } from '@/services/ai.service';
import type { AIQueryResponse, ConversationMessage } from '@/types/ai.types';

const DEFAULT_SUGGESTIONS = [
  "Which experiment has the best accuracy?",
  "Show failed runs.",
  "Which Random Forest run performed best?",
  "Compare all XGBoost runs.",
  "What should I improve next?",
  "Summarize active experiments and dataset sizes.",
];

export function Assistant() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Active answer and lightweight session context
  const [activeResponse, setActiveResponse] = useState<AIQueryResponse | null>(null);
  const [sessionContext, setSessionContext] = useState<ConversationMessage[]>([]);

  // Auxiliary data
  const [suggestions, setSuggestions] = useState<string[]>(DEFAULT_SUGGESTIONS);
  const [recentQueries, setRecentQueries] = useState<AIQueryResponse[]>([]);
  const [recentLoading, setRecentLoading] = useState(true);
  const [refreshFeedback, setRefreshFeedback] = useState(false);

  useEffect(() => {
    loadAuxiliaryData(false);
  }, []);

  async function loadAuxiliaryData(isManual = false) {
    setRecentLoading(true);
    const startTime = Date.now();
    try {
      const [sugRes, recRes] = await Promise.all([
        getSuggestedQuestions().catch(() => ({ data: DEFAULT_SUGGESTIONS })),
        getRecentQueries(8).catch(() => ({ data: [] as AIQueryResponse[] })),
      ]);
      if (sugRes?.data && sugRes.data.length > 0) {
        setSuggestions(sugRes.data);
      }
      if (recRes?.data) {
        setRecentQueries(recRes.data);
      }
      if (isManual) {
        const elapsed = Date.now() - startTime;
        if (elapsed < 500) await new Promise(r => setTimeout(r, 500 - elapsed));
      }
    } finally {
      setRecentLoading(false);
      if (isManual) {
        setRefreshFeedback(true);
        setTimeout(() => setRefreshFeedback(false), 2000);
      }
    }
  }

  async function handleAsk(queryText?: string) {
    const textToSend = (queryText || question).trim();
    if (!textToSend || loading) return;

    setLoading(true);
    setError(null);
    setQuestion(textToSend);

    try {
      const res = await askAssistant(textToSend, sessionContext);
      if (res.data) {
        const data = res.data;
        setActiveResponse(data);
        // Append to session memory for follow-up turns
        setSessionContext((prev) => [
          ...prev,
          { role: 'user', content: textToSend },
          { role: 'assistant', content: data.answer },
        ]);
        // Refresh recent queries table quietly
        loadAuxiliaryData();
      }
    } catch (err: any) {
      console.error("Assistant error:", err);
      setError(err?.response?.data?.detail || err?.message || "Failed to query MicroFlow Assistant. Please ensure GEMINI_API_KEY is configured.");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  }

  function handleClearSession() {
    setQuestion('');
    setActiveResponse(null);
    setSessionContext([]);
    setError(null);
  }

  function handleSelectRecent(item: AIQueryResponse) {
    setQuestion(item.question);
    setActiveResponse(item);
    setError(null);
  }

  return (
    <div className="page space-y-8 pb-16 max-w-6xl mx-auto">
      {/* ── Header Section ──────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200/60 dark:border-gray-800 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold flex items-center gap-3 tracking-tight">
            <span className="p-2.5 rounded-2xl bg-purple-600/10 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 shadow-sm border border-purple-500/20">
              <Sparkles size={26} className="animate-pulse" />
            </span>
            Ask MicroFlow
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-gradient-to-r from-purple-600/10 to-blue-600/10 dark:from-purple-500/20 dark:to-blue-500/20 text-purple-700 dark:text-purple-300 border border-purple-500/25 shadow-sm flex items-center gap-1.5">
            <Cpu size={14} />
            <span>Source of Truth</span>
          </div>
          {sessionContext.length > 0 && (
            <button
              onClick={handleClearSession}
              title="Clear active conversation session"
              className="btn btn-secondary px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 flex items-center gap-1.5 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <Trash2 size={13} />
              <span>Reset Session</span>
            </button>
          )}
        </div>
      </div>

      {/* ── Main Search Input Box ───────────────────────────────────────────── */}
      <div className="relative group">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-300"></div>
        <div className="relative bg-white dark:bg-gray-900 ring-1 ring-gray-200 dark:ring-gray-800 rounded-2xl shadow-xl p-3 sm:p-4 flex flex-col gap-3">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 sm:gap-3">
            <div className="flex items-center gap-2 flex-1 pl-1 sm:pl-2">
              <span className="text-purple-600 dark:text-purple-400 shrink-0">
                <MessageSquare size={20} />
              </span>
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Query metrics, runs, models, or datasets..."
                className="w-full bg-transparent text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none text-sm sm:text-base font-medium px-2 py-1.5"
                disabled={loading}
              />
            </div>
            <button
              onClick={() => handleAsk()}
              disabled={loading || !question.trim()}
              className={`w-full sm:w-auto px-6 py-2.5 rounded-xl font-semibold text-white shadow-md flex items-center justify-center gap-2 transition-all duration-200 shrink-0 ${
                loading || !question.trim()
                  ? 'bg-gray-400 dark:bg-gray-700 cursor-not-allowed opacity-75'
                  : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 hover:shadow-lg active:scale-[0.98]'
              }`}
            >
              {loading ? (
                <>
                  <RefreshCw size={17} className="animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Send size={17} />
                  <span>Ask AI</span>
                </>
              )}
            </button>
          </div>

          {/* Suggested Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gray-100 dark:border-gray-800/80">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mr-1 flex items-center gap-1">
              <Lightbulb size={13} className="text-amber-500" />
              Try asking:
            </span>
            {suggestions.map((sug, i) => (
              <button
                key={i}
                onClick={() => handleAsk(sug)}
                disabled={loading}
                className="text-xs font-medium px-3 py-1.5 rounded-full bg-gray-100/80 dark:bg-gray-800/80 hover:bg-purple-50 dark:hover:bg-purple-950/40 text-gray-700 dark:text-gray-300 hover:text-purple-700 dark:hover:text-purple-300 border border-gray-200/80 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-800 transition-all shadow-sm"
              >
                {sug}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Error Banner ────────────────────────────────────────────────────── */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 flex items-start gap-3 shadow-sm animate-fadeIn">
          <AlertCircle size={20} className="shrink-0 mt-0.5 text-red-500" />
          <div>
            <h4 className="font-semibold text-sm">Assistant Query Failed</h4>
            <p className="text-xs mt-1 leading-relaxed opacity-90">{error}</p>
          </div>
        </div>
      )}

      {/* ── Active Response Viewer ───────────────────────────────────────────── */}
      {activeResponse ? (
        <div className="space-y-6 animate-fadeIn">
          {/* Query Header bar */}
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-inner">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 text-purple-600 dark:text-purple-400 font-bold">
                Q
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  "{activeResponse.question}"
                </h2>
              </div>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500 font-medium shrink-0">
              <Clock size={13} />
              <span>
                {new Date(activeResponse.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>

          {/* 4-Column Structured Engineering Sections */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* 1. Primary Answer */}
            <div className="md:col-span-2 bg-white dark:bg-gray-900 border border-purple-200 dark:border-purple-900/60 rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-2.5 pb-3.5 mb-3.5 border-b border-gray-100 dark:border-gray-800">
                <span className="p-2 rounded-xl bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400 font-bold">
                  <CheckCircle2 size={20} />
                </span>
                <h3 className="font-bold text-base tracking-wide text-gray-900 dark:text-gray-100">
                  Analysis & Findings
                </h3>
              </div>
              <p className="text-gray-800 dark:text-gray-200 text-base leading-relaxed whitespace-pre-wrap font-normal">
                {activeResponse.answer}
              </p>
            </div>

            {/* 2. Analytical Reasoning */}
            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-2.5 pb-3 mb-3 border-b border-gray-100 dark:border-gray-800">
                <span className="p-2 rounded-xl bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400">
                  <Cpu size={18} />
                </span>
                <h3 className="font-bold text-sm uppercase tracking-wider text-gray-700 dark:text-gray-300">
                  Reasoning
                </h3>
              </div>
              <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                {activeResponse.reasoning}
              </p>
            </div>

            {/* 3. Supporting Data (Source of Truth) */}
            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-2.5 pb-3 mb-3 border-b border-gray-100 dark:border-gray-800">
                <span className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
                  <Database size={18} />
                </span>
                <h3 className="font-bold text-sm uppercase tracking-wider text-gray-700 dark:text-gray-300">
                  Telemetry Evidence
                </h3>
              </div>
              <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed font-mono text-xs whitespace-pre-wrap bg-gray-50 dark:bg-gray-800/50 p-3 rounded-xl border border-gray-100 dark:border-gray-800">
                {activeResponse.supporting_data}
              </p>
            </div>

            {/* 4. Recommendation */}
            <div className="md:col-span-2 bg-gradient-to-r from-amber-50/50 to-orange-50/50 dark:from-amber-950/20 dark:to-orange-950/20 border border-amber-200 dark:border-amber-900/60 rounded-2xl p-5 shadow-sm">
              <div className="flex items-center gap-2.5 pb-3 mb-3 border-b border-amber-200/60 dark:border-amber-900/40">
                <span className="p-2 rounded-xl bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 font-bold">
                  <Lightbulb size={18} />
                </span>
                <h3 className="font-bold text-sm uppercase tracking-wider text-amber-900 dark:text-amber-300">
                  Suggested Next Step
                </h3>
              </div>
              <p className="text-gray-800 dark:text-gray-200 text-sm leading-relaxed whitespace-pre-wrap font-medium">
                {activeResponse.recommendation || "No further action required."}
              </p>
            </div>
          </div>
        </div>
      ) : (
        /* Empty Welcome Hero when no query asked yet */
        <div className="py-12 px-6 rounded-3xl bg-gradient-to-br from-gray-50 via-purple-50/20 to-blue-50/20 dark:from-gray-900/80 dark:via-purple-950/20 dark:to-gray-900 border border-gray-200/70 dark:border-gray-800 text-center shadow-inner max-w-4xl mx-auto">
          <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-purple-600 to-blue-600 text-white flex items-center justify-center mx-auto mb-5 shadow-lg shadow-purple-500/20">
            <Sparkles size={32} />
          </div>
          <h2 className="text-2xl font-extrabold text-gray-900 dark:text-gray-100 tracking-tight">
            Query your experiment telemetry.
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 max-w-xl mx-auto mt-2.5 leading-relaxed font-medium">
            Analyze evaluation metrics, compare model performance deltas, or troubleshoot training failures across your workspace.
          </p>
        </div>
      )}

      {/* ── Recent Questions Section ────────────────────────────────────────── */}
      <div className="pt-8 border-t border-gray-200/60 dark:border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
            <Clock size={18} className="text-gray-500" />
            <span>Recent Platform Questions</span>
          </h3>
          <button
            onClick={() => loadAuxiliaryData(true)}
            disabled={recentLoading}
            className="text-xs font-bold px-3.5 py-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-purple-300 flex items-center gap-1.5 transition-all shadow-sm cursor-pointer disabled:opacity-50"
          >
            {refreshFeedback ? (
              <>
                <CheckCircle2 size={13} className="text-emerald-400" />
                <span className="text-emerald-300 font-bold">Updated!</span>
              </>
            ) : (
              <>
                <RefreshCw size={13} className={recentLoading ? "animate-spin text-purple-200" : ""} />
                <span>{recentLoading ? "Refreshing..." : "Refresh list"}</span>
              </>
            )}
          </button>
        </div>

        {recentLoading && recentQueries.length === 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="h-20 bg-gray-100 dark:bg-gray-800 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : recentQueries.length === 0 ? (
          <div className="text-center py-8 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
            No recent questions recorded yet. Ask a question above to begin!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {recentQueries.map((item) => (
              <div
                key={item.id}
                onClick={() => handleSelectRecent(item)}
                className="p-4 rounded-xl bg-white dark:bg-gray-900 border border-gray-200/80 dark:border-gray-800 hover:border-purple-300 dark:hover:border-purple-700 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group"
              >
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-sm font-bold text-gray-800 dark:text-gray-200 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors line-clamp-1">
                    "{item.question}"
                  </h4>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mt-2 font-normal leading-relaxed">
                  {item.answer}
                </p>
                <div className="flex items-center justify-end gap-2 mt-3 pt-2 border-t border-gray-100 dark:border-gray-800/60 text-[11px] text-purple-600 dark:text-purple-400 font-medium">
                  <span>Click to view analysis →</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
