import {
  BarChart3,
  CalendarDays,
  Download,
  Filter,
  ChevronDown,
  TrendingUp,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  ArrowUpRight,
} from "lucide-react";

const trendData = [
  { day: "Mon", passed: 18, warning: 5, failed: 2 },
  { day: "Tue", passed: 22, warning: 4, failed: 1 },
  { day: "Wed", passed: 16, warning: 7, failed: 3 },
  { day: "Thu", passed: 24, warning: 3, failed: 2 },
  { day: "Fri", passed: 20, warning: 6, failed: 2 },
  { day: "Sat", passed: 15, warning: 4, failed: 1 },
  { day: "Sun", passed: 21, warning: 5, failed: 1 },
];

const nonCompliantProducts = [
  {
    name: "Coca-Cola Original",
    violations: 8,
    score: 45,
  },
  {
    name: "Maggi 2-Minute Noodles",
    violations: 6,
    score: 68,
  },
  {
    name: "Parle-G Original",
    violations: 4,
    score: 72,
  },
  {
    name: "Sunlite Refined Oil",
    violations: 3,
    score: 76,
  },
];

const recentInspections = [
  {
    product: "Sunlite Refined Oil",
    id: "INS-2026-000128",
    date: "Aug 23, 2026",
    status: "Passed",
    score: 92,
  },
  {
    product: "Amul Taaza Milk",
    id: "INS-2026-000127",
    date: "Aug 23, 2026",
    status: "Passed",
    score: 95,
  },
  {
    product: "Maggi 2-Minute Noodles",
    id: "INS-2026-000126",
    date: "Aug 22, 2026",
    status: "Warning",
    score: 68,
  },
  {
    product: "Coca-Cola Original",
    id: "INS-2026-000124",
    date: "Aug 21, 2026",
    status: "Failed",
    score: 45,
  },
];

const statusStyles = {
  Passed: "bg-[#E8F8F0] text-[#07975F]",
  Warning: "bg-[#FFF3DF] text-[#E88900]",
  Failed: "bg-[#FFE9EB] text-[#E62D37]",
};

