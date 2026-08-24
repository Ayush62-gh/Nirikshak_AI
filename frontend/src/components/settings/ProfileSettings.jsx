import React from "react";
import { User, Save } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

function ProfileSettings() {
  const { user } = useAuth();

  const fullName = user?.full_name || "Inspector";
  const email = user?.email || "inspector@nirikshak.gov.in";
  const initials = fullName
    ? fullName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "IN";

  return (
    <section className="mb-5 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">

      {/* Header */}
      <div className="px-6 py-4">
        <div className="flex items-center gap-3">

          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
            <User size={20} />
          </div>

          <div>
            <h2 className="text-[17px] font-bold text-[#17233d]">
              Profile Information
            </h2>

            <p className="text-xs text-[#7890ae]">
              Manage your inspector profile details.
            </p>
          </div>

        </div>
      </div>

      {/* Profile Content */}
      <div
        className="border-t border-slate-100 px-6 py-5"
        style={{
          display: "grid",
          gridTemplateColumns: "1.05fr 1.25fr 1.25fr auto",
          gap: "24px",
          alignItems: "end",
        }}
      >

        {/* Inspector */}
        <div className="flex items-center gap-4">

          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-[#173b63] text-lg font-bold text-white">
            {initials}
          </div>

          <div>
            <h3 className="text-base font-bold text-[#17233d]">
              {fullName}
            </h3>

            <p className="mt-1 text-sm text-[#6680a3]">
              Compliance Inspector
            </p>

            <div className="mt-1 flex items-center gap-2 text-xs font-semibold text-emerald-600">
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
              Active
            </div>
          </div>

        </div>

        {/* Full Name */}
        <div>
          <label className="mb-2 block text-sm font-semibold text-[#34445e]">
            Full Name
          </label>

          <input
            type="text"
            key={fullName}
            defaultValue={fullName}
            className="h-11 w-full rounded-lg border border-slate-200 bg-white px-4 text-sm text-[#17233d] outline-none transition focus:border-[#12988d] focus:ring-2 focus:ring-teal-100"
          />
        </div>

        {/* Email */}
        <div>
          <label className="mb-2 block text-sm font-semibold text-[#34445e]">
            Email Address
          </label>

          <input
            type="email"
            key={email}
            defaultValue={email}
            className="h-11 w-full rounded-lg border border-slate-200 bg-white px-4 text-sm text-[#17233d] outline-none transition focus:border-[#12988d] focus:ring-2 focus:ring-teal-100"
          />
        </div>

        {/* Save */}
        <button
          type="button"
          className="flex h-11 items-center justify-center gap-2 rounded-lg bg-[#12988d] px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0e8178]"
        >
          <Save size={17} />
          Save Changes
        </button>

      </div>
    </section>
  );
}

export default ProfileSettings;