/**
 * DevotionalCardSkeleton - Loading skeleton for devotional cards
 * Matches the actual card layout with animated shimmer effect
 */
export function DevotionalCardSkeleton() {
  return (
    <div className="bg-card rounded-3xl border border-border p-6 md:p-8 animate-pulse">
      {/* Author */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-muted animate-shimmer" />
        <div className="flex-1">
          <div className="h-4 w-32 bg-muted rounded mb-2 animate-shimmer" />
          <div className="h-3 w-24 bg-muted rounded animate-shimmer" />
        </div>
      </div>

      {/* Category badge */}
      <div className="h-6 w-20 bg-muted rounded-full mb-3 animate-shimmer" />

      {/* Title */}
      <div className="h-8 w-3/4 bg-muted rounded mb-3 animate-shimmer" />
      <div className="h-8 w-1/2 bg-muted rounded mb-4 animate-shimmer" />

      {/* Excerpt */}
      <div className="space-y-2 mb-4">
        <div className="h-4 w-full bg-muted rounded animate-shimmer" />
        <div className="h-4 w-full bg-muted rounded animate-shimmer" />
        <div className="h-4 w-3/4 bg-muted rounded animate-shimmer" />
      </div>

      {/* Scripture tag */}
      <div className="h-8 w-32 bg-muted rounded-lg animate-shimmer" />
    </div>
  );
}

/**
 * FeedSkeleton - Multiple skeleton cards for feed page
 */
export function FeedSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-6">
      {Array.from({ length: count }).map((_, i) => (
        <DevotionalCardSkeleton key={i} />
      ))}
    </div>
  );
}

/**
 * SeriesCardSkeleton - Loading skeleton for series cards
 * Matches the SeriesCard layout with cover image and content
 */
export function SeriesCardSkeleton() {
  return (
    <div className="bg-card rounded-3xl border border-border overflow-hidden h-full">
      {/* Cover Image Skeleton */}
      <div className="h-48 md:h-56 bg-muted animate-pulse relative">
        {/* Count Badge Skeleton */}
        <div className="absolute bottom-4 right-4 bg-white/95 dark:bg-black/95 backdrop-blur-sm px-4 py-2 rounded-full">
          <div className="h-5 w-24 bg-muted animate-shimmer rounded" />
        </div>
      </div>

      {/* Content Skeleton */}
      <div className="p-6">
        {/* Title Skeleton */}
        <div className="h-7 w-3/4 bg-muted rounded mb-2 animate-shimmer" />
        <div className="h-7 w-1/2 bg-muted rounded mb-4 animate-shimmer" />

        {/* Description Skeleton */}
        <div className="space-y-2 mb-4">
          <div className="h-4 w-full bg-muted rounded animate-shimmer" />
          <div className="h-4 w-full bg-muted rounded animate-shimmer" />
          <div className="h-4 w-3/4 bg-muted rounded animate-shimmer" />
        </div>

        {/* Author Skeleton */}
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-muted rounded-full animate-shimmer" />
          <div className="h-4 w-28 bg-muted rounded animate-shimmer" />
        </div>
      </div>
    </div>
  );
}

/**
 * SeriesGridSkeleton - Grid of series card skeletons
 */
export function SeriesGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
      {Array.from({ length: count }).map((_, i) => (
        <SeriesCardSkeleton key={i} />
      ))}
    </div>
  );
}
