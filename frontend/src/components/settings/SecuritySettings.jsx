import React, { useState } from "react";
import { Lock, ChevronRight, ShieldCheck } from "lucide-react";

function SecuritySettings() {
  const [twoFactor, setTwoFactor] = useState(false);

  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm">

      {/* Header */}
      <div className="mb-3 flex items-center gap-3">

        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
          <Lock size={19} />
        </div>

        <div>
          <h2 className="text-[17px] font-bold text-[#17233d]">
            Security
          </h2>

          <p className="text-xs text-[#7890ae]">
            Keep your inspector account secure.
          </p>
        </div>

      </div>

      {/* Change Password */}
      <button
        type="button"
        className="flex w-full items-center justify-between gap-4 py-4 text-left transition hover:bg-slate-50"
      >
        <div>
          <p className="text-sm font-semibold text-[#17233d]">
            Change Password
          </p>

          <p className="mt-1 text-xs text-[#7890ae]">
            Update your account password.
          </p>
        </div>

        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-50 text-[#6680a3]">
          <ChevronRight size={18} />
        </div>
      </button>

      {/* Two Factor Authentication */}
      <div className="flex items-center justify-between gap-5 py-4">

        <div>
          <p className="text-sm font-semibold text-[#17233d]">
            Two-Factor Authentication
          </p>

          <p className="mt-1 text-xs leading-5 text-[#7890ae]">
            Add an extra layer of security to your account.
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-3">

          <span
            className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
              twoFactor
                ? "bg-emerald-50 text-emerald-600"
                : "bg-red-50 text-red-500"
            }`}
          >
            {twoFactor ? "Enabled" : "Not Enabled"}
          </span>

          <button
            type="button"
            onClick={() => setTwoFactor(!twoFactor)}
            className={`relative h-6 w-11 shrink-0 rounded-full p-0 transition-colors ${
              twoFactor ? "bg-[#12988d]" : "bg-slate-300"
            }`}
          >
            <span
              className={`absolute top-1 h-4 w-4 rounded-full bg-white shadow transition-all ${
                twoFactor ? "left-6" : "left-1"
              }`}
            />
          </button>

          <ShieldCheck
            size={18}
            className={
              twoFactor
                ? "text-emerald-600"
                : "text-slate-400"
            }
          />

        </div>

      </div>

    </section>
  );
}

export default SecuritySettings;