import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const publicPaths = ["/login", "/register", "/public"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (publicPaths.some((p) => pathname.startsWith(p))) return NextResponse.next();
  // Protected routes: auth is checked client-side via api.get("/auth/me") with Bearer token from sessionStorage.
  // Middleware runs on server and has no access to sessionStorage, so we cannot pass the token here.
  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/dashboard", "/wishlist/:path*"],
};
// Note: /wishlist/new is protected (user must be logged in to create). /public/:token is public.
