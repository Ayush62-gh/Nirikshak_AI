import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getScans } from "../services/api";

import StatCard from "../components/StatCard";
import UploadBox from "../components/UploadBox";
import RecentInspections from "../components/RecentInspections";
import ComplianceInsights from "../components/ComplianceInsights";
import { AlertCircle, RefreshCw } from "lucide-react";

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
      <div className="mt-6 grid grid-cols-1 items-start gap-6 xl:grid-cols-2">

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

      </div>

      {/* Compliance Insights Section */}
      <div className="compliance-insights-section">
        <ComplianceInsights />
      </div>

    </div>
  );
}

export default Dashboard;