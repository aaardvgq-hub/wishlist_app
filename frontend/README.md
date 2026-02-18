# Wishlist Frontend (Next.js 14)

- **Next.js 14** (App Router)
- **TypeScript**, **Tailwind CSS**
- **React Query**, **Zustand**
- **WebSocket** for realtime updates on public wishlist view

## Setup

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local: set NEXT_PUBLIC_API_URL to your API (e.g. http://localhost:8000/api)
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Default redirect is to `/dashboard` (login required).

## Pages

| Route | Description |
|-------|-------------|
| `/login` | Sign in (email + password) |
| `/register` | Create account |
| `/dashboard` | List your wishlists; create new |
| `/wishlist/new` | Create a wishlist (title, description) |
| `/wishlist/[id]/edit` | Edit wishlist, add/remove items |
| `/public/[token]` | Public view by share token (reserve, contribute, realtime) |

## Features

- **Auth**: Login/register with httpOnly cookies; protected routes (middleware + client redirect).
- **Realtime**: Public page subscribes to WebSocket by `wishlist_id`; reserves and contributions refresh automatically.
- **Contribution progress**: Progress bar and totals on items with group contribution.
- **Empty states**: Dashboard and edit show empty state with CTA.
- **Mobile**: Responsive layout with Tailwind.

## Env

- `NEXT_PUBLIC_API_URL` — Base URL for API (e.g. `http://localhost:8000/api`). Required for API and WebSocket base URL derivation.
