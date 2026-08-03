import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  X,
  Download,
  Copy,
  Check,
  FileCode,
  Layers,
  Database,
  Terminal,
  Calendar,
  HardDrive,
  Hash,
} from 'lucide-react';
import { ArtifactTypeBadge } from './ArtifactTypeBadge';
import { formatBytes } from '@/utils/format';
import { getArtifactDownloadUrl } from '@/services/artifact.service';
import type { Artifact, ArtifactDetail } from '@/types/artifact.types';
import type { ExperimentListItem } from '@/types/experiment.types';
import type { DatasetListItem } from '@/types/dataset.types';

interface ArtifactDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  artifact: Artifact | ArtifactDetail | null;
  experiment?: ExperimentListItem;
  dataset?: DatasetListItem;
}

export function ArtifactDetailModal({
  isOpen,
  onClose,
  artifact,
  experiment,
  dataset,
}: ArtifactDetailModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !artifact) return null;

  const handleCopyChecksum = (checksum: string) => {
    navigator.clipboard.writeText(checksum);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasExtraDetails = 'sha256_checksum' in artifact;
  const downloadUrl = getArtifactDownloadUrl(artifact.id);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
      <div className="bg-surface border border-border rounded-xl w-full max-w-lg shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface-2">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-surface border border-border text-accent-blue">
              <FileCode className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-text-primary text-base">Artifact Metadata</h3>
              <p className="text-xs text-text-muted">{artifact.filename}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
          <div className="flex items-center justify-between p-3 rounded-lg bg-surface-2 border border-border">
            <span className="text-xs text-text-muted font-medium">Type</span>
            <ArtifactTypeBadge type={artifact.artifact_type} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-surface-2 border border-border">
              <div className="flex items-center gap-1.5 text-xs text-text-muted mb-1">
                <HardDrive className="w-3.5 h-3.5" />
                <span>File Size</span>
              </div>
              <span className="text-sm font-semibold font-mono text-text-primary">
                {formatBytes(artifact.file_size_bytes)}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-surface-2 border border-border">
              <div className="flex items-center gap-1.5 text-xs text-text-muted mb-1">
                <Calendar className="w-3.5 h-3.5" />
                <span>Created</span>
              </div>
              <span className="text-xs font-medium text-text-primary">
                {new Date(artifact.created_at).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Lineage Info */}
          <div className="space-y-2 pt-2 border-t border-border">
            <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">Lineage</h4>
            
            <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/40">
              <span className="text-xs text-text-muted flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5" /> Run
              </span>
              <Link
                to={`/runs/${artifact.run_id}`}
                className="font-mono text-xs text-accent-blue hover:underline"
              >
                {artifact.run_id.slice(0, 8)}…
              </Link>
            </div>

            <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/40">
              <span className="text-xs text-text-muted flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" /> Experiment
              </span>
              {experiment ? (
                <Link
                  to={`/experiments/${experiment.id}`}
                  className="text-xs text-accent-blue hover:underline font-medium truncate max-w-[220px]"
                >
                  {experiment.name}
                </Link>
              ) : (
                <span className="font-mono text-xs text-text-muted">{artifact.experiment_id.slice(0, 8)}…</span>
              )}
            </div>

            <div className="flex items-center justify-between text-sm py-1.5 border-b border-border/40">
              <span className="text-xs text-text-muted flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5" /> Dataset
              </span>
              {dataset ? (
                <Link
                  to={`/datasets/${dataset.id}`}
                  className="text-xs text-accent-blue hover:underline font-medium truncate max-w-[220px]"
                >
                  {dataset.name}
                </Link>
              ) : (
                <span className="font-mono text-xs text-text-muted">{artifact.dataset_id.slice(0, 8)}…</span>
              )}
            </div>
          </div>

          {/* Technical Info */}
          {hasExtraDetails && (
            <div className="space-y-2 pt-2 border-t border-border">
              <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">Integrity</h4>

              <div className="p-3 rounded-lg bg-surface-2 border border-border">
                <div className="flex items-center justify-between text-xs text-text-muted mb-1">
                  <span className="flex items-center gap-1">
                    <Hash className="w-3.5 h-3.5" /> SHA-256 Checksum
                  </span>
                  <button
                    onClick={() => handleCopyChecksum((artifact as ArtifactDetail).sha256_checksum)}
                    className="flex items-center gap-1 text-accent-blue hover:underline text-[11px]"
                  >
                    {copied ? <Check className="w-3 h-3 text-accent-emerald" /> : <Copy className="w-3 h-3" />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <code className="text-[11px] font-mono text-text-secondary break-all select-all block">
                  {(artifact as ArtifactDetail).sha256_checksum}
                </code>
              </div>

              {(artifact as ArtifactDetail).mime_type && (
                <div className="flex items-center justify-between text-xs py-1">
                  <span className="text-text-muted">MIME Type</span>
                  <code className="text-text-secondary font-mono">{(artifact as ArtifactDetail).mime_type}</code>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border bg-surface-2 flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="btn btn--secondary text-xs px-4 py-2"
          >
            Close
          </button>
          <a
            href={downloadUrl}
            download={artifact.filename}
            className="btn btn--primary text-xs px-4 py-2 inline-flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" /> Download File
          </a>
        </div>
      </div>
    </div>
  );
}
