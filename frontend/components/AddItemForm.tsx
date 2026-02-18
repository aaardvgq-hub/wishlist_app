"use client";

import { useState } from "react";
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

  async function handleFetchMetadata() {
    const url = productUrl.trim();
    if (!url) return;
    setFetchingMeta(true);
    setError("");
    try {
      const preview = await api.post<ProductPreview>("/items/preview", { product_url: url });
      if (preview.title) setTitle(preview.title);
      if (preview.description) setDescription(preview.description);
      if (preview.image_url) setImageUrl(preview.image_url);
      if (preview.price != null && preview.price !== "") setTargetPrice(String(preview.price));
    } catch {
      setError("Could not fetch metadata from URL");
    } finally {
      setFetchingMeta(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
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
          <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-700">Description (optional)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            placeholder="Or paste product URL and click Fetch metadata"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-700">Product URL (optional)</label>
          <div className="flex gap-2">
            <Input
              type="url"
              value={productUrl}
              onChange={(e) => setProductUrl(e.target.value)}
              placeholder="https://..."
              className="flex-1"
            />
            <Button
              type="button"
              variant="secondary"
              onClick={handleFetchMetadata}
              disabled={!productUrl.trim() || fetchingMeta}
            >
              {fetchingMeta ? "…" : "Fetch metadata"}
            </Button>
          </div>
        </div>
        {imageUrl && (
          <div>
            <label className="mb-1 block text-sm text-gray-700">Image (from page)</label>
            <img src={imageUrl} alt="" className="h-24 rounded-lg object-cover bg-gray-100" />
          </div>
        )}
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
        <Button type="submit" disabled={loading}>{loading ? "Adding…" : "Add"}</Button>
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  );
}
