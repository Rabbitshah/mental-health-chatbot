/**
 * AuthContext — server-authoritative authentication state.
 *
 * Auth truth comes from the /me endpoint (cookie-based). We never trust
 * localStorage flags for route protection; localStorage is only used to
 * cache the user profile object for instant renders.
 */
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import API from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // null  = still loading (checking with server)
  // false = confirmed logged-out
  // object = confirmed logged-in user object
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const res = await API.get("/me");
      setUser(res.data);
      localStorage.setItem("user", JSON.stringify(res.data));
    } catch {
      setUser(false);
      localStorage.removeItem("user");
      localStorage.removeItem("isLoggedIn");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = useCallback((userData) => {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
  }, []);

  const logout = useCallback(async () => {
    try {
      await API.post("/logout");
    } catch {
      // Proceed with local cleanup even if the server call fails
    }
    setUser(false);
    localStorage.removeItem("user");
    localStorage.removeItem("isLoggedIn");
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refetch: fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
