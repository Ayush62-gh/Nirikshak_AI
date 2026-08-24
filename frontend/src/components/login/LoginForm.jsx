import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { loginUser, registerUser } from "../../services/api";
import {
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  User as UserIcon,
  ShieldCheck,
  ArrowRight,
  AlertCircle,
  Loader2,
} from "lucide-react";

function LoginForm() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName] = useState("");
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
      let res;
      if (isRegister) {
        res = await registerUser(email, password, fullName);
      } else {
        res = await loginUser(email, password);
      }
      login(res.access_token, res.user);
      navigate("/");
    } catch (err) {
      console.error("Auth error:", err);
      setError(
        err.message ||
          (isRegister
            ? "Registration failed. Please check your details."
            : "Invalid credentials. Please check your email and password.")
      );
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsRegister(!isRegister);
    setError(null);
  };

  return (
    <div className="flex min-h-screen flex-1 items-center justify-center bg-white px-6 py-10 sm:px-10 lg:px-14 xl:px-20">

      <div className="w-full max-w-[430px]">

        {/* Small Brand */}
        <div className="mb-8 flex items-center gap-2.5 lg:hidden">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#12988d] text-white">
            <ShieldCheck size={20} />
          </div>

          <p className="text-lg font-bold text-[#173b63]">
            NIRIKSHAK<span className="text-[#12988d]">AI</span>
          </p>
        </div>

        {/* Auth Mode Tabs */}
        <div className="mb-6 flex rounded-xl bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => { setIsRegister(false); setError(null); }}
            className={`flex-1 rounded-lg py-2 text-xs font-bold transition-all ${
              !isRegister
                ? "bg-white text-[#173b63] shadow-xs"
                : "text-[#6680a3] hover:text-[#173b63]"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsRegister(true); setError(null); }}
            className={`flex-1 rounded-lg py-2 text-xs font-bold transition-all ${
              isRegister
                ? "bg-white text-[#12988d] shadow-xs"
                : "text-[#6680a3] hover:text-[#12988d]"
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Heading */}
        <div className="mb-6">
          <p className="mb-1 text-xs font-bold uppercase tracking-wider text-[#12988d]">
            {isRegister ? "New Account" : "Welcome Back"}
          </p>

          <h1 className="text-2xl font-bold tracking-tight text-[#173b63]">
            {isRegister ? "Create your account" : "Sign in to your account"}
          </h1>

          <p className="mt-1.5 text-xs leading-5 text-[#7890ae]">
            {isRegister
              ? "Register to start inspecting package labels with Nirikshak AI."
              : "Access your inspections, reports and compliance insights."}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-800">
            <AlertCircle size={17} className="mt-0.5 shrink-0 text-red-600" />
            <div className="flex-1">
              <p className="font-bold text-red-900">
                {isRegister ? "Registration Error" : "Authentication Error"}
              </p>
              <p className="mt-0.5 leading-relaxed text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>

          {/* Full Name (Sign Up only) */}
          {isRegister && (
            <div className="mb-4">
              <label
                htmlFor="fullName"
                className="mb-1.5 block text-xs font-bold text-[#34445e]"
              >
                Full Name
              </label>

              <div className="relative">
                <UserIcon
                  size={17}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-[#91a3ba]"
                />

                <input
                  id="fullName"
                  type="text"
                  placeholder="Enter your full name"
                  required={isRegister}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="h-11 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-xs text-[#173b63] outline-none transition placeholder:text-[#a8b5c5] focus:border-[#12988d] focus:ring-4 focus:ring-[#12988d]/10"
                />
              </div>
            </div>
          )}

          {/* Email */}
          <div className="mb-4">
            <label
              htmlFor="email"
              className="mb-1.5 block text-xs font-bold text-[#34445e]"
            >
              Email Address
            </label>

            <div className="relative">
              <Mail
                size={17}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-[#91a3ba]"
              />

              <input
                id="email"
                type="email"
                placeholder="Enter your email address"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-xs text-[#173b63] outline-none transition placeholder:text-[#a8b5c5] focus:border-[#12988d] focus:ring-4 focus:ring-[#12988d]/10"
              />
            </div>
          </div>

          {/* Password */}
          <div className="mb-4">
            <div className="mb-1.5 flex items-center justify-between">
              <label
                htmlFor="password"
                className="block text-xs font-bold text-[#34445e]"
              >
                Password
              </label>

              {!isRegister && (
                <button
                  type="button"
                  onClick={() => navigate("/forgot-password")}
                  className="text-xs font-semibold text-[#12988d] transition hover:text-[#0e8178]"
                >
                  Forgot Password?
                </button>
              )}
            </div>

            <div className="relative">
              <LockKeyhole
                size={17}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-[#91a3ba]"
              />

              <input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder={isRegister ? "Create a password" : "Enter your password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-12 text-xs text-[#173b63] outline-none transition placeholder:text-[#a8b5c5] focus:border-[#12988d] focus:ring-4 focus:ring-[#12988d]/10"
              />

              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-lg text-[#91a3ba] transition hover:bg-slate-50 hover:text-[#12988d]"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </div>

          {/* Remember Me (Sign In only) */}
          {!isRegister && (
            <label className="mb-6 flex cursor-pointer items-center gap-2.5">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="h-4 w-4 cursor-pointer accent-[#12988d]"
              />
              <span className="text-xs text-[#6680a3]">Remember me</span>
            </label>
          )}

          {/* Action Button */}
          <button
            type="submit"
            disabled={loading}
            className="group flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-[#12988d] text-xs font-bold text-white shadow-xs transition hover:bg-[#0e8178] hover:shadow-md active:scale-[0.99] disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 size={17} className="animate-spin" />
                <span>{isRegister ? "Creating Account..." : "Signing In..."}</span>
              </>
            ) : (
              <>
                <span>{isRegister ? "Create Account" : "Sign In"}</span>
                <ArrowRight
                  size={16}
                  className="transition-transform duration-200 group-hover:translate-x-1"
                />
              </>
            )}
          </button>
        </form>

        {/* Mode Toggle Footer */}
        <div className="mt-6 text-center text-xs text-[#6680a3]">
          {isRegister ? (
            <p>
              Already have an account?{" "}
              <button
                type="button"
                onClick={toggleMode}
                className="font-bold text-[#12988d] transition hover:underline cursor-pointer"
              >
                Sign In
              </button>
            </p>
          ) : (
            <p>
              Don't have an account?{" "}
              <button
                type="button"
                onClick={toggleMode}
                className="font-bold text-[#12988d] transition hover:underline cursor-pointer"
              >
                Sign Up
              </button>
            </p>
          )}
        </div>

        {/* Security Note */}
        <div className="mt-6 flex items-start gap-2.5 rounded-xl bg-[#f5faf9] px-3.5 py-3">
          <ShieldCheck size={16} className="mt-0.5 shrink-0 text-[#12988d]" />
          <p className="text-[11px] leading-4 text-[#6680a3]">
            Protected with secure JWT authentication and encrypted passwords.
          </p>
        </div>

        {/* Footer */}
        <div className="mt-6 flex items-center justify-between text-[10px] text-[#9aabbe]">
          <span>© 2026 NIRIKSHAK AI</span>
          <span>v1.0.0</span>
        </div>

      </div>

    </div>
  );
}

export default LoginForm;