import React from "react";
import { Info, CheckCircle2, Server, CalendarDays } from "lucide-react";

function SystemInformation() {
  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm">

      {/* Header */}
      <div className="mb-3 flex items-center gap-3">

        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-50 text-purple-600">
          <Info size={19} />
        </div>

        <div>
          <h2 className="text-[17px] font-bold text-[#17233d]">
            System Information
          </h2>

          <p className="text-xs text-[#7890ae]">
            Information about your NIRIKSHAK system.
          </p>
        </div>

      </div>

      {/* Version */}
      <div className="flex items-center justify-between py-4">

        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            <Server size={16} />
          </div>

          <span className="text-sm font-medium text-[#34445e]">
            Version
          </span>
        </div>

        <span className="rounded-md bg-slate-50 px-3 py-1 text-sm font-semibold text-[#17233d]">
          1.0.0
        </span>

      </div>

      {/* Last Updated */}
      <div className="flex items-center justify-between py-4">

        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-50 text-orange-500">
            <CalendarDays size={16} />
          </div>

          <span className="text-sm font-medium text-[#34445e]">
            Last Updated
          </span>
        </div>

        <span className="text-sm font-semibold text-[#17233d]">
          Aug 20, 2026
        </span>

      </div>

      {/* System Status */}
      <div className="flex items-center justify-between py-4">

        <div className="flex items-center gap-3">

          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
            <CheckCircle2 size={16} />
          </div>

          <span className="text-sm font-medium text-[#34445e]">
            System Status
          </span>

        </div>

        <span className="flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-600">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          Operational
        </span>

      </div>

    </section>
  );
}

export default SystemInformation;