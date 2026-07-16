import { useCallback, useEffect, useState } from "react";
import { authApi } from "../services/authApi";
import { AuthContext } from "./authContext";

const TOKEN_KEY = "autodev_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  // Only a persisted token needs validating on mount; no token means nothing to load.
  const [loading, setLoading] = useState(() => !!localStorage.getItem(TOKEN_KEY));

  useEffect(() => {
    if (!token) {
      return;
    }
    authApi
      .me(token)
      .then(setUser)
      .catch(() => {
        // Stored token is expired/invalid — clear it so protected routes redirect to login.
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const register = useCallback(async (email, password) => {
    const { token: newToken } = await authApi.register(email, password);
    // Resolve the user BEFORE returning — isAuthenticated needs both token
    // and user, so setting only the token here would leave a brief window
    // where ProtectedRoute sees isAuthenticated=false and bounces back to
    // /login right after a successful register/login.
    const newUser = await authApi.me(newToken);
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
    setUser(newUser);
  }, []);

  const login = useCallback(async (email, password) => {
    const { token: newToken } = await authApi.login(email, password);
    const newUser = await authApi.me(newToken);
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
    setUser(newUser);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = {
    token,
    user,
    loading,
    isAuthenticated: !!token && !!user,
    register,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
