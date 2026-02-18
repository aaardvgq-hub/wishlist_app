const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export const ACCESS_TOKEN_KEY = "access_token";

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  if (typeof window !== "undefined") sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  if (typeof window !== "undefined") sessionStorage.removeItem(ACCESS_TOKEN_KEY);
}

type RequestInitWithCredentials = RequestInit & { credentials?: RequestCredentials };

function parseApiError(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (first && typeof first === "object" && "msg" in first && typeof (first as { msg: unknown }).msg === "string") {
      return (first as { msg: string }).msg;
    }
  }
  return "Request failed";
}

async function request<T>(
  path: string,
  options: RequestInitWithCredentials = {}
): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      credentials: "include",
      headers,
    });
  } catch (e) {
    const msg = e instanceof TypeError && e.message === "Failed to fetch"
      ? "Network error. API unreachable — check backend is up and NEXT_PUBLIC_API_URL."
      : e instanceof Error ? e.message : "Request failed";
    throw new Error(msg);
  }
  if (res.status === 401) clearAccessToken();
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = (body as { detail?: unknown }).detail ?? res.statusText;
    throw new Error(parseApiError(detail));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: "DELETE" }),
};

export default api;
