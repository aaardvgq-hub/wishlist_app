"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Wishlist } from "@/lib/types";
import { useAuthStore } from "@/stores/auth";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/EmptyState";
import { DashboardSkeleton } from "@/components/ui/Skeleton";

export default function DashboardPage() {
  const router = useRouter();
  const { user, fetchUser, logout } = useAuthStore();
  useEffect(() => {
    fetchUser();
  }, [fetchUser]);
  const { data: wishlists = [], isLoading, isError, error, refetch } = useQuery({
    queryKey: ["wishlists"],
    queryFn: () => api.get<Wishlist[]>("/wishlists/"),
    retry: 1,
  });

  if (isError) {
    const is401 = error instanceof Error && (error.message.includes("401") || error.message.includes("Unauthorized"));
    if (is401) {
      router.push("/login");
      return null;
    }
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 text-center">
        <p className="text-gray-600">Failed to load wishlists.</p>
        <p className="mt-1 text-sm text-gray-500">{error instanceof Error ? error.message : "Unknown error"}</p>
        <Button className="mt-4" variant="secondary" onClick={() => refetch()}>Try again</Button>
      </div>
    );
  }

  async function handleLogout() {
    await logout();
    router.push("/login");
    router.refresh();
  }

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="mx-auto min-h-screen max-w-3xl px-4 py-6 sm:py-8">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My wishlists</h1>
          {user?.email && <p className="text-sm text-gray-500">{user.email}</p>}
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={() => fetchUser()}>
            Refresh
          </Button>
          <Button variant="secondary" onClick={handleLogout}>
            Log out
          </Button>
        </div>
      </header>

      {wishlists.length === 0 ? (
        <EmptyState
          title="No wishlists yet"
          description="Create your first list and share the link with friends so they can reserve or contribute to gifts."
          action={
            <Button onClick={() => router.push("/wishlist/new")}>Create wishlist</Button>
          }
        />
      ) : (
        <>
          <div className="mb-6 flex justify-end">
            <Button onClick={() => router.push("/wishlist/new")}>New wishlist</Button>
          </div>
          <ul className="space-y-3">
            {wishlists.map((w) => (
              <li key={w.id}>
                <Link
                  href={`/wishlist/${w.id}/edit`}
                  className="block rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:border-primary-200 hover:shadow"
                >
                  <h2 className="font-semibold text-gray-900">{w.title}</h2>
                  {w.description && (
                    <p className="mt-1 line-clamp-2 text-sm text-gray-500">{w.description}</p>
                  )}
                  <p className="mt-2 text-xs text-gray-400">
                    Share: /public/{w.share_token}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
