"use client";

import { useState } from "react";
import type { WishItem } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { EditItemForm } from "@/components/EditItemForm";

export function ItemDetailModal({
  item,
  onClose,
  onSaved,
  onDelete,
}: {
  item: WishItem;
  onClose: () => void;
  onSaved: () => void;
  onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);

  function handleSaved() {
    onSaved();
    setEditing(false);
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-modal="true"
      aria-labelledby="item-modal-title"
    >
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
          <h2 id="item-modal-title" className="text-lg font-semibold text-gray-900">
            {editing ? "Edit item" : item.title}
          </h2>
          <div className="flex gap-2">
            {!editing && (
              <>
                <Button variant="secondary" onClick={() => setEditing(true)}>
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  className="text-red-600 hover:bg-red-50"
                  onClick={() => {
                    if (confirm("Remove this item?")) onDelete();
                  }}
                >
                  Remove
                </Button>
              </>
            )}
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
        <div className="p-4">
          {editing ? (
            <EditItemForm
              item={item}
              onSuccess={handleSaved}
              onCancel={() => setEditing(false)}
            />
          ) : (
            <div className="space-y-3">
              {item.description && (
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{item.description}</p>
              )}
              {item.product_url && (
                <p className="text-sm">
                  <span className="text-gray-500">Link: </span>
                  <a
                    href={item.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:underline break-all"
                  >
                    {item.product_url}
                  </a>
                </p>
              )}
              {item.image_url && (
                <img
                  src={item.image_url}
                  alt=""
                  className="max-h-48 rounded-lg object-contain bg-gray-100"
                />
              )}
              {item.target_price && item.target_price !== "0" && (
                <p className="text-sm text-gray-600">Target price: {item.target_price}</p>
              )}
              {item.allow_group_contribution && (
                <p className="text-sm text-gray-500">Allows group contribution</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
