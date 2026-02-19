import { cn } from "@/lib/utils";

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-gradient-to-r from-muted via-muted/50 to-muted bg-[length:200%_100%]",
        "animate-shimmer",
        className
      )}
      {...props}
    />
  );
}

/**
 * Property Card Skeleton
 * Loading state for property cards with image and content sections
 */
export function PropertyCardSkeleton() {
  return (
    <div className="rounded-xl border bg-card overflow-hidden">
      {/* Image skeleton */}
      <Skeleton className="aspect-[4/3] rounded-t-xl rounded-b-none" />

      {/* Content skeleton */}
      <div className="p-5 space-y-3">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />

        {/* Features */}
        <div className="flex gap-4">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-16" />
        </div>

        {/* Badges */}
        <div className="flex flex-wrap gap-2">
          <Skeleton className="h-5 w-12 rounded-full" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t">
          <div className="flex items-center gap-2">
            <Skeleton className="h-6 w-6 rounded-full" />
            <Skeleton className="h-4 w-24" />
          </div>
          <Skeleton className="h-4 w-20" />
        </div>
      </div>
    </div>
  );
}

/**
 * Stat Card Skeleton
 * Loading state for dashboard statistics cards
 */
export function StatCardSkeleton() {
  return (
    <div className="rounded-xl border bg-card p-6">
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-8 w-8 rounded-lg" />
        <Skeleton className="h-5 w-12 rounded-full" />
      </div>
      <Skeleton className="h-8 w-20 mb-1" />
      <Skeleton className="h-4 w-32 mb-3" />
      <Skeleton className="h-10 w-full rounded" />
    </div>
  );
}

/**
 * Table Row Skeleton
 * Loading state for table rows
 */
export function TableRowSkeleton() {
  return (
    <div className="flex items-center gap-4 p-4 border-b">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-3 w-1/3" />
      </div>
      <Skeleton className="h-8 w-20 rounded-full" />
      <Skeleton className="h-8 w-8 rounded" />
    </div>
  );
}

/**
 * Form Skeleton
 * Loading state for forms
 */
export function FormSkeleton() {
  return (
    <div className="space-y-6">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-11 w-full rounded-lg" />
        </div>
      ))}
      <div className="flex gap-3 justify-end pt-4">
        <Skeleton className="h-10 w-24 rounded-lg" />
        <Skeleton className="h-10 w-24 rounded-lg" />
      </div>
    </div>
  );
}
