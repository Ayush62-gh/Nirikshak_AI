import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Loader2 } from "lucide-react";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-900 text-slate-200">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
          <span className="text-sm font-medium text-slate-400">Verifying session...</span>
        </div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" replace />;
}

export default ProtectedRoute;