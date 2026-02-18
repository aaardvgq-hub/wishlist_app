export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Wishlist {
  id: string;
  owner_id: string;
  share_token: string;
  title: string;
  description: string | null;
  event_date: string | null;
  is_public: boolean;
  created_at: string;
}

export interface WishlistWithItems extends Wishlist {
  items: WishItem[];
}

export interface WishItem {
  id: string;
  wishlist_id: string;
  title: string;
  description: string | null;
  product_url: string | null;
  image_url: string | null;
  target_price: string;
  allow_group_contribution: boolean;
  is_deleted?: boolean;
}

export interface WishlistItemPublic extends WishItem {
  reserved: boolean;
  contributed_total: string;
  contribution_progress_percent: number;
}

export interface WishlistPublic {
  id: string;
  share_token: string;
  title: string;
  description: string | null;
  event_date: string | null;
  is_public: boolean;
  event_date_passed?: boolean;
  items: WishlistItemPublic[];
}
