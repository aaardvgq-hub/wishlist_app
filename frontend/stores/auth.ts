import { create } from "zustand";
import type { User } from "@/lib/types";
import { api, clearAccessToken } from "@/lib/api";

interface AuthState {
  user: User | null;
  setUser: (u: User | null) => void;
  fetchUser: () => Promise<User | null>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  fetchUser: async () => {
    try {
      const user = await api.get<User>("/auth/me");
      set({ user });
      return user;
    } catch {
      set({ user: null });
      return null;
    }
  },
  logout: async () => {
    try {
      await api.post("/auth/logout");
    } finally {
      clearAccessToken();
      set({ user: null });
    }
  },
}));
