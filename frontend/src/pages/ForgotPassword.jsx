import React, { useState } from "react";
import { Mail, ShieldCheck, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

function ForgotPassword() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    // Backend reset-password API yahan connect hogi
    console.log("Password reset requested for:", email);
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] px-6 py-10">

      <div className="mx-auto flex min-h-[calc(100vh-80px)] max-w-6xl items-center justify-center">

        {/* Card */}
        <div className="w-full max-w-[520px] rounded-3xl border border-white bg-white p-8 shadow-[0_20px_60px_rgba(18,59,99,0.08)] sm:p-10">

          {/* Brand */}
          <div className="mb-10 flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#12988d] text-white">
              <ShieldCheck size={24} />
            </div>

            <div>
              <p className="text-xl font-bold text-[#173b63]">
                NIRIKSHAK<span className="text-[#12988d]">AI</span>
              </p>

              <p className="text-[10px] uppercase tracking-wide text-[#7890ae]">
                Smart Compliance. Fair Trade.
              </p>
            </div>

          </div>

          {/* Heading */}
          <div className="mb-8">

            <h1 className="text-3xl font-bold tracking-tight text-[#173b63]">
              Forgot Password?
            </h1>

            <p className="mt-3 text-sm leading-6 text-[#7890ae]">
              No worries. Enter your registered email address and we'll
              send you a link to reset your password.
            </p>

          </div>

          {/* Form */}
          <form onSubmit={handleSubmit}>

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
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email address"
                required
                className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-sm text-[#173b63] outline-none transition placeholder:text-[#a8b5c5] focus:border-[#12988d] focus:ring-4 focus:ring-[#12988d]/10"
              />

            </div>

            {/* Submit */}
            <button
              type="submit"
              className="mt-6 flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#12988d] text-sm font-semibold text-white shadow-sm transition hover:bg-[#0e8178] hover:shadow-md active:scale-[0.99]"
            >
              Send Reset Link
            </button>

          </form>

          {/* Back to Login */}
          <button
            type="button"
            onClick={() => navigate("/login")}
            className="mx-auto mt-7 flex items-center gap-2 text-sm font-semibold text-[#12988d] transition hover:text-[#0e8178]"
          >
            <ArrowLeft size={17} />
            Back to Login
          </button>

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

        </div>

      </div>

    </div>
  );
}

export default ForgotPassword;