function Reports() {
  return (
    <div className="min-h-full bg-[#F6F9FC] px-8 py-6">

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-[#142B4A]">
            Reports & Analytics
          </h1>

          <p className="mt-1.5 text-sm text-[#6B7F99]">
            Analyze inspection performance and compliance trends.
          </p>
        </div>

        <button className="flex items-center gap-2 rounded-lg bg-[#0F766E] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0B625C]">
          <Download size={18} />
          Export Report
        </button>
      </div>

      {/* Filters */}
      <div className="mt-5 flex flex-wrap items-center gap-3 rounded-2xl border border-[#DDE6F0] bg-white p-4 shadow-sm">

        <button className="flex min-w-[170px] items-center justify-between gap-4 rounded-lg border border-[#D8E1EB] px-4 py-2.5 text-sm text-[#405570]">
          <span className="flex items-center gap-2">
            <CalendarDays size={17} />
            Last 30 Days
          </span>
          <ChevronDown size={16} />
        </button>

        <button className="flex min-w-[170px] items-center justify-between gap-4 rounded-lg border border-[#D8E1EB] px-4 py-2.5 text-sm text-[#405570]">
          <span className="flex items-center gap-2">
            <Filter size={17} />
            All Products
          </span>
          <ChevronDown size={16} />
        </button>

        <button className="flex min-w-[150px] items-center justify-between gap-4 rounded-lg border border-[#D8E1EB] px-4 py-2.5 text-sm text-[#405570]">
          All Status
          <ChevronDown size={16} />
        </button>

        <div className="ml-auto flex items-center gap-2 text-sm text-[#6B7F99]">
          <TrendingUp size={17} className="text-[#0F766E]" />
          Updated today
        </div>
      </div>

      {/* Stats */}
      <div className="mt-5 grid grid-cols-2 gap-4 xl:grid-cols-5">

        <div className="rounded-2xl border border-[#DDE6F0] bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[#6B7F99]">
              Total Inspections
            </p>

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#E5F0FF] text-[#2878D7]">
              <BarChart3 size={18} />
            </div>
          </div>

          <h2 className="mt-3 text-2xl font-bold text-[#142B4A]">
            128
          </h2>

          <p className="mt-1 text-xs text-[#07975F]">
            +12.4% from last month
          </p>
        </div>

        <div className="rounded-2xl border border-[#DDE6F0] bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[#6B7F99]">Passed</p>

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#E8F8F0] text-[#07975F]">
              <CheckCircle2 size={18} />
            </div>
          </div>

          <h2 className="mt-3 text-2xl font-bold text-[#07975F]">
            98
          </h2>

          <p className="mt-1 text-xs text-[#6B7F99]">
            76.6% of inspections
          </p>
        </div>

        <div className="rounded-2xl border border-[#DDE6F0] bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[#6B7F99]">Warnings</p>

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#FFF3DF] text-[#E88900]">
              <AlertTriangle size={18} />
            </div>
          </div>

          <h2 className="mt-3 text-2xl font-bold text-[#E88900]">
            18
          </h2>

          <p className="mt-1 text-xs text-[#6B7F99]">
            14.1% of inspections
          </p>
        </div>

        <div className="rounded-2xl border border-[#DDE6F0] bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[#6B7F99]">Failed</p>

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#FFE9EB] text-[#E62D37]">
              <XCircle size={18} />
            </div>
          </div>

          <h2 className="mt-3 text-2xl font-bold text-[#E62D37]">
            12
          </h2>

          <p className="mt-1 text-xs text-[#6B7F99]">
            9.3% of inspections
          </p>
        </div>

        <div className="rounded-2xl border border-[#DDE6F0] bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[#6B7F99]">
              Avg. Compliance
            </p>

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#E8F8F5] text-[#0F766E]">
              <ShieldCheck size={18} />
            </div>
          </div>

          <h2 className="mt-3 text-2xl font-bold text-[#0F766E]">
            86.4%
          </h2>

          <p className="mt-1 text-xs text-[#07975F]">
            +3.2% improvement
          </p>
        </div>

      </div>

      {/* Charts */}
      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-[1.65fr_1fr]">

        {/* Inspection Trends */}
        <div className="rounded-2xl border border-[#DDE6F0] bg-white p-6 shadow-sm">

          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-lg font-bold text-[#142B4A]">
                Inspection Trends
              </h2>

              <p className="mt-1 text-sm text-[#71829B]">
                Inspection results over the last 7 days
              </p>
            </div>

            <div className="flex items-center gap-4 text-xs text-[#6B7F99]">
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#0F766E]" />
                Passed
              </span>

              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#E9A23B]" />
                Warning
              </span>

              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#E45B63]" />
                Failed
              </span>
            </div>
          </div>

          <div className="mt-7 flex h-[250px] items-end gap-5 border-b border-l border-[#E6EDF4] px-5 pb-2 pt-4">

            {trendData.map((item) => {
              const total = item.passed + item.warning + item.failed;
              const max = 35;

              return (
                <div
                  key={item.day}
                  className="flex h-full flex-1 flex-col items-center justify-end gap-2"
                >
                  <div className="flex h-full w-full max-w-12 flex-col justify-end overflow-hidden rounded-t-md">

                    <div
                      className="bg-[#E45B63]"
                      style={{
                        height: `${(item.failed / max) * 100}%`,
                      }}
                    />

                    <div
                      className="bg-[#E9A23B]"
                      style={{
                        height: `${(item.warning / max) * 100}%`,
                      }}
                    />

                    <div
                      className="bg-[#0F766E]"
                      style={{
                        height: `${(item.passed / max) * 100}%`,
                      }}
                    />

                  </div>

                  <span className="text-xs text-[#71829B]">
                    {item.day}
                  </span>

                  <span className="text-[11px] text-[#94A3B8]">
                    {total}
                  </span>
                </div>
              );
            })}

          </div>
        </div>

        {/* Compliance Status */}
        <div className="rounded-2xl border border-[#DDE6F0] bg-white p-6 shadow-sm">

          <h2 className="text-lg font-bold text-[#142B4A]">
            Compliance by Status
          </h2>

          <p className="mt-1 text-sm text-[#71829B]">
            Overall inspection distribution
          </p>

          <div className="mt-7 flex items-center justify-center">

            <div
              className="relative flex h-48 w-48 items-center justify-center rounded-full"
              style={{
                background:
                  "conic-gradient(#0F766E 0deg 276deg, #E9A23B 276deg 327deg, #E45B63 327deg 360deg)",
              }}
            >
              <div className="flex h-32 w-32 flex-col items-center justify-center rounded-full bg-white">
                <span className="text-3xl font-bold text-[#142B4A]">
                  128
                </span>
                <span className="text-xs text-[#71829B]">
                  Total
                </span>
              </div>
            </div>

          </div>

          <div className="mt-6 grid grid-cols-3 gap-3">

            <div className="text-center">
              <div className="mx-auto h-2.5 w-2.5 rounded-full bg-[#0F766E]" />
              <p className="mt-2 text-xs text-[#71829B]">
                Passed
              </p>
              <strong className="text-sm text-[#142B4A]">
                76.6%
              </strong>
            </div>

            <div className="text-center">
              <div className="mx-auto h-2.5 w-2.5 rounded-full bg-[#E9A23B]" />
              <p className="mt-2 text-xs text-[#71829B]">
                Warning
              </p>
              <strong className="text-sm text-[#142B4A]">
                14.1%
              </strong>
            </div>

            <div className="text-center">
              <div className="mx-auto h-2.5 w-2.5 rounded-full bg-[#E45B63]" />
              <p className="mt-2 text-xs text-[#71829B]">
                Failed
              </p>
              <strong className="text-sm text-[#142B4A]">
                9.3%
              </strong>
            </div>

          </div>

        </div>
      </div>

      {/* Bottom Section */}
      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-[1fr_1.45fr]">

        {/* Non Compliant Products */}
        <div className="rounded-2xl border border-[#DDE6F0] bg-white p-6 shadow-sm">

          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-[#142B4A]">
                Top Non-Compliant Products
              </h2>

              <p className="mt-1 text-sm text-[#71829B]">
                Products requiring attention
              </p>
            </div>

            <ArrowUpRight size={19} className="text-[#E62D37]" />
          </div>

          <div className="mt-5 space-y-4">

            {nonCompliantProducts.map((product) => (
              <div
                key={product.name}
                className="rounded-xl border border-[#E7EDF4] p-4"
              >
                <div className="flex items-center justify-between gap-3">

                  <div>
                    <p className="text-sm font-semibold text-[#243B55]">
                      {product.name}
                    </p>

                    <p className="mt-1 text-xs text-[#7B8DA3]">
                      {product.violations} violations detected
                    </p>
                  </div>

                  <span className="text-sm font-bold text-[#E62D37]">
                    {product.score}%
                  </span>

                </div>

                <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#EEF2F6]">
                  <div
                    className="h-full rounded-full bg-[#E45B63]"
                    style={{
                      width: `${product.score}%`,
                    }}
                  />
                </div>
              </div>
            ))}

          </div>
        </div>

        {/* Recent Inspections */}
        <div className="rounded-2xl border border-[#DDE6F0] bg-white shadow-sm">

          <div className="flex items-center justify-between border-b border-[#E6EDF4] px-6 py-5">

            <div>
              <h2 className="text-lg font-bold text-[#142B4A]">
                Recent Inspections
              </h2>

              <p className="mt-1 text-sm text-[#71829B]">
                Latest compliance checks
              </p>
            </div>

            <button className="text-sm font-semibold text-[#0F766E]">
              View All
            </button>

          </div>

          <div className="overflow-x-auto">

            <table className="w-full min-w-[650px]">

              <thead>
                <tr className="border-b border-[#E6EDF4] text-left">
                  <th className="px-6 py-3 text-xs font-semibold text-[#71829B]">
                    Product
                  </th>

                  <th className="px-4 py-3 text-xs font-semibold text-[#71829B]">
                    Date
                  </th>

                  <th className="px-4 py-3 text-xs font-semibold text-[#71829B]">
                    Status
                  </th>

                  <th className="px-6 py-3 text-xs font-semibold text-[#71829B]">
                    Score
                  </th>
                </tr>
              </thead>

              <tbody>

                {recentInspections.map((inspection) => (
                  <tr
                    key={inspection.id}
                    className="border-b border-[#EEF2F6] last:border-none"
                  >

                    <td className="px-6 py-4">
                      <p className="text-sm font-semibold text-[#243B55]">
                        {inspection.product}
                      </p>

                      <p className="mt-1 text-xs text-[#8A9AAF]">
                        {inspection.id}
                      </p>
                    </td>

                    <td className="px-4 py-4 text-sm text-[#64748B]">
                      {inspection.date}
                    </td>

                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold ${statusStyles[inspection.status]}`}
                      >
                        {inspection.status === "Passed" && (
                          <CheckCircle2 size={13} />
                        )}

                        {inspection.status === "Warning" && (
                          <AlertTriangle size={13} />
                        )}

                        {inspection.status === "Failed" && (
                          <XCircle size={13} />
                        )}

                        {inspection.status}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      <span
                        className={`text-sm font-bold ${
                          inspection.score >= 80
                            ? "text-[#07975F]"
                            : inspection.score >= 60
                            ? "text-[#E88900]"
                            : "text-[#E62D37]"
                        }`}
                      >
                        {inspection.score}%
                      </span>
                    </td>

                  </tr>
                ))}

              </tbody>

            </table>

          </div>
        </div>

      </div>
    </div>
  );
}

export default Reports;