"use client";

import { useState, useCallback } from "react";
import { useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

type ProductPreview = {
  title?: string | null;
  image_url?: string | null;
  description?: string | null;
  price?: string | number | null;
  preview_quality?: string;
  missing_fields?: string[];
};

const DEBOUNCE_MS = 800;
const PREVIEW_REQUEST_TIMEOUT_MS = 8000;

export function AddItemForm({
  wishlistId,
  onSuccess,
  onCancel,
}: {
  wishlistId: string;
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [productUrl, setProductUrl] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [allowGroup, setAllowGroup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetchingMeta, setFetchingMeta] = useState(false);
  const [error, setError] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchMetadata = useCallback(async (url: string) => {
    if (!url.trim()) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setFetchingMeta(true);
    setError("");
    const timeoutId = setTimeout(() => controller.abort(), PREVIEW_REQUEST_TIMEOUT_MS);
    try {
      const base = process.env.NEXT_PUBLIC_API_URL ?? "";
      const path = `/link-preview?url=${encodeURIComponent(url.trim())}`;
      const res = await fetch(`${path.startsWith("http") ? path : base + path}`, {
        signal: controller.signal,
        credentials: "include",
        headers: { "Content-Type": "application/json", ...(typeof window !== "undefined" && sessionStorage.getItem("access_token") ? { Authorization: `Bearer ${sessionStorage.getItem("access_token")}` } : {}) },
      });
      clearTimeout(timeoutId);
      if (!res.ok) throw new Error("Preview failed");
      const preview = (await res.json()) as ProductPreview;
      if (preview.description != null) setDescription(preview.description);
      if (preview.image_url != null) setImageUrl(preview.image_url);
      if (preview.price != null && preview.price !== "") setTargetPrice(String(preview.price));
      if (!preview.image_url) setError("");
    } catch (e) {
      if (abortRef.current !== controller) return; // отменён из-за смены URL
      if ((e as { name?: string })?.name === "AbortError") {
        setError("Preview timed out. You can still add the item.");
      } else {
        setError("Could not load link preview. Check the URL.");
      }
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      setFetchingMeta(false);
    }
  }, []);

  useEffect(() => {
    const url = productUrl.trim();
    if (!url) {
      setDescription("");
      setImageUrl("");
      setError("");
      setTargetPrice("");
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchMetadata(url), DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [productUrl, fetchMetadata]);

  const canSubmit = title.trim() !== "" && productUrl.trim() !== "" && targetPrice.trim() !== "" && !loading && !fetchingMeta;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!title.trim() || !productUrl.trim() || !targetPrice.trim()) {
      setError("Fill in Title, Product URL and Target price.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/items/", {
        wishlist_id: wishlistId,
        title: title.trim(),
        description: description.trim() || null,
        product_url: productUrl.trim() || null,
        image_url: imageUrl.trim() || null,
        target_price: targetPrice.trim() || "0",
        allow_group_contribution: allowGroup,
      });
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className="font-semibold text-gray-900">Add item</h3>
      <div className="mt-3 space-y-3">
        <div>
          <label className="mb-1 block text-sm text-gray-700">Title</label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="Your own title for this item" />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-700">Product URL (required)</label>
          <Input
            type="url"
            value={productUrl}
            onChange={(e) => setProductUrl(e.target.value)}
            placeholder="https://..."
            required
          />
          {fetchingMeta && <p className="mt-1 text-xs text-gray-500">Loading preview…</p>}
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-700">Description (from page meta)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            readOnly
            className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-700"
            placeholder="Filled automatically from the link"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-700">Preview image (from link)</label>
          {imageUrl ? (
            <img src={imageUrl} alt="" className="h-32 w-full rounded-lg object-contain bg-gray-100" />
          ) : (
            <div className="flex h-32 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-gray-50 text-sm text-gray-500">
              {fetchingMeta ? "Loading preview…" : productUrl.trim() ? "No image on page" : "Enter product URL above"}
            </div>
          )}
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-700">Target price (required)</label>
          <Input
            type="text"
            inputMode="decimal"
            value={targetPrice}
            onChange={(e) => setTargetPrice(e.target.value)}
            placeholder="0"
            required
          />
        </div>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={allowGroup}
            onChange={(e) => setAllowGroup(e.target.checked)}
            className="rounded border-gray-300"
          />
          <span className="text-sm text-gray-700">Allow group contribution</span>
        </label>
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <div className="mt-4 flex gap-2">
        <Button type="submit" disabled={!canSubmit}>
          {loading ? "Adding…" : "Add"}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  );
}
