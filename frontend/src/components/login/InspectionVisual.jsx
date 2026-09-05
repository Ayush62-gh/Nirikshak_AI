import React from "react";
import {
  CheckCircle2,
  AlertTriangle,
  FileText,
  ScanLine,
  TrendingUp,
} from "lucide-react";

function InspectionVisual() {
  return (
    <div className="relative h-[310px] w-full max-w-[500px]">

      {/* Decorative dots */}
      <div className="absolute left-8 top-10 h-2 w-2 rounded-full bg-[#12988d]/40" />
      <div className="absolute right-12 top-20 h-1.5 w-1.5 rounded-full bg-[#173b63]/30" />
      <div className="absolute bottom-12 left-20 h-1.5 w-1.5 rounded-full bg-[#12988d]/30" />

      {/* Main inspection card */}
      <div className="absolute left-[8%] top-[7%] w-[72%] rounded-2xl border border-white bg-white p-5 shadow-[0_18px_45px_rgba(23,59,99,0.10)] transition-transform duration-500 hover:-translate-y-1">

        {/* Card header */}
        <div className="flex items-center justify-between">

          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#eef8f6] text-[#12988d]">
              <FileText size={20} />
            </div>

            <div>
              <p className="text-sm font-bold text-[#173b63]">
                Inspection Report
              </p>

              <p className="mt-0.5 text-[11px] text-[#7890ae]">
                Recent inspection analysis
              </p>
            </div>
          </div>

          <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-semibold text-emerald-600">
            Completed
          </span>

        </div>

        {/* Score */}
        <div className="mt-6 flex items-center gap-5">

          <div className="relative flex h-24 w-24 items-center justify-center">

            <svg
              className="absolute inset-0 h-full w-full -rotate-90"
              viewBox="0 0 100 100"
            >
              <circle
                cx="50"
                cy="50"
                r="42"
                fill="none"
                stroke="#e8f1f3"
                strokeWidth="8"
              />

              <circle
                cx="50"
                cy="50"
                r="42"
                fill="none"
                stroke="#12988d"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray="264"
                strokeDashoffset="21"
              />
            </svg>

            <div className="text-center">
              <p className="text-xl font-bold text-[#173b63]">
                92%
              </p>

              <p className="text-[9px] font-medium text-[#7890ae]">
                Compliance
              </p>
            </div>

          </div>

          <div className="flex-1">

            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs text-[#7890ae]">
                Compliance Score
              </span>

              <span className="text-xs font-bold text-[#12988d]">
                Excellent
              </span>
            </div>

            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full w-[92%] rounded-full bg-[#12988d]" />
            </div>

            <div className="mt-4 flex items-center gap-2">
              <CheckCircle2
                size={15}
                className="text-emerald-500"
              />

              <span className="text-[11px] text-[#6680a3]">
                All critical checks completed
              </span>
            </div>

          </div>

        </div>

        {/* Mini stats */}
        <div className="mt-6 grid grid-cols-3 gap-2">

          <MiniStat
            label="Checks"
            value="24"
          />

          <MiniStat
            label="Passed"
            value="22"
          />

          <MiniStat
            label="Issues"
            value="02"
            warning
          />

        </div>

      </div>

      {/* Floating issue card */}
      <div className="absolute bottom-[7%] right-[2%] w-[210px] animate-[float_4s_ease-in-out_infinite] rounded-xl border border-white bg-white p-4 shadow-[0_15px_35px_rgba(23,59,99,0.12)]">

        <div className="flex items-center justify-between">

          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-500">
              <AlertTriangle size={16} />
            </div>

            <div>
              <p className="text-[11px] font-bold text-[#173b63]">
                Issues Found
              </p>

              <p className="text-[9px] text-[#7890ae]">
                Needs attention
              </p>
            </div>
          </div>

          <span className="text-lg font-bold text-amber-500">
            02
          </span>

        </div>

        <div className="mt-3 flex items-center gap-2">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full w-[35%] rounded-full bg-amber-400" />
          </div>

          <span className="text-[9px] font-semibold text-[#7890ae]">
            Review
          </span>
        </div>

      </div>

      {/* Floating scan badge */}
      <div className="absolute right-[13%] top-[2%] flex animate-[float_5s_ease-in-out_infinite] items-center gap-2 rounded-full border border-white bg-white px-3 py-2 shadow-[0_10px_25px_rgba(23,59,99,0.10)]">
        <ScanLine size={14} className="text-[#12988d]" />

        <span className="text-[10px] font-semibold text-[#173b63]">
          AI Analysis
        </span>

        <span className="h-1.5 w-1.5 rounded-full bg-[#12988d]" />
      </div>

      {/* Floating trend badge */}
      <div className="absolute bottom-[12%] left-[1%] flex items-center gap-2 rounded-xl border border-white bg-white px-3 py-2.5 shadow-[0_10px_25px_rgba(23,59,99,0.08)]">
        <TrendingUp size={15} className="text-[#12988d]" />

        <div>
          <p className="text-[9px] text-[#7890ae]">
            Compliance trend
          </p>

          <p className="text-xs font-bold text-[#173b63]">
            +12.4%
          </p>
        </div>
      </div>

      {/* Animation */}
      <style>
        {`
          @keyframes float {
            0%, 100% {
              transform: translateY(0px);
            }
            50% {
              transform: translateY(-7px);
            }
          }
        `}
      </style>

    </div>
  );
}

function MiniStat({ label, value, warning = false }) {
  return (
    <div className="rounded-lg bg-[#f7fafb] px-3 py-2.5">
      <p className="text-[9px] text-[#7890ae]">
        {label}
      </p>

      <p
        className={`mt-0.5 text-sm font-bold ${
          warning ? "text-amber-500" : "text-[#173b63]"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

export default InspectionVisual;