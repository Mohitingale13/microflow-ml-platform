interface LoadingSkeletonProps {
  rows?: number;
  cols?: number;
}

export function TableSkeleton({ rows = 5, cols = 5 }: LoadingSkeletonProps) {
  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="divide-y divide-border">
        {/* Header */}
        <div className="grid gap-4 px-4 py-3 bg-surface-2" style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
          {Array.from({ length: cols }).map((_, i) => (
            <div key={i} className="h-3 bg-border rounded animate-pulse" />
          ))}
        </div>
        {/* Rows */}
        {Array.from({ length: rows }).map((_, r) => (
          <div
            key={r}
            className="grid gap-4 px-4 py-4"
            style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
          >
            {Array.from({ length: cols }).map((_, c) => (
              <div
                key={c}
                className="h-3 bg-surface-2 rounded animate-pulse"
                style={{ width: c === 0 ? '70%' : c === cols - 1 ? '40%' : '55%' }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function CardSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-surface border border-border rounded-lg p-5 animate-pulse">
          <div className="h-4 bg-surface-2 rounded w-1/3 mb-3" />
          <div className="h-7 bg-surface-2 rounded w-1/2 mb-2" />
          <div className="h-3 bg-surface-2 rounded w-3/4" />
        </div>
      ))}
    </div>
  );
}
