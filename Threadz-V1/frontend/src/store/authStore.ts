import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'user' | 'admin';
  avatar?: string;
  createdAt: Date;
}

interface AuthStore {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      isLoading: false,
      
      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          // Mock API call - replace with real API
          const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
          });
          
          if (response.ok) {
            const data = await response.json();
            const user: User = {
              id: data.user.user_id,
              email: data.user.email,
              name: data.user.full_name,
              role: data.user.role, // Use the role from API response
              createdAt: new Date(),
            };
            set({ user, isLoading: false });
          } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Login failed');
          }
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      signup: async (email: string, password: string, name: string) => {
        set({ isLoading: true });
        try {
          // Mock API call - replace with real API
          const response = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, full_name: name }),
          });
          
          if (response.ok) {
            const data = await response.json();
            const user: User = {
              id: data.user_id,
              email,
              name,
              role: 'user', // Default role for signup
              createdAt: new Date(),
            };
            set({ user, isLoading: false });
          } else {
            throw new Error('Signup failed');
          }
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        set({ user: null, isLoading: false });
        // Clear any persisted data by forcing a fresh state
        localStorage.removeItem('auth-store');
      },

      get isAdmin() {
        return get().user?.role === 'admin';
      },
    }),
    {
      name: 'auth-store',
    }
  )
);
