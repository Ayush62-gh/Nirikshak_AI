import { useNavigate } from "react-router-dom";
import { ChevronRight, FileText, Loader2 } from "lucide-react";

function formatTimestamp(isoString) {
  if (!isoString) return "N/A";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return isoString;
  }
}

function mapStatusConfig(status) {
  switch (status) {
    case "COMPLIANT":
      return {
        label: "Compliant",
        className: "bg-[#ECFDF5] text-[#059669]",
        scoreText: "100/100",
        scoreClass: "text-[#059669]",
      };
    case "NON_COMPLIANT":
      return {
        label: "Non-Compliant",
        className: "bg-[#FEF2F2] text-[#DC2626]",
        scoreText: "FAIL",
        scoreClass: "text-[#DC2626]",
      };
    default:
      return {
        label: "Under Review",
        className: "bg-[#FFF7ED] text-[#EA580C]",
        scoreText: "REVIEW",
        scoreClass: "text-[#EA580C]",
      };
  }
}

function RecentInspections({ scans = [], loading = false, error = null }) {
  const navigate = useNavigate();

  return (
    <div className="min-w-0 rounded-2xl border border-[#E2E8F0] bg-white p-5 shadow-sm">

      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-bold text-[#172033]">
          Recent Inspections
        </h2>

        <button
          onClick={() => navigate("/history")}
          className="flex items-center gap-1 text-sm font-semibold text-[#0F766E] hover:text-[#0B625C] transition-colors"
        >
          View All
          <ChevronRight size={17} />
        </button>
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="flex items-center justify-center p-8 text-[#64748B] gap-3">
          <Loader2 size={20} className="animate-spin text-[#0F766E]" />
          <span className="text-sm font-medium">Loading recent inspections...</span>
        </div>
      ) : scans.length === 0 ? (
        <div className="p-8 text-center">
          <FileText size={36} className="mx-auto mb-2 text-[#94A3B8]" />
          <p className="text-sm font-semibold text-[#172033]">No inspections recorded yet</p>
          <p className="mt-1 text-xs text-[#64748B]">
            Start a new inspection scan to see compliance results here.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-[#EEF2F6]">
          {scans.map((scan, index) => {
            const rawStatus = scan.compliance?.status;
            const config = mapStatusConfig(rawStatus);
            const dateStr = formatTimestamp(scan.timestamp);
            const displayId = scan.scan_id
              ? `LMC-${scan.scan_id.slice(0, 5).toUpperCase()}`
              : `LMC-00${index + 1}`;

            return (
              <div
                key={scan.scan_id || index}
                onClick={() => navigate("/history")}
                className="grid grid-cols-[48px_minmax(50px,1fr)_auto_65px_82px_18px] items-center gap-3 border-b border-[#EEF2F6] py-3 last:border-b-0 cursor-pointer hover:bg-slate-50/50 transition-colors"
              >
                {/* Product Image Placeholder */}
                <div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-lg bg-[#F8FAFC] text-[#64748B]">
                  <FileText size={20} />
                </div>

                {/* Product Info */}
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[#172033] truncate">
                    {scan.product?.product_name || "Unknown Product"}
                  </p>

                  <p className="mt-0.5 whitespace-nowrap text-xs text-[#64748B]">
                    {displayId}
                  </p>
                </div>

                {/* Status Badge */}
                <span
                  className={`whitespace-nowrap rounded-md px-2.5 py-1 text-xs font-semibold ${config.className}`}
                >
                  {config.label}
                </span>

                {/* Score */}
                <span
                  className={`text-right text-sm font-bold ${config.scoreClass}`}
                >
                  {config.scoreText}
                </span>

                {/* Date */}
                <span className="text-right text-[10px] whitespace-nowrap text-[#64748B]">
                  {dateStr}
                </span>

                {/* Arrow */}
                <div className="flex justify-end text-[#94A3B8]">
                  <ChevronRight size={18} />
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}

export default RecentInspections;