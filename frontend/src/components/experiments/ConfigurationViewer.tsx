interface ConfigurationViewerProps {
  config: Record<string, unknown> | null | undefined;
  emptyMessage?: string;
}

export function ConfigurationViewer({
  config,
  emptyMessage = 'No configuration defined.',
}: ConfigurationViewerProps) {
  if (!config || Object.keys(config).length === 0) {
    return (
      <p className="text-sm text-text-muted italic">{emptyMessage}</p>
    );
  }

  return (
    <div className="bg-bg border border-border rounded-lg overflow-hidden">
      <div className="px-3 py-2 bg-surface-2 border-b border-border">
        <span className="text-xs font-mono text-text-muted tracking-wider uppercase">
          JSON Configuration
        </span>
      </div>
      <pre className="p-4 text-sm font-mono text-text-primary overflow-x-auto leading-relaxed">
        <code>{JSON.stringify(config, null, 2)}</code>
      </pre>
    </div>
  );
}
