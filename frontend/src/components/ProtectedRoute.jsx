import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import LoadingSpinner from "./LoadingSpinner";

/**
 * Route guard that relies on server-verified auth state (via /me).
 *
 * States:
 *  loading === true  → show spinner (initial /me fetch in progress)
 *  user === false    → redirect to /login
 *  user === object   → render children
 */
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
