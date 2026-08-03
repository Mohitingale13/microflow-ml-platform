import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, X, FileText, AlertCircle } from 'lucide-react';
import { formatBytes } from '../../utils/format';
import { useUploadDataset } from '../../hooks/useDatasets';
import { cn } from '../../utils/cn';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const uploadMutation = useUploadDataset();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError(null);
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      if (!name) {
        // Auto-fill name from filename if empty
        setName(acceptedFiles[0].name.replace('.csv', ''));
      }
    }
  }, [name]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
    multiple: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!file) {
      setError('Please select a file to upload.');
      return;
    }
    if (!name.trim()) {
      setError('Dataset name is required.');
      return;
    }

    const formData = new FormData();
    formData.append('name', name);
    if (description) formData.append('description', description);
    formData.append('file', file);

    try {
      await uploadMutation.mutateAsync(formData);
      handleClose();
    } catch (err: any) {
      setError(err.message || 'An error occurred during upload.');
    }
  };

  const handleClose = () => {
    setName('');
    setDescription('');
    setFile(null);
    setError(null);
    uploadMutation.reset();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div 
        className="bg-bg border border-border rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary">Upload Dataset</h2>
          <button 
            onClick={handleClose}
            className="p-1.5 rounded-md text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[80vh]">
          {error && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-md flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <form id="upload-form" onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-text-primary mb-1.5">
                Dataset Name <span className="text-red-400">*</span>
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Single Cell RNA-Seq v1"
                className="w-full px-3 py-2 bg-surface border border-border rounded-md text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
                disabled={uploadMutation.isPending}
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-text-primary mb-1.5">
                Description
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Briefly describe the contents of this dataset..."
                rows={3}
                className="w-full px-3 py-2 bg-surface border border-border rounded-md text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors resize-none"
                disabled={uploadMutation.isPending}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                CSV File <span className="text-red-400">*</span>
              </label>
              <div
                {...getRootProps()}
                className={cn(
                  "border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-colors",
                  isDragActive 
                    ? "border-accent-blue bg-blue-500/5" 
                    : "border-border hover:bg-surface-2 bg-surface",
                  uploadMutation.isPending && "opacity-50 cursor-not-allowed pointer-events-none"
                )}
              >
                <input {...getInputProps()} />
                
                {file ? (
                  <div className="flex flex-col items-center gap-2">
                    <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-accent-blue" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text-primary truncate max-w-[200px] sm:max-w-[300px]">{file.name}</p>
                      <p className="text-xs text-text-muted mt-0.5">
                        {formatBytes(file.size)}
                      </p>
                    </div>
                    <button 
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setFile(null); }}
                      className="mt-2 text-xs text-red-400 hover:text-red-300 font-medium"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <div className="w-10 h-10 rounded-full bg-surface-2 flex items-center justify-center mb-2">
                      <UploadCloud className="w-5 h-5 text-text-muted" />
                    </div>
                    <p className="text-sm font-medium text-text-primary">
                      Click to upload or drag and drop
                    </p>
                    <p className="text-xs text-text-muted">
                      CSV files only (Max 100MB)
                    </p>
                  </div>
                )}
              </div>
            </div>
          </form>
        </div>

        <div className="px-6 py-4 border-t border-border bg-surface flex justify-end gap-3 mt-auto">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-text-primary hover:bg-surface-2 rounded-md transition-colors border border-border"
            disabled={uploadMutation.isPending}
          >
            Cancel
          </button>
          <button
            type="submit"
            form="upload-form"
            disabled={!file || !name.trim() || uploadMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-accent-blue hover:opacity-90 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {uploadMutation.isPending ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Uploading...
              </>
            ) : (
              'Upload Dataset'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
