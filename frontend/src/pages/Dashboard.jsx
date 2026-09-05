import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getScans } from "../services/api";

import StatCard from "../components/StatCard";
import RecentInspections from "../components/RecentInspections";
import ComplianceInsights from "../components/ComplianceInsights";
import { AlertCircle, RefreshCw ,Camera, ArrowRight} from "lucide-react";

function Dashboard() {
  const navigate = useNavigate();

  const [scans, setScans] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getScans(1, 50);
      setScans(data.scans || []);
      setTotalCount(data.total || (data.scans ? data.scans.length : 0));
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      setError(err.message || "Failed to load dashboard metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Compute live statistics from scan records
  const compliantCount = scans.filter(
    (s) => s.compliance?.status === "COMPLIANT"
  ).length;

  const nonCompliantCount = scans.filter(
    (s) => s.compliance?.status === "NON_COMPLIANT"
  ).length;

  const reviewCount = scans.filter(
    (s) =>
      s.compliance?.status !== "COMPLIANT" &&
      s.compliance?.status !== "NON_COMPLIANT"
  ).length;

  // Safe percentage calculations
  const total = totalCount || scans.length;
  const compliantPct = total > 0 ? ((compliantCount / scans.length) * 100).toFixed(1) : "0.0";
  const nonCompliantPct = total > 0 ? ((nonCompliantCount / scans.length) * 100).toFixed(1) : "0.0";
  const reviewPct = total > 0 ? ((reviewCount / scans.length) * 100).toFixed(1) : "0.0";

  return (
    <div className="p-8">

      {/* Error Alert */}
      {error && (
        <div className="mb-6 flex items-center justify-between rounded-xl border border-red-200 bg-red-50 p-4 text-red-800 shadow-sm">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-600" />
            <div>
              <h4 className="font-bold text-red-900">Error Loading Dashboard</h4>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
          <button
            onClick={fetchDashboardData}
            className="flex items-center gap-1.5 rounded-lg bg-red-100 px-3 py-1.5 text-xs font-semibold text-red-800 hover:bg-red-200 transition-colors"
          >
            <RefreshCw size={14} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-4 gap-5">

        <StatCard
          type="total"
          title="Total Inspections"
          value={loading ? "..." : total.toLocaleString()}
          description="All recorded scans"
        />

        <StatCard
          type="compliant"
          title="Compliant"
          value={loading ? "..." : compliantCount.toLocaleString()}
          description={`${compliantPct}% of sample`}
        />

        <StatCard
          type="nonCompliant"
          title="Non-Compliant"
          value={loading ? "..." : nonCompliantCount.toLocaleString()}
          description={`${nonCompliantPct}% of sample`}
        />

        <StatCard
          type="review"
          title="Under Review"
          value={loading ? "..." : reviewCount.toLocaleString()}
          description={`${reviewPct}% of sample`}
        />

      </div>

      {/* New Inspection & Recent Inspections */}
      {/* <div className="mt-6 grid grid-cols-1 items-start gap-6 xl:grid-cols-2">

        <div
          onClick={() => navigate("/new-inspection")}
          className="cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
        >
          <UploadBox />
        </div>

        <RecentInspections
          scans={scans.slice(0, 5)}
          loading={loading}
          error={error}
        />

      </div> */}
      {/* New Inspection & Recent Inspections */}
        <div className="mt-6 space-y-6">

          {/* Start New Inspection */}
        <div
        onClick={() => navigate("/new-inspection")}
        className="group flex cursor-pointer items-center justify-between rounded-2xl border border-[#D9E5EE] bg-white px-7 py-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-[#0F766E]/40 hover:shadow-md"
        >
        <div className="flex items-center gap-5">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#F0FDFA] text-[#0F766E]">
        <Camera size={28} strokeWidth={1.8} />
        </div>

        <div>
        <h2 className="text-xl font-bold text-[#172033]">
          Start New Inspection
        </h2>

        <p className="mt-1 text-sm text-[#64748B]">
          Scan a packaged commodity and check its compliance.
        </p>
      </div>
    </div>

    <div className="flex items-center gap-2 rounded-xl bg-[#0F766E] px-5 py-3 text-sm font-semibold text-white transition group-hover:bg-[#0D6B64]">
      Start Inspection
      <ArrowRight size={18} />
    </div>
  </div>

  {/* Recent Inspections */}
  <RecentInspections
    scans={scans.slice(0, 5)}
    loading={loading}
    error={error}
  />

</div>

      {/* Compliance Insights Section */}
      <div className="compliance-insights-section">
        <ComplianceInsights />
      </div>

    </div>
  );
}

export default Dashboard;