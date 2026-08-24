import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { loginUser } from "../../services/api";
import {
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
  ArrowRight,
  AlertCircle,
  Loader2,
} from "lucide-react";

function LoginForm() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const res = await loginUser(email, password);
      login(res.access_token, res.user);
      navigate("/");
    } catch (err) {
      console.error("Login error:", err);
      setError(err.message || "Invalid credentials. Please check your email and password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-1 items-center justify-center bg-white px-6 py-10 sm:px-10 lg:px-14 xl:px-20">

      <div className="w-full max-w-[430px]">

        {/* Small Brand */}
        <div className="mb-10 flex items-center gap-2.5 lg:hidden">

          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#12988d] text-white">
            <ShieldCheck size={20} />
          </div>

          <p className="text-lg font-bold text-[#173b63]">
            NIRIKSHAK<span className="text-[#12988d]">AI</span>
          </p>

        </div>

        {/* Heading */}
        <div className="mb-8">

          <p className="mb-2 text-sm font-semibold text-[#12988d]">
            Welcome back
          </p>

          <h1 className="text-3xl font-bold tracking-tight text-[#173b63]">
            Sign in to your account
          </h1>

          <p className="mt-2.5 text-sm leading-6 text-[#7890ae]">
            Access your inspections, reports and compliance insights.
          </p>

        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            <AlertCircle size={18} className="mt-0.5 shrink-0 text-red-600" />
            <div className="flex-1">
              <p className="font-semibold text-red-900">Authentication Error</p>
              <p className="mt-0.5 text-xs text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>

          {/* Email */}
          <div className="mb-5">

            <label
              htmlFor="email"
              className="mb-2 block text-sm font-semibold text-[#34445e]"
            >
              Email Address
            </label>

            <div className="relative">

              <Mail
                size={18}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-[#91a3ba]"
              />

              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-sm text-[#173b63] outline-none transition placeholder:text-[#a8b5c5] focus:border-[#12988d] focus:ring-4 focus:ring-[#12988d]/10"
              />

            </div>

          </div>

          {/* Password */}
          <div className="mb-4">

            <div className="mb-2 flex items-center justify-between">

              <label
                htmlFor="password"
                className="block text-sm font-semibold text-[#34445e]"
              >
                Password
              </label>

              <button
              type="button"
              onClick={() => navigate("/forgot-password")}
              className="text-xs font-semibold text-[#12988d] transition hover:text-[#0e8178]"
              >
               Forgot Password?
              </button>

            </div>

            <div className="relative">

              <LockKeyhole
                size={18}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-[#91a3ba]"
              />

              <input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-12 text-sm text-[#173b63] outline-none transition placeholder:text-[#a8b5c5] focus:border-[#12988d] focus:ring-4 focus:ring-[#12988d]/10"
              />

              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-lg text-[#91a3ba] transition hover:bg-slate-50 hover:text-[#12988d]"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff size={18} />
                ) : (
                  <Eye size={18} />
                )}
              </button>

            </div>

          </div>

          {/* Remember Me */}
          <label className="mb-7 flex cursor-pointer items-center gap-2.5">

            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 cursor-pointer accent-[#12988d]"
            />

            <span className="text-sm text-[#6680a3]">
              Remember me
            </span>

          </label>

          {/* Sign In */}
          <button
            type="submit"
            disabled={loading}
            className="group flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#12988d] text-sm font-semibold text-white shadow-sm transition hover:bg-[#0e8178] hover:shadow-md active:scale-[0.99] disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Signing In...</span>
              </>
            ) : (
              <>
                <span>Sign In</span>
                <ArrowRight
                  size={17}
                  className="transition-transform duration-200 group-hover:translate-x-1"
                />
              </>
            )}
          </button>

          {/* Divider */}
          <div className="my-7 flex items-center gap-4">

            <div className="h-px flex-1 bg-slate-100" />

            <span className="text-xs text-[#a0aec0]">
              or
            </span>

            <div className="h-px flex-1 bg-slate-100" />

          </div>

          {/* SSO */}
          <button
            type="button"
            className="flex h-12 w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white text-sm font-semibold text-[#34445e] transition hover:border-[#12988d]/40 hover:bg-[#f7fbfa]"
          >
            <ShieldCheck size={18} className="text-[#12988d]" />
            Continue with SSO
          </button>

        </form>

        {/* Security note */}
        <div className="mt-8 flex items-start gap-3 rounded-xl bg-[#f5faf9] px-4 py-3.5">

          <ShieldCheck
            size={17}
            className="mt-0.5 shrink-0 text-[#12988d]"
          />

          <p className="text-[11px] leading-5 text-[#6680a3]">
            Your account information is protected with secure
            authentication.
          </p>

        </div>

        {/* Footer */}
        <div className="mt-8 flex items-center justify-between text-[10px] text-[#9aabbe]">
          <span>© 2026 NIRIKSHAK AI</span>

          <span>v1.0.0</span>
        </div>

      </div>

    </div>
  );
}

export default LoginForm;