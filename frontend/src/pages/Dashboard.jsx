import StatCard from "../components/StatCard";
import UploadBox from "../components/UploadBox";
import RecentInspections from "../components/RecentInspections";
import ComplianceInsights from "../components/ComplianceInsights";

function Dashboard() {
  return (
    <div className="p-8">

      {/* Statistics */}
      <div className="grid grid-cols-4 gap-5">
        
        <StatCard
          type="total"
          title="Total Inspections"
          value="1,248"
          trend="+18.6%"
          description="vs last 30 days"
        />

        <StatCard
          type="compliant"
          title="Compliant"
          value="876"
          description="70.2% of total"
        />

        <StatCard
          type="nonCompliant"
          title="Non-Compliant"
          value="258"
          description="20.7% of total"
        />

        <StatCard
          type="review"
          title="Under Review"
          value="114"
          description="9.1% of total"
        />

      </div>
      {/* New Inspection */}
      <div className="mt-6 grid grid-cols-1 items-start gap-6 xl:grid-cols-2">
        <UploadBox />
        <RecentInspections />
      </div>
      {/* Compliance Insights Section */}
    <div className="compliance-insights-section">
     <ComplianceInsights />
     </div>
    </div>
  );
}

export default Dashboard;