import { useState } from 'react';
import { X, Tag, Settings2 } from 'lucide-react';
import { useCreateExperiment } from '@/hooks/useExperiments';
import type { ExperimentCreate } from '@/types/experiment.types';

interface CreateExperimentModalProps {
  isOpen: boolean;
  onClose: () => void;
  datasets: { id: string; name: string }[];
}

const DEFAULT_CONFIG_PLACEHOLDER = `{
  "test_size": 0.2,
  "random_state": 42
}`;

export function CreateExperimentModal({
  isOpen,
  onClose,
  datasets,
}: CreateExperimentModalProps) {
  const [name, setName] = useState('');
  const [datasetId, setDatasetId] = useState('');
  const [description, setDescription] = useState('');
  const [objective, setObjective] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [configText, setConfigText] = useState('');
  const [configError, setConfigError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const createMutation = useCreateExperiment();

  const handleClose = () => {
    setName(''); setDatasetId(''); setDescription('');
    setObjective(''); setTagsInput(''); setConfigText('');
    setConfigError(null); setError(null);
    createMutation.reset();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setConfigError(null);

    if (!name.trim()) { setError('Experiment name is required.'); return; }
    if (!datasetId) { setError('Please select a dataset.'); return; }

    let parsedConfig: Record<string, unknown> | null = null;
    if (configText.trim()) {
      try {
        parsedConfig = JSON.parse(configText.trim());
      } catch {
        setConfigError('Invalid JSON. Please check the configuration format.');
        return;
      }
    }

    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    const payload: ExperimentCreate = {
      name: name.trim(),
      dataset_id: datasetId,
      description: description.trim() || null,
      objective: objective.trim() || null,
      default_configuration: parsedConfig,
      tags: tags.length > 0 ? tags : null,
    };

    try {
      await createMutation.mutateAsync(payload);
      handleClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create experiment.');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div
        className="bg-bg border border-border rounded-xl shadow-2xl w-full max-w-xl overflow-hidden flex flex-col"
        style={{ maxHeight: '90vh' }}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between shrink-0">
          <h2 className="text-base font-semibold text-text-primary">Create Experiment</h2>
          <button
            onClick={handleClose}
            className="p-1.5 rounded text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto flex-1">
          {error && (
            <div className="mb-5 p-3 bg-red-500/10 border border-red-500/20 rounded text-sm text-red-400">
              {error}
            </div>
          )}

          <form id="create-experiment-form" onSubmit={handleSubmit} className="space-y-5">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Name <span className="text-red-400">*</span>
              </label>
              <input
                id="exp-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Predict Gut Colonization"
                className="w-full px-3 py-2 bg-surface border border-border rounded text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
              />
            </div>

            {/* Dataset */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Dataset <span className="text-red-400">*</span>
              </label>
              <select
                id="exp-dataset"
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
                className="w-full px-3 py-2 bg-surface border border-border rounded text-sm text-text-primary focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
              >
                <option value="">Select a dataset…</option>
                {datasets.map((ds) => (
                  <option key={ds.id} value={ds.id}>{ds.name}</option>
                ))}
              </select>
            </div>

            {/* Objective */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Objective
              </label>
              <input
                type="text"
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                placeholder="e.g. Binary classification — colonization yes/no"
                className="w-full px-3 py-2 bg-surface border border-border rounded text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                placeholder="Brief description of this experiment…"
                className="w-full px-3 py-2 bg-surface border border-border rounded text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors resize-none"
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <span className="flex items-center gap-1.5"><Tag className="w-3.5 h-3.5" />Tags</span>
              </label>
              <input
                type="text"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                placeholder="classification, biology, pilot (comma separated)"
                className="w-full px-3 py-2 bg-surface border border-border rounded text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
              />
            </div>

            {/* Default Configuration */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <span className="flex items-center gap-1.5"><Settings2 className="w-3.5 h-3.5" />Default Configuration (JSON)</span>
              </label>
              <textarea
                value={configText}
                onChange={(e) => { setConfigText(e.target.value); setConfigError(null); }}
                rows={4}
                placeholder={DEFAULT_CONFIG_PLACEHOLDER}
                className={`w-full px-3 py-2 bg-surface border rounded text-sm font-mono text-text-primary placeholder-text-muted focus:outline-none focus:ring-1 transition-colors resize-none ${
                  configError
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : 'border-border focus:border-accent-blue focus:ring-accent-blue'
                }`}
              />
              {configError && (
                <p className="mt-1.5 text-xs text-red-400">{configError}</p>
              )}
              <p className="mt-1.5 text-xs text-text-muted">
                Runs will inherit this configuration. Run-level overrides take precedence.
              </p>
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border flex justify-end gap-3 shrink-0 bg-surface">
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
            form="create-experiment-form"
            disabled={createMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-accent-blue hover:opacity-90 rounded transition-colors disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creating…' : 'Create Experiment'}
          </button>
        </div>
      </div>
    </div>
  );
}
