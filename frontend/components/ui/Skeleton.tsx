"use client";

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-md bg-gray-200 ${className}`}
      aria-hidden
    />
  );
}

export function PublicWishlistSkeleton() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <Skeleton className="mb-2 h-8 w-3/4" />
      <Skeleton className="mb-8 h-4 w-full" />
      <ul className="space-y-4">
        {[1, 2, 3].map((i) => (
          <li key={i} className="rounded-xl border border-gray-200 bg-white p-4">
            <div className="flex gap-4">
              <Skeleton className="h-24 w-24 shrink-0 rounded-lg" />
              <div className="min-w-0 flex-1 space-y-2">
                <Skeleton className="h-5 w-4/5" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-1/3" />
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <Skeleton className="h-9 w-24 rounded-lg" />
              <Skeleton className="h-9 w-28 rounded-lg" />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-8 flex justify-between">
        <Skeleton className="h-8 w-48" />
        <div className="flex gap-2">
          <Skeleton className="h-9 w-20 rounded-lg" />
          <Skeleton className="h-9 w-24 rounded-lg" />
        </div>
      </div>
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-24 w-full rounded-xl" />
        ))}
      </div>
    </div>
  );
}

export function EditWishlistSkeleton() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <Skeleton className="mb-4 h-4 w-24" />
      <div className="flex justify-between gap-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-9 w-28 rounded-lg" />
      </div>
      <Skeleton className="mt-8 mb-4 h-6 w-20" />
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <Skeleton key={i} className="h-16 w-full rounded-xl" />
        ))}
      </div>
    </div>
  );
}
