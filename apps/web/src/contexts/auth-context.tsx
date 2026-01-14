"use client";

/**
 * Authentication Context
 *
 * Manages authentication state across the application.
 */

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import { api } from "@/lib/api";
import type { User, LoginRequest, LoginResponse, AuthState } from "@/types/auth";

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<{ error?: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  const setUser = (user: User | null) => {
    setState({
      user,
      isAuthenticated: !!user,
      isLoading: false,
    });
  };

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setState({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }

    const response = await api.get<User>("/auth/me");
    if (response.data) {
      setUser(response.data);
    } else {
      // Token invalid, clear storage
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      setUser(null);
    }
  }, []);

  // Check auth once on mount
  useEffect(() => {
    let isMounted = true;

    const initAuth = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (!token) {
        setState((prev) => ({ ...prev, isLoading: false }));
        return;
      }

      try {
        const response = await api.get<User>("/auth/me");
        if (isMounted) {
          if (response.data) {
            setUser(response.data);
          } else {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            setUser(null);
          }
        }
      } catch {
        if (isMounted) setUser(null);
      }
    };

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []); // Run only once on mount

  const login = async (credentials: LoginRequest): Promise<{ error?: string }> => {
    const response = await api.post<LoginResponse>("/auth/login", credentials);

    if (response.error) {
      return { error: response.error };
    }

    if (response.data) {
      localStorage.setItem(TOKEN_KEY, response.data.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refresh_token);
      setUser(response.data.user);
    }

    return {};
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
