import React, { useState } from "react";
import { SlidersHorizontal } from "lucide-react";

function InspectionSettings() {
  const [autoSave, setAutoSave] = useState(true);
  const [threshold, setThreshold] = useState("80%");

  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm">

      {/* Header */}
      <div className="mb-3 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-50 text-[#12988d]">
          <SlidersHorizontal size={19} />
        </div>

        <div>
          <h2 className="text-[17px] font-bold text-[#17233d]">
            Inspection Preferences
          </h2>

          <p className="text-xs text-[#7890ae]">
            Customize how inspections are handled.
          </p>
        </div>
      </div>

      {/* Auto Save */}
      <div className="flex items-center justify-between gap-5  py-4">
        <div>
          <p className="text-sm font-semibold text-[#17233d]">
            Auto-save Inspections
          </p>

          <p className="mt-1 text-xs leading-5 text-[#7890ae]">
            Automatically save your inspection progress.
          </p>
        </div>

        {/* Toggle */}
        <div
          onClick={() => setAutoSave(!autoSave)}
          role="switch"
          aria-checked={autoSave}
          style={{
            width: "44px",
            height: "24px",
            minWidth: "44px",
            backgroundColor: autoSave ? "#12988d" : "#cbd5e1",
            borderRadius: "9999px",
            position: "relative",
            cursor: "pointer",
            flexShrink: 0,
            transition: "background-color 0.2s ease",
          }}
        >
          <span
            style={{
              position: "absolute",
              top: "4px",
              left: autoSave ? "24px" : "4px",
              width: "16px",
              height: "16px",
              backgroundColor: "#ffffff",
              borderRadius: "50%",
              boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
              transition: "left 0.2s ease",
            }}
          />
        </div>
      </div>

      {/* Compliance Threshold */}
      <div className="flex items-center justify-between gap-5  py-4">
        <div>
          <p className="text-sm font-semibold text-[#17233d]">
            Default Compliance Threshold
          </p>

          <p className="mt-1 text-xs leading-5 text-[#7890ae]">
            Set the minimum score required for compliance.
          </p>
        </div>

        <select
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
          className="h-10 w-24 rounded-lg bg-white px-3 text-sm font-semibold text-[#34445e] outline-none focus:border-[#12988d] focus:ring-2 focus:ring-teal-100"
        >
          <option>70%</option>
          <option>75%</option>
          <option>80%</option>
          <option>85%</option>
          <option>90%</option>
          <option>95%</option>
        </select>
      </div>

    </section>
  );
}

export default InspectionSettings;