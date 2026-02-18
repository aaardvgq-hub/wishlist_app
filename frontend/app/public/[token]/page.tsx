"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useCallback, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { WishlistPublic, WishlistItemPublic } from "@/lib/types";
import { useWishlistWebSocket } from "@/hooks/useWebSocket";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { EmptyState } from "@/components/EmptyState";
import { PublicWishlistSkeleton } from "@/components/ui/Skeleton";

export default function PublicWishlistPage() {
  const params = useParams();
  const token = params.token as string;
  const queryClient = useQueryClient();
  const [contributingItem, setContributingItem] = useState<string | null>(null);
  const [reservingItemId, setReservingItemId] = useState<string | null>(null);
  const [contributingItemId, setContributingItemId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const contributeSubmittingRef = useRef(false);

  const { data: wishlist, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["public-wishlist", token],
    queryFn: () => api.get<WishlistPublic>(`/wishlists/public/${token}`),
    enabled: !!token,
  });

  const updateCacheFromWs = useCallback(
    (payload: { item_id?: string; contributed_total?: string; target_price?: string; progress_percent?: number }) => {
      if (!payload.item_id) return;
      queryClient.setQueryData<WishlistPublic>(["public-wishlist", token], (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          items: prev.items.map((it) => {
            if (it.id !== payload.item_id) return it;
            return {
              ...it,
              ...(payload.contributed_total != null && { contributed_total: payload.contributed_total }),
              ...(payload.target_price != null && { target_price: payload.target_price }),
              ...(payload.progress_percent != null && { contribution_progress_percent: payload.progress_percent }),
            };
          }),
        };
      });
    },
    [queryClient, token]
  );

  useWishlistWebSocket(wishlist?.id ?? null, useCallback((msg) => {
    const pl = msg.payload as Record<string, unknown>;
    if (msg.event === "contribution_added" && pl?.item_id) {
      updateCacheFromWs({
        item_id: pl.item_id as string,
        contributed_total: pl.contributed_total as string,
        target_price: pl.target_price as string,
        progress_percent: pl.progress_percent as number,
      });
    }
    if (msg.event === "reservation_created" || msg.event === "reservation_cancelled") {
      queryClient.invalidateQueries({ queryKey: ["public-wishlist", token] });
    }
    if (msg.event === "item_updated") {
      queryClient.invalidateQueries({ queryKey: ["public-wishlist", token] });
    }
  }, [queryClient, token, updateCacheFromWs]));

  async function handleReserve(itemId: string) {
    if (reservingItemId) return;
    setReservingItemId(itemId);
    setErrorMessage(null);
    const prev = queryClient.getQueryData<WishlistPublic>(["public-wishlist", token]);
    queryClient.setQueryData<WishlistPublic>(["public-wishlist", token], (old) => {
      if (!old) return old;
      return {
        ...old,
        items: old.items.map((it) => (it.id === itemId ? { ...it, reserved: true } : it)),
      };
    });
    try {
      await api.post(`/items/${itemId}/reserve`, {});
      queryClient.invalidateQueries({ queryKey: ["public-wishlist", token] });
    } catch (err) {
      queryClient.setQueryData(["public-wishlist", token], prev);
      setErrorMessage(err instanceof Error ? err.message : "Failed to reserve");
    } finally {
      setReservingItemId(null);
    }
  }

  async function handleUnreserve(itemId: string) {
    if (reservingItemId) return;
    setReservingItemId(itemId);
    setErrorMessage(null);
    const prev = queryClient.getQueryData<WishlistPublic>(["public-wishlist", token]);
    queryClient.setQueryData<WishlistPublic>(["public-wishlist", token], (old) => {
      if (!old) return old;
      return {
        ...old,
        items: old.items.map((it) => (it.id === itemId ? { ...it, reserved: false } : it)),
      };
    });
    try {
      await api.delete(`/items/${itemId}/reserve`);
      queryClient.invalidateQueries({ queryKey: ["public-wishlist", token] });
    } catch (err) {
      queryClient.setQueryData(["public-wishlist", token], prev);
      setErrorMessage(err instanceof Error ? err.message : "Failed to cancel reservation");
    } finally {
      setReservingItemId(null);
    }
  }

  async function handleContribute(itemId: string, amount: number) {
    if (!amount || amount <= 0) return;
    if (contributeSubmittingRef.current) return;
    contributeSubmittingRef.current = true;
    setContributingItemId(itemId);
    setErrorMessage(null);
    const prev = queryClient.getQueryData<WishlistPublic>(["public-wishlist", token]);
    try {
      const res = await api.post<{ contributed_total: string | number; target_price: string | number; progress_percent: number }>(
        `/items/${itemId}/contribute`,
        { amount }
      );
      setContributingItem(null);
      const totalStr = typeof res.contributed_total === "number" ? String(res.contributed_total) : res.contributed_total;
      queryClient.setQueryData<WishlistPublic>(["public-wishlist", token], (old) => {
        if (!old) return old;
        return {
          ...old,
          items: old.items.map((it) =>
            it.id === itemId
              ? { ...it, contributed_total: totalStr, contribution_progress_percent: res.progress_percent }
              : it
          ),
        };
      });
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to contribute");
      queryClient.setQueryData(["public-wishlist", token], prev);
    } finally {
      setContributingItemId(null);
      contributeSubmittingRef.current = false;
    }
  }

  if (isLoading) {
    return <PublicWishlistSkeleton />;
  }

  if (isError || !wishlist) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <p className="text-gray-600">Wishlist not found or the link may be invalid.</p>
        <p className="mt-1 text-sm text-gray-500">{error?.message}</p>
        <Button className="mt-4" variant="secondary" onClick={() => refetch()}>
          Try again
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto min-h-screen max-w-2xl px-4 py-6 sm:py-8">
      {errorMessage && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
          {errorMessage}
          <button type="button" onClick={() => setErrorMessage(null)} className="ml-2 underline focus:outline-none" aria-label="Dismiss">Dismiss</button>
        </div>
      )}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">{wishlist.title}</h1>
        {wishlist.description && (
          <p className="mt-1 text-gray-600">{wishlist.description}</p>
        )}
      </div>

      {wishlist.items.length === 0 ? (
        <EmptyState
          title="No items yet"
          description="The owner hasn’t added any gifts to this list."
        />
      ) : (
        <ul className="space-y-4">
          {wishlist.items.map((item) => (
            <ItemCard
              key={item.id}
              item={item}
              onReserve={() => handleReserve(item.id)}
              onUnreserve={() => handleUnreserve(item.id)}
              onSubmitContribute={(amountStr) => {
                const n = parseFloat(amountStr);
                if (!isNaN(n)) handleContribute(item.id, n);
              }}
              showContributeForm={contributingItem === item.id}
              onOpenContribute={() => setContributingItem(item.id)}
              onCloseContribute={() => setContributingItem(null)}
              isReservePending={reservingItemId === item.id}
              isContributePending={contributingItemId === item.id}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function ItemCard({
  item,
  onReserve,
  onUnreserve,
  onSubmitContribute,
  showContributeForm,
  onOpenContribute,
  onCloseContribute,
  isReservePending,
  isContributePending,
}: {
  item: WishlistItemPublic;
  onReserve: () => void;
  onUnreserve: () => void;
  onSubmitContribute: (amount: string) => void;
  showContributeForm: boolean;
  onOpenContribute: () => void;
  onCloseContribute: () => void;
  isReservePending: boolean;
  isContributePending: boolean;
}) {
  const [amount, setAmount] = useState("");
  const anyPending = isReservePending || isContributePending;

  return (
    <li className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start gap-4">
        {item.image_url && (
          <img
            src={item.image_url}
            alt=""
            className="h-24 w-24 rounded-lg object-cover"
          />
        )}
        <div className="min-w-0 flex-1">
          <h2 className="font-semibold text-gray-900">{item.title}</h2>
          {item.description && (
            <p className="mt-1 text-sm text-gray-500">{item.description}</p>
          )}
          {item.product_url && (
            <a
              href={item.product_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 inline-block text-sm text-primary-600 hover:underline"
            >
              View product
            </a>
          )}
          {item.target_price && parseFloat(item.target_price) > 0 && (
            <p className="mt-1 text-sm text-gray-600">Target: {item.target_price}</p>
          )}
        </div>
      </div>

      {item.reserved && (
        <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Reserved
        </p>
      )}

      {item.allow_group_contribution && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Contributed: {item.contributed_total} / {item.target_price}</span>
            <span className="font-medium">{item.contribution_progress_percent.toFixed(0)}%</span>
          </div>
          <div className="mt-1 h-2 overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full rounded-full bg-primary-500 transition-all"
              style={{ width: `${Math.min(100, item.contribution_progress_percent)}%` }}
            />
          </div>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {!item.reserved && (
          <Button onClick={onReserve} disabled={anyPending} variant="primary">
            {isReservePending ? "Reserving…" : "Reserve"}
          </Button>
        )}
        {item.reserved && (
          <Button onClick={onUnreserve} disabled={anyPending} variant="secondary">
            {isReservePending ? "Cancelling…" : "Cancel reservation"}
          </Button>
        )}
        {item.allow_group_contribution && !showContributeForm && (
          <Button onClick={onOpenContribute} disabled={anyPending} variant="secondary">
            Contribute
          </Button>
        )}
      </div>

      {showContributeForm && item.allow_group_contribution && (
        <div className="mt-4 flex flex-wrap items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 p-3">
          <Input
            type="number"
            min="0.01"
            step="0.01"
            placeholder="Amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-28"
            disabled={isContributePending}
          />
          <Button
            onClick={() => onSubmitContribute(amount)}
            disabled={isContributePending || !amount || parseFloat(amount) <= 0}
          >
            {isContributePending ? "Adding…" : "Add"}
          </Button>
          <Button variant="ghost" onClick={onCloseContribute} disabled={isContributePending}>
            Cancel
          </Button>
        </div>
      )}
    </li>
  );
}
