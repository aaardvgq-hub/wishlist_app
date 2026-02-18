import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const publicPaths = ["/login", "/register", "/public"];
const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (publicPaths.some((p) => pathname.startsWith(p))) return NextResponse.next();

  if (pathname === "/" || pathname === "/dashboard" || pathname.startsWith("/wishlist/")) {
    try {
      const res = await fetch(`${apiBase}/auth/me`, {
        credentials: "include",
        headers: request.headers.get("cookie") ? { cookie: request.headers.get("cookie")! } : {},
      });
      if (!res.ok) return NextResponse.redirect(new URL("/login", request.url));
    } catch {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/dashboard", "/wishlist/:path*"],
};
// Note: /wishlist/new is protected (user must be logged in to create). /public/:token is public.
