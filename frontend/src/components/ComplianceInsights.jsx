import { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  Clock3,
  FileWarning,
  Tag,
  Scale,
} from "lucide-react";

import { getScans } from "../services/api";
import "../styles/ComplianceInsights.css";

const PAGE_SIZE = 100;

function ComplianceInsights() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAllScans = async () => {
      try {
        setLoading(true);
        setError(null);

        const firstPage = await getScans(1, PAGE_SIZE);

        const allScans = firstPage.scans || [];
        const total = firstPage.total || allScans.length;

        const totalPages = Math.ceil(total / PAGE_SIZE);

        if (totalPages > 1) {
          const remainingPages = await Promise.all(
            Array.from({ length: totalPages - 1 }, (_, index) =>
              getScans(index + 2, PAGE_SIZE)
            )
          );

          remainingPages.forEach((page) => {
            if (page.scans) {
              allScans.push(...page.scans);
            }
          });
        }

        setScans(allScans);
      } catch (err) {
        console.error("Failed to fetch compliance insights:", err);
        setError("Unable to load compliance insights.");
      } finally {
        setLoading(false);
      }
    };

    fetchAllScans();
  }, []);

  const complianceData = useMemo(() => {
    const total = scans.length;

    if (total === 0) {
      return [
        {
          label: "Compliant",
          value: 0,
          percentage: "0%",
          color: "#10B981",
        },
        {
          label: "Non-Compliant",
          value: 0,
          percentage: "0%",
          color: "#EF4444",
        },
        {
          label: "Under Review",
          value: 0,
          percentage: "0%",
          color: "#F59E0B",
        },
      ];
    }

    const compliant = scans.filter(
      (scan) => scan.compliance?.status === "COMPLIANT"
    ).length;

    const nonCompliant = scans.filter(
      (scan) => scan.compliance?.status === "NON_COMPLIANT"
    ).length;

    const partial = scans.filter(
      (scan) => scan.compliance?.status === "PARTIAL"
    ).length;

    // const getPercentage = (value) =>
    //   `${((value / total) * 100).toFixed(1)}%`;
    const getPercentage = (value) =>
  total === 0 ? "0%" : `${((value / total) * 100).toFixed(1)}%`;

    return [
      {
        label: "Compliant",
        value: compliant,
        percentage: getPercentage(compliant),
        color: "#10B981",
      },
      {
        label: "Non-Compliant",
        value: nonCompliant,
        percentage: getPercentage(nonCompliant),
        color: "#EF4444",
      },
      {
        label: "Under Review",
        value: partial,
        percentage: getPercentage(partial),
        color: "#F59E0B",
      },
    ];
  }, [scans]);

  const violations = useMemo(() => {
    const counts = {
      missingDeclarations: 0,
      mrp: 0,
      netQuantity: 0,
      readability: 0,
    };

    scans.forEach((scan) => {
      const scanViolations = scan.compliance?.violations || [];

      scanViolations.forEach((violation) => {
        const field = String(violation.field || "").toLowerCase();

        if (field.includes("mrp")) {
          counts.mrp++;
        } else if (
          field.includes("netquantity") ||
          field.includes("net_quantity")
        ) {
          counts.netQuantity++;
        } else if (
          field.includes("readability") ||
          field.includes("font") ||
          field.includes("size")
        ) {
          counts.readability++;
        } else {
          counts.missingDeclarations++;
        }
      });
    });

    return [
      {
        label: "Missing Declarations",
        count: counts.missingDeclarations,
        icon: FileWarning,
        type: "danger",
      },
      {
        label: "Incorrect MRP",
        count: counts.mrp,
        icon: Tag,
        type: "warning",
      },
      {
        label: "Net Quantity Issues",
        count: counts.netQuantity,
        icon: Scale,
        type: "warning",
      },
      {
        label: "Readability Issues",
        count: counts.readability,
        icon: AlertTriangle,
        type: "info",
      },
    ];
  }, [scans]);

  const donutBackground = useMemo(() => {
    if (scans.length === 0) {
      return "conic-gradient(#E2E8F0 0% 100%)";
    }

    const compliant = parseFloat(complianceData[0].percentage);
    const nonCompliant = parseFloat(complianceData[1].percentage);

    const firstEnd = compliant;
    const secondEnd = compliant + nonCompliant;

    return `conic-gradient(
      #10B981 0% ${firstEnd}%,
      #EF4444 ${firstEnd}% ${secondEnd}%,
      #F59E0B ${secondEnd}% 100%
    )`;
  }, [complianceData, scans.length]);

  return (
    <section className="insights-card">
      <div className="compliance-section">
        <h2>Compliance Insights</h2>

        {loading ? (
          <div className="compliance-content">
            <div className="donut-chart">
              <div className="donut-inner">
                <strong>—</strong>
                <span>Loading</span>
              </div>
            </div>

            <div className="compliance-legend">
              <p>Loading compliance data...</p>
            </div>
          </div>
        ) : error ? (
          <div className="compliance-content">
            <div className="donut-chart">
              <div className="donut-inner">
                <strong>—</strong>
                <span>Error</span>
              </div>
            </div>

            <div className="compliance-legend">
              <p>{error}</p>
            </div>
          </div>
        ) : (
          <div className="compliance-content">
            <div
              className="donut-chart"
              style={{
                background: donutBackground,
              }}
            >
              <div className="donut-inner">
                <strong>{scans.length}</strong>
                <span>Total</span>
              </div>
            </div>
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
        )}
      </div>

      <div className="violations-section">
        <div className="section-heading">
          <h2>Top Violations</h2>
          <button>View All</button>
        </div>

        {loading ? (
          <div className="violations-list">
            <p>Loading violation data...</p>
          </div>
        ) : error ? (
          <div className="violations-list">
            <p>Unable to load violations.</p>
          </div>
        ) : (
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
        )}
      </div>
      <div className="ai-insight">
      <div className="ai-insight-icon">
      <CheckCircle2 size={38} />
      </div>

    <div>
      <h3>
        Turn every label into an evidence-backed inspection.
      </h3>

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