import { useState } from 'react';
import { Play, X, AlertCircle, Loader2 } from 'lucide-react';
import type { Dataset } from '@/types/dataset.types';

interface ExecuteRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExecute: (payload: { target_column: string; test_split?: number }) => Promise<void>;
  isLoading: boolean;
  dataset?: Dataset | null;
  defaultSplit?: number;
}

export function ExecuteRunModal({
  isOpen,
  onClose,
  onExecute,
  isLoading,
  dataset,
  defaultSplit = 0.2,
}: ExecuteRunModalProps) {
  const [isCustomColumn, setIsCustomColumn] = useState(false);
  const [customColumnText, setCustomColumnText] = useState('');
  const [targetColumn, setTargetColumn] = useState('');
  const [testSplit, setTestSplit] = useState(defaultSplit);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const effectiveColumn = isCustomColumn ? customColumnText.trim() : targetColumn.trim();
    if (!effectiveColumn) {
      setError('Please select or specify a target column.');
      return;
    }
    setError(null);
    try {
      await onExecute({
        target_column: effectiveColumn,
        test_split: Number(testSplit),
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Execution failed');
    }
  };

  const availableColumns = dataset?.column_names || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-surface border border-border rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface-2">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent-blue/10 flex items-center justify-center">
              <Play className="w-4 h-4 text-accent-blue" />
            </div>
            <div>
              <h3 className="font-semibold text-text-primary text-base">Execute Training Pipeline</h3>
              <p className="text-xs text-text-muted">Train and evaluate model on dataset</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-surface transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                Target Column <span className="text-accent-red">*</span>
              </label>
              {availableColumns.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    setIsCustomColumn(!isCustomColumn);
                    setError(null);
                  }}
                  className="text-[11px] text-accent-blue hover:underline font-medium"
                >
                  {isCustomColumn ? 'Pick from dataset' : 'Type custom column'}
                </button>
              )}
            </div>

            {availableColumns.length > 0 && !isCustomColumn ? (
              <select
                value={targetColumn}
                onChange={(e) => setTargetColumn(e.target.value)}
                disabled={isLoading}
                className="w-full px-3 py-2 bg-surface-2 border border-border rounded text-sm text-text-primary focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
              >
                <option value="">Select target column to predict…</option>
                {availableColumns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={isCustomColumn ? customColumnText : targetColumn}
                onChange={(e) => {
                  if (isCustomColumn) setCustomColumnText(e.target.value);
                  else setTargetColumn(e.target.value);
                }}
                placeholder="e.g. variety, species, or invalid_column"
                disabled={isLoading}
                className="w-full px-3 py-2 bg-surface-2 border border-border rounded text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
              />
            )}
            <p className="text-[11px] text-text-muted mt-1">
              {isCustomColumn 
                ? 'Type any column name (useful for testing error handling).'
                : 'The label / classification column the model will learn to predict.'}
            </p>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                Test Split Ratio
              </label>
              <span className="text-xs font-mono font-bold text-accent-blue">
                {Math.round(testSplit * 100)}% test / {Math.round((1 - testSplit) * 100)}% train
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="0.5"
              step="0.05"
              value={testSplit}
              onChange={(e) => setTestSplit(parseFloat(e.target.value))}
              disabled={isLoading}
              className="w-full accent-accent-blue cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-text-muted mt-0.5">
              <span>10% (0.1)</span>
              <span>20% (Default)</span>
              <span>50% (0.5)</span>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-border mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-text-muted hover:text-text-primary rounded transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn--primary flex items-center gap-2 px-5 py-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Training Model…
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Execute Run
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
