import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Trash2, Database, Table2, FileBarChart, HardDrive, AlertCircle, Sparkles } from 'lucide-react';
import { formatBytes } from '@/utils/format';
import { useDataset, useDatasetPreview, useDatasetStatistics, useDeleteDataset } from '../hooks/useDatasets';
import { StatusBadge } from '../components/datasets/StatusBadge';
import { PreviewTable } from '../components/datasets/PreviewTable';
import { StatisticsPanel } from '../components/datasets/StatisticsPanel';
import { AIInsightsTab } from '../components/datasets/AIInsightsTab';

export function DatasetDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'schema' | 'preview' | 'statistics' | 'storage' | 'ai_insights'>('overview');
  
  const { data: dataset, isLoading, error } = useDataset(id!);
  const { data: preview, isLoading: isLoadingPreview, error: previewError } = useDatasetPreview(id!);
  const { data: stats, isLoading: isLoadingStats, error: statsError } = useDatasetStatistics(id!);
  
  const deleteMutation = useDeleteDataset();

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this dataset? This action cannot be undone and will delete the files from storage.')) {
      try {
        await deleteMutation.mutateAsync(id!);
        navigate('/datasets');
      } catch (err) {
        console.error('Failed to delete dataset', err);
        alert('Failed to delete dataset');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="page flex items-center justify-center min-h-[60vh]">
        <div className="text-text-muted animate-pulse flex flex-col items-center gap-3">
          <Database className="w-8 h-8 opacity-50" />
          <p>Loading dataset details...</p>
        </div>
      </div>
    );
  }

  if (error || !dataset) {
    return (
      <div className="page">
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold mb-1">Failed to load dataset</h3>
            <p className="text-sm opacity-90">{(error as Error)?.message || 'Dataset not found'}</p>
          </div>
        </div>
        <button onClick={() => navigate('/datasets')} className="mt-4 btn btn--secondary inline-flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Datasets
        </button>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: <Database className="w-4 h-4" /> },
    { id: 'schema', label: 'Schema', icon: <Table2 className="w-4 h-4" /> },
    { id: 'preview', label: 'Preview', icon: <Table2 className="w-4 h-4" /> },
    { id: 'statistics', label: 'Statistics', icon: <FileBarChart className="w-4 h-4" /> },
    { id: 'storage', label: 'Storage', icon: <HardDrive className="w-4 h-4" /> },
    { id: 'ai_insights', label: '✨ AI Insights', icon: <Sparkles className="w-4 h-4 text-purple-400" /> },
  ] as const;

  return (
    <div className="page h-[calc(100vh-[var(--header-height)])] flex flex-col">
      {/* Header */}
      <div className="flex-none pb-6">
        <button 
          onClick={() => navigate('/datasets')}
          className="text-text-muted hover:text-text-primary flex items-center gap-1.5 text-sm font-medium mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Datasets
        </button>

        <div className="flex items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-text-primary tracking-tight">{dataset.name}</h1>
              <StatusBadge status={dataset.status} />
              <span className="text-xs font-mono text-text-muted bg-surface-2 px-2 py-0.5 rounded">
                {dataset.version}
              </span>
            </div>
            <p className="text-text-muted text-sm max-w-2xl mt-2 leading-relaxed">
              {dataset.description || 'No description provided.'}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="btn bg-red-500/10 text-red-500 hover:bg-red-500/20 border border-red-500/20 flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-none border-b border-border mb-6">
        <div className="flex gap-6 overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-accent-blue text-accent-blue'
                  : 'border-transparent text-text-muted hover:text-text-primary'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto pb-8 min-h-0">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Total Rows" value={dataset.row_count?.toLocaleString() ?? '-'} />
            <StatCard label="Total Columns" value={dataset.column_count?.toLocaleString() ?? '-'} />
            <StatCard 
              label="File Size" 
              value={formatBytes(dataset.file_size_bytes)} 
            />
            <StatCard 
              label="Uploaded On" 
              value={new Date(dataset.created_at).toLocaleDateString()} 
            />
          </div>
        )}

        {activeTab === 'schema' && (
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-2 border-b border-border">
                  <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase">Column Name</th>
                  <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase">Data Type (Pandas)</th>
                  <th className="px-4 py-3 text-xs font-medium tracking-wider text-text-muted uppercase">Missing Values</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {dataset.column_names?.map(col => (
                  <tr key={col} className="hover:bg-white/5 transition-colors">
                    <td className="px-4 py-3 font-medium text-text-primary text-sm">{col}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs font-mono text-text-muted bg-surface-2 px-2 py-1 rounded">
                        {dataset.dtypes?.[col] ?? 'unknown'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {(() => {
                        const count = dataset.missing_values?.[col] ?? 0;
                        const total = dataset.row_count ?? 1;
                        const percent = ((count / total) * 100).toFixed(1);
                        return (
                          <span className={`${count > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                            {count.toLocaleString()} <span className="opacity-70 text-xs">({percent}%)</span>
                          </span>
                        );
                      })()}
                    </td>
                  </tr>
                ))}
                {!dataset.column_names?.length && (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-text-muted">
                      Schema not available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'preview' && (
          <div className="h-[600px] min-h-0">
            {isLoadingPreview ? (
              <div className="h-full flex items-center justify-center text-text-muted">
                Loading preview...
              </div>
            ) : previewError ? (
              <div className="p-4 text-red-400">Failed to load preview.</div>
            ) : preview ? (
              <PreviewTable preview={preview} />
            ) : null}
          </div>
        )}

        {activeTab === 'statistics' && (
          <div className="pb-8">
            {isLoadingStats ? (
              <div className="flex items-center justify-center py-12 text-text-muted">
                Loading statistics...
              </div>
            ) : statsError ? (
              <div className="p-4 text-red-400">Failed to load statistics.</div>
            ) : stats ? (
              <StatisticsPanel stats={stats} />
            ) : null}
          </div>
        )}

        {activeTab === 'storage' && (
          <div className="bg-surface border border-border rounded-lg p-6">
            <h3 className="text-lg font-medium text-text-primary mb-4">Storage Information</h3>
            <div className="space-y-4">
              <div>
                <span className="block text-sm text-text-muted mb-1">Internal Storage Path</span>
                <code className="text-sm bg-surface-2 px-2 py-1 rounded text-text-primary break-all">
                  {dataset.storage_path || 'Not stored yet'}
                </code>
              </div>
              <div>
                <span className="block text-sm text-text-muted mb-1">Original Filename</span>
                <span className="text-sm text-text-primary">{dataset.original_filename}</span>
              </div>
              <div>
                <span className="block text-sm text-text-muted mb-1">File Hash (SHA-256)</span>
                <code className="text-sm bg-surface-2 px-2 py-1 rounded text-text-primary break-all">
                  {dataset.file_hash}
                </code>
              </div>
              <div>
                <span className="block text-sm text-text-muted mb-1">Database ID</span>
                <code className="text-sm bg-surface-2 px-2 py-1 rounded text-text-primary">
                  {dataset.id}
                </code>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'ai_insights' && (
          <AIInsightsTab datasetId={id!} />
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-5">
      <span className="block text-sm text-text-muted mb-2 font-medium uppercase tracking-wider">{label}</span>
      <span className="block text-2xl font-bold text-text-primary tracking-tight">{value}</span>
    </div>
  );
}
