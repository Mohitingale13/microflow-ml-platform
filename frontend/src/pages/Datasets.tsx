import { useState } from 'react';
import { UploadCloud } from 'lucide-react';
import { DatasetTable } from '../components/datasets/DatasetTable';
import { UploadModal } from '../components/datasets/UploadModal';
import { useDatasets } from '../hooks/useDatasets';

export function Datasets() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const { data: datasets, isLoading, error } = useDatasets();

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2 className="page-title">Datasets</h2>
          <p className="page-subtitle">Upload, version, and manage training datasets</p>
        </div>
        <button 
          onClick={() => setIsUploadModalOpen(true)}
          className="btn btn--primary flex items-center gap-2"
        >
          <UploadCloud className="w-4 h-4" />
          Upload Dataset
        </button>
      </div>

      {error ? (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
          Error loading datasets: {(error as Error).message}
        </div>
      ) : (
        <div className="bg-bg rounded-lg">
          <DatasetTable data={datasets || []} isLoading={isLoading} />
        </div>
      )}

      <UploadModal 
        isOpen={isUploadModalOpen} 
        onClose={() => setIsUploadModalOpen(false)} 
      />
    </div>
  );
}
