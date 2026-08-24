import {
  CheckCircle2,
  AlertTriangle,
  Clock3,
  FileWarning,
  Tag,
  Scale,
} from "lucide-react";
import "../styles/ComplianceInsights.css";

const complianceData = [
  {
    label: "Compliant",
    value: 876,
    percentage: "70.2%",
    color: "#10B981",
  },
  {
    label: "Non-Compliant",
    value: 258,
    percentage: "20.7%",
    color: "#EF4444",
  },
  {
    label: "Under Review",
    value: 114,
    percentage: "9.1%",
    color: "#F59E0B",
  },
];

const violations = [
  {
    label: "Missing Declarations",
    count: 128,
    icon: FileWarning,
    type: "danger",
  },
  {
    label: "Incorrect MRP",
    count: 64,
    icon: Tag,
    type: "warning",
  },
  {
    label: "Net Quantity Issues",
    count: 42,
    icon: Scale,
    type: "warning",
  },
  {
    label: "Readability Issues",
    count: 24,
    icon: AlertTriangle,
    type: "info",
  },
];

function ComplianceInsights() {
  return (
    <section className="insights-card">

      {/* LEFT — Compliance Insights */}
      <div className="compliance-section">
        <h2>Compliance Insights</h2>

        <div className="compliance-content">

          {/* Donut */}
          <div
            className="donut-chart"
            style={{
              background:
                "conic-gradient(#10B981 0% 70.2%, #EF4444 70.2% 90.9%, #F59E0B 90.9% 100%)",
            }}
          >
            <div className="donut-inner">
              <strong>1,248</strong>
              <span>Total</span>
            </div>
          </div>

          {/* Legend */}
          <div className="compliance-legend">
            {complianceData.map((item) => (
              <div className="legend-row" key={item.label}>
                <span
                  className="legend-dot"
                  style={{ backgroundColor: item.color }}
                ></span>

                <span className="legend-label">
                  {item.label}
                </span>

                <span className="legend-value">
                  {item.value} ({item.percentage})
                </span>
              </div>
            ))}
          </div>

        </div>
      </div>

      {/* MIDDLE — Top Violations */}
      <div className="violations-section">
        <div className="section-heading">
          <h2>Top Violations</h2>
          <button>View All</button>
        </div>

        <div className="violations-list">
          {violations.map((item) => {
            const Icon = item.icon;

            return (
              <div className="violation-row" key={item.label}>
                <div className={`violation-icon ${item.type}`}>
                  <Icon size={16} />
                </div>

                <span className="violation-name">
                  {item.label}
                </span>

                <strong className={`violation-count ${item.type}`}>
                  {item.count}
                </strong>
              </div>
            );
          })}
        </div>
      </div>

      {/* RIGHT — AI Insight */}
      <div className="ai-insight">
        <div className="ai-insight-icon">
          <CheckCircle2 size={38} />
        </div>

        <div>
          <h3>Turn every label into an evidence-backed inspection.</h3>

          <p>
            Accurate. Transparent.
            <br />
            Accountable.
          </p>
        </div>
      </div>

    </section>
  );
}

export default ComplianceInsights;