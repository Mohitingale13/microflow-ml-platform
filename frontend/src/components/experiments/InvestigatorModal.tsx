import { useState, useEffect } from 'react';
import {
  X,
    CheckCircle2,
  ArrowRight,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  BrainCircuit,
  Loader2
} from 'lucide-react';
import type { InvestigateResponseData } from '@/types/investigator.types';
import { postInvestigate } from '@/services/investigator.service';

interface InvestigatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  experimentId: string;
}

const EXAMPLE_PROMPTS = [
  "Why did the weakest run perform worse?",
  "Which features influenced the model most?",
  "What changed between the best and worst runs?",
];

const LOADING_STEPS = [
  "Inspecting experiment runs",
  "Comparing run configurations",
  "Analyzing performance metrics",
  "Examining feature importance",
  "Synthesizing final report"
];

export function InvestigatorModal({
  isOpen,
  onClose,
  experimentId,
}: InvestigatorModalProps) {
  const [objective, setObjective] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InvestigateResponseData | null>(null);
  
  // Simulated loading state steps
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [showTrace, setShowTrace] = useState(false);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading) {
      interval = setInterval(() => {
        setCurrentStepIndex(prev => {
          if (prev < LOADING_STEPS.length - 1) return prev + 1;
          return prev;
        });
      }, 2500); // Progress to next step every 2.5 seconds
    } else {
      setCurrentStepIndex(0);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  const handleClose = () => {
    if (isLoading) return; // Prevent closing while running
    setObjective('');
    setResult(null);
    setError(null);
    setShowTrace(false);
    onClose();
  };

  const handleInvestigate = async () => {
    if (!objective.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const res = await postInvestigate(experimentId, { objective });
      setResult(res.data);
    } catch (err: any) {
      setError(err.message || 'An error occurred during investigation');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="investigator-dialog-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Panel */}
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-surface border border-border rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface-2 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent-blue/10 flex items-center justify-center">
              <BrainCircuit className="w-4 h-4 text-accent-blue" />
            </div>
            <div>
              <h2 id="investigator-dialog-title" className="text-sm font-bold text-text-primary">
                Experiment Investigator
              </h2>
              <p className="text-xs text-text-muted">
                Ask MicroFlow to investigate your experiment.
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={isLoading}
            className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-3 transition-colors disabled:opacity-50"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm flex items-start gap-2">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* INPUT STATE */}
          {!isLoading && !result && (
            <div className="space-y-6 max-w-2xl mx-auto mt-4">
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-text-primary">
                  Objective
                </label>
                <textarea
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  placeholder="e.g. Why did the best run outperform the others?"
                  className="w-full h-32 px-4 py-3 bg-surface-2 border border-border rounded-xl text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue resize-none"
                />
              </div>

              <div className="space-y-3">
                <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">Example Prompts</span>
                <div className="flex flex-col gap-2">
                  {EXAMPLE_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => setObjective(prompt)}
                      className="text-left px-4 py-2.5 bg-surface-2 hover:bg-surface-3 border border-border rounded-lg text-sm text-text-primary transition-colors flex items-center gap-2 group"
                    >
                      <ArrowRight className="w-3.5 h-3.5 text-text-muted group-hover:text-accent-blue transition-colors" />
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <button
                  onClick={handleInvestigate}
                  disabled={!objective.trim()}
                  className="btn btn--primary flex items-center gap-2 py-2.5 px-6"
                >
                  Investigate <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* LOADING STATE */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-16 px-4 space-y-8 min-h-[400px]">
              <div className="relative">
                <div className="absolute inset-0 bg-accent-blue/20 blur-xl rounded-full" />
                <Loader2 className="w-12 h-12 text-accent-blue animate-spin relative z-10" />
              </div>
              
              <div className="text-center space-y-1">
                <h3 className="text-lg font-bold text-text-primary">Investigation in progress</h3>
                <p className="text-sm text-text-muted">Agentic execution running up to 5 iterations...</p>
              </div>

              <div className="w-full max-w-sm space-y-3 bg-surface-2 p-5 rounded-xl border border-border">
                {LOADING_STEPS.map((step, idx) => {
                  const isPast = idx < currentStepIndex;
                  const isCurrent = idx === currentStepIndex;
                  
                  return (
                    <div 
                      key={step} 
                      className={`flex items-center gap-3 text-sm transition-all duration-300 ${
                        isPast ? 'text-emerald-400' : isCurrent ? 'text-accent-blue font-medium' : 'text-text-muted opacity-50'
                      }`}
                    >
                      {isPast ? (
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                      ) : isCurrent ? (
                        <ArrowRight className="w-4 h-4 shrink-0 animate-pulse" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border-2 border-current opacity-30 shrink-0" />
                      )}
                      <span>{step}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* RESULT STATE */}
          {!isLoading && result && (
            <div className="space-y-8">
              <div className="flex items-center justify-between border-b border-border pb-4">
                <h3 className="text-xl font-bold text-text-primary">Investigation Report</h3>
                <button onClick={() => { setResult(null); setObjective(''); }} className="text-sm text-accent-blue hover:underline">
                  New Investigation
                </button>
              </div>

              {/* Conclusion */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-text-primary uppercase tracking-wide">Conclusion</h4>
                <div className="p-4 bg-surface-2 border border-border rounded-xl">
                  <p className="text-text-primary leading-relaxed whitespace-pre-wrap">{result.conclusion}</p>
                </div>
              </div>

              {/* Evidence */}
              {result.evidence.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-text-primary uppercase tracking-wide">Evidence</h4>
                  <div className="border border-border rounded-xl overflow-hidden">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-surface-2 border-b border-border">
                        <tr>
                          <th className="px-4 py-3 font-semibold text-text-muted w-48">Source Tool</th>
                          <th className="px-4 py-3 font-semibold text-text-muted">Finding</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {result.evidence.map((ev, idx) => (
                          <tr key={idx} className="bg-surface">
                            <td className="px-4 py-3 align-top">
                              <span className="inline-flex px-2 py-1 text-xs font-mono font-medium bg-surface-3 text-text-primary rounded">
                                {ev.source_tool}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-text-primary leading-relaxed">
                              {ev.finding}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Recommendations */}
                {result.recommendations.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-emerald-400 uppercase tracking-wide">Recommendations</h4>
                    <ul className="space-y-2">
                      {result.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex gap-2 text-sm text-text-primary bg-emerald-500/5 border border-emerald-500/10 p-3 rounded-lg">
                          <span className="text-emerald-400 font-bold">•</span>
                          <span className="leading-relaxed">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Limitations */}
                {result.limitations.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-amber-400 uppercase tracking-wide">Limitations</h4>
                    <ul className="space-y-2">
                      {result.limitations.map((lim, idx) => (
                        <li key={idx} className="flex gap-2 text-sm text-text-primary bg-amber-500/5 border border-amber-500/10 p-3 rounded-lg">
                          <span className="text-amber-400 font-bold">•</span>
                          <span className="leading-relaxed">{lim}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Investigation Trace */}
              {result.trace && result.trace.length > 0 && (
                <div className="mt-8 pt-6 border-t border-border">
                  <button
                    onClick={() => setShowTrace(!showTrace)}
                    className="flex items-center gap-2 text-sm font-medium text-text-muted hover:text-text-primary transition-colors"
                  >
                    {showTrace ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    Investigation trace: {result.iterations_used} iterations · {result.trace.length} tools used
                  </button>
                  
                  {showTrace && (
                    <div className="mt-4 p-4 bg-[#0d1117] border border-border rounded-xl font-mono text-xs overflow-x-auto">
                      {result.trace.map((step, idx) => (
                        <div key={idx} className="flex flex-col">
                          <div className="flex items-center gap-2 text-accent-blue mb-1">
                            <span className="font-bold text-text-muted">Step {step.step}:</span>
                            <span className="font-semibold">{step.tool_name}</span>
                          </div>
                          {idx < result.trace.length - 1 && (
                            <div className="ml-4 my-1 text-text-muted/50">↓</div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

            </div>
          )}

        </div>
      </div>
    </div>
  );
}
