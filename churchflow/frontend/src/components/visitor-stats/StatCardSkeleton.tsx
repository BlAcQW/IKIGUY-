/**
 * Stat Card Skeleton Component
 *
 * Loading placeholder that matches StatCard dimensions.
 * Provides smooth shimmer animation while data loads.
 */

export default function StatCardSkeleton() {
  return (
    <div className="relative overflow-hidden bg-white rounded-lg border border-gray-200 border-l-4 border-l-gray-300 p-4 shadow-sm">
      <div className="animate-pulse">
        {/* Header skeleton */}
        <div className="flex items-center justify-between mb-3">
          <div className="h-3 bg-gray-200 rounded w-1/3"></div>
          <div className="w-8 h-8 bg-gray-100 rounded-md"></div>
        </div>

        {/* Value skeleton */}
        <div className="mb-3">
          <div className="h-9 bg-gray-200 rounded w-2/3"></div>
        </div>

        {/* Sparkline skeleton */}
        <div className="mb-2 h-7 bg-gray-100 rounded"></div>

        {/* Footer skeleton */}
        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
      </div>

      {/* Shimmer effect overlay */}
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/40 to-transparent"></div>
    </div>
  );
}
