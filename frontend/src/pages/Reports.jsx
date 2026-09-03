import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
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
  Loader2,
  AlertCircle,
  FileText,
  RefreshCw,
} from "lucide-react";
import { getScans } from "../services/api";

const statusStyles = {
  Passed: "bg-[#E8F8F0] text-[#07975F]",
  Warning: "bg-[#FFF3DF] text-[#E88900]",
  Failed: "bg-[#FFE9EB] text-[#E62D37]",
};

function formatTimestamp(isoString) {
  if (!isoString) return "N/A";
  try {
    const dateObj = new Date(isoString);
    if (isNaN(dateObj.getTime())) return "N/A";
    return dateObj.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return "N/A";
  }
}

function calculateScanScore(scan) {
  const status = scan.compliance?.status;
  const violationsCount = scan.compliance?.violations?.length || 0;
  if (status === "COMPLIANT") return 100;
  if (status === "NON_COMPLIANT") return Math.max(10, 100 - violationsCount * 25);
  return Math.max(30, 100 - violationsCount * 15);
}

function Reports() {
  const navigate = useNavigate();
  const [scans, setScans] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchReportsData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getScans(1, 100);
      const list = Array.isArray(data.scans)
        ? data.scans
        : Array.isArray(data)
        ? data
        : [];
      setScans(list);
      setTotalCount(typeof data.total === "number" ? data.total : list.length);
    } catch (err) {
      console.error("Reports fetch error:", err);
      setError(err.message || "Failed to load reports data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportsData();
  }, []);

  // Compute live summary statistics
  const total = totalCount || scans.length;
  const passedCount = scans.filter((s) => s.compliance?.status === "COMPLIANT").length;
  const warningCount = scans.filter((s) => s.compliance?.status === "PARTIAL").length;
  const failedCount = scans.filter((s) => s.compliance?.status === "NON_COMPLIANT").length;

  const passedPct = total > 0 ? ((passedCount / scans.length) * 100).toFixed(1) : "0.0";
  const warningPct = total > 0 ? ((warningCount / scans.length) * 100).toFixed(1) : "0.0";
  const failedPct = total > 0 ? ((failedCount / scans.length) * 100).toFixed(1) : "0.0";

  const totalScores = scans.reduce((acc, s) => acc + calculateScanScore(s), 0);
  const avgComplianceScore = scans.length > 0 ? (totalScores / scans.length).toFixed(1) : "0.0";

  // Compute rolling last 7 days trend data
  const now = new Date();
  const rollingDays = [];

  for (let i = 6; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const dayName = d.toLocaleDateString("en-US", { weekday: "short" });
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const dateKey = `${yyyy}-${mm}-${dd}`;

    rollingDays.push({
      day: dayName,
      dateKey,
      passed: 0,
      warning: 0,
      failed: 0,
    });
  }

  scans.forEach((scan) => {
    if (!scan.timestamp) return;
    const scanDate = new Date(scan.timestamp);
    if (isNaN(scanDate.getTime())) return;
    const yyyy = scanDate.getFullYear();
    const mm = String(scanDate.getMonth() + 1).padStart(2, "0");
    const dd = String(scanDate.getDate()).padStart(2, "0");
    const scanDateKey = `${yyyy}-${mm}-${dd}`;

    const targetDay = rollingDays.find((rd) => rd.dateKey === scanDateKey);
    if (targetDay) {
      const status = scan.compliance?.status;
      if (status === "COMPLIANT") targetDay.passed += 1;
      else if (status === "NON_COMPLIANT") targetDay.failed += 1;
      else targetDay.warning += 1;
    }
  });

  const trendData = rollingDays;
  const maxTrendTotal = Math.max(
    5,
    ...trendData.map((d) => d.passed + d.warning + d.failed)
  );

  // Compute Conic Donut Gradient Angles
  const passedAngle = total > 0 ? (passedCount / scans.length) * 360 : 0;
  const warningAngle = total > 0 ? (warningCount / scans.length) * 360 : 0;
  const donutGradient = total > 0
    ? `conic-gradient(#0F766E 0deg ${passedAngle}deg, #E9A23B ${passedAngle}deg ${passedAngle + warningAngle}deg, #E45B63 ${passedAngle + warningAngle}deg 360deg)`
    : "conic-gradient(#DDE6F0 0deg 360deg)";

  // Compute Top Non-Compliant Products
  const nonCompliantMap = {};
  scans.forEach((scan) => {
    if (scan.compliance?.status === "COMPLIANT") return;
    const name = scan.product?.product_name || scan.extracted_fields?.product_name || "Unidentified Product";
    const violations = scan.compliance?.violations?.length || 1;
    const score = calculateScanScore(scan);

    if (!nonCompliantMap[name]) {
      nonCompliantMap[name] = { name, violations: 0, totalScore: 0, count: 0 };
    }
    nonCompliantMap[name].violations += violations;
    nonCompliantMap[name].totalScore += score;
    nonCompliantMap[name].count += 1;
  });

  const nonCompliantProducts = Object.values(nonCompliantMap)
    .map((item) => ({
      name: item.name,
      violations: item.violations,
      score: Math.round(item.totalScore / item.count),
    }))
    .sort((a, b) => b.violations - a.violations)
    .slice(0, 4);

  // Compute Recent Inspections
  const recentInspections = scans.slice(0, 5).map((scan, index) => {
    const rawStatus = scan.compliance?.status;
    const statusLabel =
      rawStatus === "COMPLIANT"
        ? "Passed"
        : rawStatus === "NON_COMPLIANT"
        ? "Failed"
        : "Warning";

    return {
      id: scan.scan_id
        ? `INS-${scan.scan_id.slice(0, 8).toUpperCase()}`
        : `INS-00${index + 1}`,
      product: scan.product?.product_name || "Unknown Product",
      date: formatTimestamp(scan.timestamp),
      status: statusLabel,
      score: calculateScanScore(scan),
    };
  });

  return (
    <div className="min-h-full bg-[#F6F9FC] px-8 pt-8 py-6">

      {/* Header */}
      {/* <div className="flex flex-wrap items-start justify-between gap-4"> */}
      <div className="flex items-start justify-between pr-62">
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
            All Recorded
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

      {/* Error Alert */}
      {error && (
        <div className="mt-5 flex items-center justify-between rounded-xl border border-red-200 bg-red-50 p-4 text-red-800 shadow-sm">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-600" />
            <div>
              <h4 className="font-bold text-red-900">Error Loading Reports</h4>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
          <button
            onClick={fetchReportsData}
            className="flex items-center gap-1.5 rounded-lg bg-red-100 px-3 py-1.5 text-xs font-semibold text-red-800 hover:bg-red-200 transition-colors"
          >
            <RefreshCw size={14} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Stats Cards */}
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
            {loading ? "..." : total.toLocaleString()}
          </h2>

          <p className="mt-1 text-xs text-[#07975F]">
            All recorded scans
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
            {loading ? "..." : passedCount.toLocaleString()}
          </h2>

          <p className="mt-1 text-xs text-[#6B7F99]">
            {passedPct}% of sample
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
            {loading ? "..." : warningCount.toLocaleString()}
          </h2>

          <p className="mt-1 text-xs text-[#6B7F99]">
            {warningPct}% of sample
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
            {loading ? "..." : failedCount.toLocaleString()}
          </h2>

          <p className="mt-1 text-xs text-[#6B7F99]">
            {failedPct}% of sample
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
            {loading ? "..." : `${avgComplianceScore}%`}
          </h2>

          <p className="mt-1 text-xs text-[#07975F]">
            Overall accuracy
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
                Inspection results breakdown by day of week
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

          {loading ? (
            <div className="flex h-[250px] items-center justify-center text-[#71829B] gap-2">
              <Loader2 size={24} className="animate-spin text-[#0F766E]" />
              <span className="text-sm">Loading trend data...</span>
            </div>
          ) : (
            <div className="mt-7 flex h-[250px] items-end gap-5 border-b border-l border-[#E6EDF4] px-5 pb-2 pt-4">

              {trendData.map((item) => {
                const itemTotal = item.passed + item.warning + item.failed;

                return (
                  <div
                    key={item.day}
                    className="flex h-full flex-1 flex-col items-center justify-end gap-2"
                  >
                    <div className="flex h-full w-full max-w-12 flex-col justify-end overflow-hidden rounded-t-md">

                      <div
                        className="bg-[#E45B63]"
                        style={{
                          height: `${(item.failed / maxTrendTotal) * 100}%`,
                        }}
                      />

                      <div
                        className="bg-[#E9A23B]"
                        style={{
                          height: `${(item.warning / maxTrendTotal) * 100}%`,
                        }}
                      />

                      <div
                        className="bg-[#0F766E]"
                        style={{
                          height: `${(item.passed / maxTrendTotal) * 100}%`,
                        }}
                      />

                    </div>

                    <span className="text-xs text-[#71829B]">
                      {item.day}
                    </span>

                    <span className="text-[11px] text-[#94A3B8]">
                      {itemTotal}
                    </span>
                  </div>
                );
              })}

            </div>
          )}
        </div>

        {/* Compliance Status Donut */}
        <div className="rounded-2xl border border-[#DDE6F0] bg-white p-6 shadow-sm">

          <h2 className="text-lg font-bold text-[#142B4A]">
            Compliance by Status
          </h2>

          <p className="mt-1 text-sm text-[#71829B]">
            Overall inspection distribution
          </p>

          <div className="mt-7 flex items-center justify-center">

            <div
              className="relative flex h-48 w-48 items-center justify-center rounded-full transition-all"
              style={{
                background: donutGradient,
              }}
            >
              <div className="flex h-32 w-32 flex-col items-center justify-center rounded-full bg-white">
                <span className="text-3xl font-bold text-[#142B4A]">
                  {loading ? "..." : total}
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
                {passedPct}%
              </strong>
            </div>

            <div className="text-center">
              <div className="mx-auto h-2.5 w-2.5 rounded-full bg-[#E9A23B]" />
              <p className="mt-2 text-xs text-[#71829B]">
                Warning
              </p>
              <strong className="text-sm text-[#142B4A]">
                {warningPct}%
              </strong>
            </div>

            <div className="text-center">
              <div className="mx-auto h-2.5 w-2.5 rounded-full bg-[#E45B63]" />
              <p className="mt-2 text-xs text-[#71829B]">
                Failed
              </p>
              <strong className="text-sm text-[#142B4A]">
                {failedPct}%
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

            {loading ? (
              <div className="flex items-center justify-center p-8 text-[#71829B] gap-2">
                <Loader2 size={20} className="animate-spin text-[#0F766E]" />
                <span className="text-sm">Loading products...</span>
              </div>
            ) : nonCompliantProducts.length === 0 ? (
              <div className="p-8 text-center text-sm text-[#71829B]">
                <CheckCircle2 size={32} className="mx-auto mb-2 text-[#07975F]" />
                No non-compliant products detected.
              </div>
            ) : (
              nonCompliantProducts.map((product) => (
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
              ))
            )}

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

            <button
              onClick={() => navigate("/history")}
              className="text-sm font-semibold text-[#0F766E] hover:text-[#0B625C] transition-colors"
            >
              View All
            </button>

          </div>

          <div className="overflow-x-auto">

            {loading ? (
              <div className="flex items-center justify-center p-8 text-[#71829B] gap-2">
                <Loader2 size={20} className="animate-spin text-[#0F766E]" />
                <span className="text-sm">Loading recent inspections...</span>
              </div>
            ) : recentInspections.length === 0 ? (
              <div className="p-8 text-center text-sm text-[#71829B]">
                <FileText size={32} className="mx-auto mb-2 text-[#94A3B8]" />
                No recent inspection records.
              </div>
            ) : (
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
                      onClick={() => navigate("/history")}
                      className="border-b border-[#EEF2F6] last:border-none cursor-pointer hover:bg-slate-50/50 transition-colors"
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
            )}

          </div>
        </div>

      </div>
    </div>
  );
}

export default Reports;