import React from "react";
import { ShieldCheck, FileCheck2, TrendingUp } from "lucide-react";
import InspectionVisual from "./InspectionVisual";

function LoginBrandPanel() {
  return (
    <div className="relative hidden min-h-screen overflow-hidden bg-[#f0f8f7] lg:flex lg:w-[52%] lg:flex-col lg:justify-between">

      {/* Soft background accents */}
      <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-[#12988d]/10 blur-3xl" />

      <div className="pointer-events-none absolute -bottom-32 -right-20 h-80 w-80 rounded-full bg-[#173b63]/10 blur-3xl" />

      {/* Branding */}
      <div className="relative z-10 px-12 pt-12 xl:px-16">

        <div className="flex items-center gap-3">

          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#12988d] text-white shadow-sm">
            <ShieldCheck size={24} />
          </div>

          <div>
            <h1 className="text-xl font-bold tracking-tight text-[#173b63]">
              NIRIKSHAK<span className="text-[#12988d]">AI</span>
            </h1>

            <p className="text-[11px] font-medium tracking-wide text-[#6680a3]">
              SMART COMPLIANCE. FAIR TRADE.
            </p>
          </div>

        </div>

        <div className="mt-14 max-w-xl">

          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-[#12988d]">
            Intelligent Inspection Platform
          </p>

          <h2 className="text-4xl font-bold leading-tight tracking-tight text-[#173b63] xl:text-5xl">
            Inspect smarter.
            <br />
            <span className="text-[#12988d]">Comply better.</span>
          </h2>

          <p className="mt-5 max-w-lg text-[15px] leading-7 text-[#6680a3]">
            Simplify inspections, identify compliance issues, and generate
            reliable reports with one intelligent platform.
          </p>

        </div>

      </div>

      {/* Visual */}
      <div className="relative z-10 mt-8 flex flex-1 items-center justify-center px-8 xl:px-14">
        <InspectionVisual />
      </div>

      {/* Bottom features */}
      <div className="relative z-10 grid grid-cols-3 gap-4 px-12 pb-10 xl:px-16">

        <Feature
          icon={<FileCheck2 size={17} />}
          title="Smart Reports"
        />

        <Feature
          icon={<ShieldCheck size={17} />}
          title="Compliance Ready"
        />

        <Feature
          icon={<TrendingUp size={17} />}
          title="Clear Insights"
        />

      </div>

    </div>
  );
}

function Feature({ icon, title }) {
  return (
    <div className="flex items-center gap-2.5 text-[#6680a3]">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-[#12988d] shadow-sm">
        {icon}
      </div>

      <span className="text-xs font-semibold">
        {title}
      </span>
    </div>
  );
}

export default LoginBrandPanel;