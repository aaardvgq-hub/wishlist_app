"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import type { WishlistWithItems } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/EmptyState";
import { AddItemForm } from "@/components/AddItemForm";
import { EditWishlistSkeleton } from "@/components/ui/Skeleton";

export default function EditWishlistPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const id = params.id as string;
  const showAdd = searchParams.get("add") === "1";

  const { data: wishlist, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["wishlist", id],
    queryFn: () => api.get<WishlistWithItems>(`/wishlists/${id}`),
    enabled: !!id && id !== "new",
  });

  // Owner view: API returns items without contributor identities (reserved/contributed_total not exposed to owner).
  const items = wishlist?.items?.filter((i) => !i.is_deleted) ?? [];

  async function handleDeleteItem(itemId: string) {
    if (!confirm("Remove this item?")) return;
    try {
      await api.delete(`/items/${itemId}`);
      queryClient.invalidateQueries({ queryKey: ["wishlist", id] });
    } catch {
      // could show toast
    }
  }

  if (id === "new") {
    router.replace("/wishlist/new");
    return null;
  }

  if (isLoading) {
    return <EditWishlistSkeleton />;
  }

  if (isError || !wishlist) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <p className="text-gray-600">Wishlist not found or you don't have access.</p>
        <p className="mt-1 text-sm text-gray-500">{error instanceof Error ? error.message : ""}</p>
        <Button className="mt-4" variant="secondary" onClick={() => refetch()}>Try again</Button>
        <Link href="/dashboard" className="ml-2 inline-block">
          <Button variant="ghost">Back to dashboard</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto min-h-screen max-w-2xl px-4 py-6 sm:py-8">
      <Link href="/dashboard" className="text-sm text-primary-600 hover:underline">
        ← Dashboard
      </Link>
      <header className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{wishlist.title}</h1>
          {wishlist.description && (
            <p className="mt-1 text-sm text-gray-500">{wishlist.description}</p>
          )}
          <p className="mt-2 text-xs text-gray-400">
            Share link: /public/{wishlist.share_token}
          </p>
        </div>
        <Button onClick={() => router.push("/dashboard")} variant="secondary">
          Back to list
        </Button>
      </header>

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900">Items</h2>
        {showAdd && (
          <div className="mt-4">
            <AddItemForm
              wishlistId={id}
              onSuccess={() => {
                queryClient.invalidateQueries({ queryKey: ["wishlist", id] });
                router.replace(`/wishlist/${id}/edit`);
              }}
              onCancel={() => router.replace(`/wishlist/${id}/edit`)}
            />
          </div>
        )}
        {!showAdd && items.length === 0 ? (
          <EmptyState
            title="No items yet"
            description="Add a gift idea with title, link, and optional price. Friends can reserve or contribute."
            action={
              <Button onClick={() => router.push(`/wishlist/${id}/edit?add=1`)}>
                Add first item
              </Button>
            }
          />
        ) : !showAdd ? (
          <ul className="mt-4 space-y-3">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between gap-4 rounded-xl border border-gray-200 bg-white p-4"
              >
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-gray-900">{item.title}</p>
                  {item.target_price && item.target_price !== "0" && (
                    <p className="text-sm text-gray-500">Target: {item.target_price}</p>
                  )}
                </div>
                <Button
                  variant="ghost"
                  className="text-red-600 hover:bg-red-50"
                  onClick={() => handleDeleteItem(item.id)}
                >
                  Remove
                </Button>
              </li>
            ))}
          </ul>
        ) : null}
        {!showAdd && items.length > 0 && (
          <div className="mt-4">
            <Button onClick={() => router.push(`/wishlist/${id}/edit?add=1`)}>
              Add item
            </Button>
          </div>
        )}
      </section>
    </div>
  );
}
