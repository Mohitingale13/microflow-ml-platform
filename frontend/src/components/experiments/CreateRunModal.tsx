import { useState } from 'react';
import { X } from 'lucide-react';
import { useCreateRun } from '@/hooks/useExperiments';
import type { RunCreate } from '@/types/experiment.types';

interface CreateRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  experimentId: string;
  experimentDefaultConfig?: Record<string, unknown> | null;
}

import { SUPPORTED_MODELS } from '@/utils/format';

export function CreateRunModal({
  isOpen,
  onClose,
  experimentId,
  experimentDefaultConfig,
}: CreateRunModalProps) {
  const [modelType, setModelType] = useState('');
  const [configText, setConfigText] = useState('');
  const [notes, setNotes] = useState('');
  const [configError, setConfigError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const createMutation = useCreateRun();

  const handleClose = () => {
    setModelType(''); setConfigText(''); setNotes('');
    setConfigError(null); setError(null);
    createMutation.reset();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setConfigError(null);

    let parsedConfig: Record<string, unknown> | null = null;
    if (configText.trim()) {
      try {
        parsedConfig = JSON.parse(configText.trim());
      } catch {
        setConfigError('Invalid JSON in run configuration.');
        return;
      }
    }

    const payload: RunCreate = {
      experiment_id: experimentId,
      model_type: modelType || null,
      training_configuration: parsedConfig,
      notes: notes.trim() || null,
    };

    try {
      await createMutation.mutateAsync(payload);
      handleClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create run.');
    }
  };

  if (!isOpen) return null;

  const configPlaceholder = experimentDefaultConfig
    ? JSON.stringify(experimentDefaultConfig, null, 2)
    : '{\n  "test_size": 0.2\n}';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-bg border border-border rounded-xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="text-base font-semibold text-text-primary">New Run</h2>
          <button
            onClick={handleClose}
            className="p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto">
          {error && (
            <div className="mb-5 p-3 bg-red-500/10 border border-red-500/20 rounded text-sm text-red-400">
              {error}
            </div>
          )}

          {experimentDefaultConfig && (
            <div className="mb-5 p-3 bg-accent-blue/5 border border-accent-blue/20 rounded text-xs text-text-muted">
              <span className="text-accent-blue font-medium">Note:</span> This run will inherit
              the experiment's default configuration. Add overrides below.
            </div>
          )}

          <form id="create-run-form" onSubmit={handleSubmit} className="space-y-5">
            {/* Model Type */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Model Type
              </label>
              <select
                id="run-model"
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                className="w-full px-3 py-2 bg-surface border border-border rounded text-sm text-text-primary focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
              >
                <option value="">None (inherit from config)</option>
                {SUPPORTED_MODELS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>

            {/* Config Override */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Configuration Override (JSON)
              </label>
              <textarea
                value={configText}
                onChange={(e) => { setConfigText(e.target.value); setConfigError(null); }}
                rows={5}
                placeholder={configPlaceholder}
                className={`w-full px-3 py-2 bg-surface border rounded text-sm font-mono text-text-primary placeholder-text-muted focus:outline-none focus:ring-1 transition-colors resize-none ${
                  configError
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : 'border-border focus:border-accent-blue focus:ring-accent-blue'
                }`}
              />
              {configError && <p className="mt-1.5 text-xs text-red-400">{configError}</p>}
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="What are you testing in this run?"
                className="w-full px-3 py-2 bg-surface border border-border rounded text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors resize-none"
              />
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border flex justify-end gap-3 bg-surface">
          <button
            type="button"
            onClick={handleClose}
            disabled={createMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-text-primary border border-border rounded hover:bg-surface-2 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="create-run-form"
            disabled={createMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-accent-blue hover:opacity-90 rounded transition-colors disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creating…' : 'Create Run'}
          </button>
        </div>
      </div>
    </div>
  );
}
