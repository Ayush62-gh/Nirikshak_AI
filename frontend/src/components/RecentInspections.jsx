import { ChevronRight } from "lucide-react";

const inspections = [
  {
    id: "LMC-00124",
    product: "Premium Tea",
    status: "Non-Compliant",
    score: "72/100",
    date: "23 Aug 2026",
    image: "/products/tea.jpeg",
  },
  {
    id: "LMC-00123",
    product: "Refined Sugar",
    status: "Compliant",
    score: "96/100",
    date: "23 Aug 2026",
    image: "/products/sugar.png",
  },
  {
    id: "LMC-00122",
    product: "Digestive Biscuits",
    status: "Non-Compliant",
    score: "45/100",
    date: "22 Aug 2026",
    image: "/products/biscuits.jpeg",
  },
  {
    id: "LMC-00121",
    product: "Sunflower Oil",
    status: "Compliant",
    score: "93/100",
    date: "22 Aug 2026",
    image: "/products/oil.png",
  },
  {
    id: "LMC-00120",
    product: "Wheat Flour",
    status: "Under Review",
    score: "—",
    date: "21 Aug 2026",
    image: "/products/flour.jpeg",
  },
];

function RecentInspections() {
  return (
    <div className="min-w-0 rounded-2xl border border-[#E2E8F0] bg-white p-5 shadow-sm">

      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-bold text-[#172033]">
          Recent Inspections
        </h2>

        <button className="flex items-center gap-1 text-sm font-semibold text-[#0F766E] hover:text-[#0B625C]">
          View All
          <ChevronRight size={17} />
        </button>
      </div>

      {/* Inspection List */}
      <div className="divide-y divide-[#EEF2F6]">
        {inspections.map((inspection) => (
  <div
    key={inspection.id}
    className="grid grid-cols-[48px_minmax(50px,1fr)_auto_65px_82px_18px] items-center gap-3 border-b border-[#EEF2F6] py-3 last:border-b-0"
  >
    {/* Product Image */}
    <div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-lg bg-[#F8FAFC]">
      <img
        src={inspection.image}
        alt={inspection.product}
        className="h-full w-full object-contain"
      />
    </div>

    {/* Product */}
    <div className="min-w-0">
      <p className="text-sm font-semibold text-[#172033]">
        {inspection.product}
      </p>

      <p className="mt-0.5 whitespace-nowrap text-xs text-[#64748B]">
        {inspection.id}
      </p>
    </div>

    {/* Status */}
    <span
      className={`whitespace-nowrap rounded-md px-2.5 py-1 text-xs font-semibold ${
        inspection.status === "Compliant"
          ? "bg-[#ECFDF5] text-[#059669]"
          : inspection.status === "Non-Compliant"
          ? "bg-[#FEF2F2] text-[#DC2626]"
          : "bg-[#FFF7ED] text-[#EA580C]"
      }`}
    >
      {inspection.status}
    </span>

    {/* Score */}
    <span
      className={`text-right text-sm font-bold ${
        inspection.status === "Compliant"
          ? "text-[#059669]"
          : inspection.status === "Non-Compliant"
          ? "text-[#DC2626]"
          : "text-[#94A3B8]"
      }`}
    >
      {inspection.score}
    </span>

    {/* Date */}
    <span className="text-right text-[10px] whitespace-nowrap text-[#64748B]">
      {inspection.date}
    </span>

    {/* Arrow */}
    <button className="flex justify-end text-[#94A3B8] hover:text-[#12355B]">
      <ChevronRight size={18} />
    </button>
  </div>
))}
      </div>

    </div>
  );
}

export default RecentInspections;