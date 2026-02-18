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

  const fetchMetadata = useCallback(async (url: string) => {
    if (!url.trim()) return;
    setFetchingMeta(true);
    setError("");
    try {
      const preview = await api.post<ProductPreview>("/items/preview", { product_url: url.trim() });
      if (preview.description != null) setDescription(preview.description);
      if (preview.image_url != null) setImageUrl(preview.image_url);
      if (preview.price != null && preview.price !== "") setTargetPrice(String(preview.price));
      if (!preview.image_url) setError("No preview image on this page. Use a product link with an image (e.g. shop or Telegram preview).");
    } catch {
      setError("Could not load page metadata. Check the URL.");
    } finally {
      setFetchingMeta(false);
    }
  }, []);

  useEffect(() => {
    const url = productUrl.trim();
    if (!url) {
      setDescription("");
      setImageUrl("");
      setError("");
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchMetadata(url), DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [productUrl, fetchMetadata]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!imageUrl.trim()) {
      setError("Preview image is required. Enter a product URL and wait for the image to load.");
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
          <label className="mb-1 block text-sm text-gray-700">Product URL (required for preview)</label>
          <Input
            type="url"
            value={productUrl}
            onChange={(e) => setProductUrl(e.target.value)}
            placeholder="https://..."
            required
          />
          {fetchingMeta && <p className="mt-1 text-xs text-gray-500">Loading description and image…</p>}
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
          <label className="mb-1 block text-sm text-gray-700">Preview image (required)</label>
          {imageUrl ? (
            <img src={imageUrl} alt="" className="h-32 w-full rounded-lg object-contain bg-gray-100" />
          ) : (
            <div className="flex h-32 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-gray-50 text-sm text-gray-500">
              {productUrl.trim() ? "Loading or no image on page…" : "Enter product URL above"}
            </div>
          )}
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-700">Target price (optional)</label>
          <Input
            type="text"
            inputMode="decimal"
            value={targetPrice}
            onChange={(e) => setTargetPrice(e.target.value)}
            placeholder="0"
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
        <Button type="submit" disabled={loading || !imageUrl.trim() || fetchingMeta}>
          {loading ? "Adding…" : "Add"}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  );
}
