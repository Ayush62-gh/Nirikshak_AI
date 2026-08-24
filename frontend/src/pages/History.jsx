import React, { useState, useEffect } from "react";
import {
  Search,
  CalendarDays,
  Download,
  FileText,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { getScans } from "../services/api";
import "../styles/History.css";

const statusConfig = {
  Passed: {
    className: "status-passed",
    icon: <CheckCircle2 size={15} />,
  },
  Warning: {
    className: "status-warning",
    icon: <AlertTriangle size={15} />,
  },
  Failed: {
    className: "status-failed",
    icon: <XCircle size={15} />,
  },
};

function mapComplianceStatus(status) {
  switch (status) {
    case "COMPLIANT":
      return "Passed";
    case "PARTIAL":
      return "Warning";
    case "NON_COMPLIANT":
      return "Failed";
    default:
      return "Warning";
  }
}

function formatTimestamp(isoString) {
  if (!isoString) return { date: "N/A", time: "N/A" };
  try {
    const dateObj = new Date(isoString);
    if (isNaN(dateObj.getTime())) return { date: "N/A", time: "N/A" };

    const date = dateObj.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });

    const time = dateObj.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });

    return { date, time };
  } catch {
    return { date: "N/A", time: "N/A" };
  }
}

function History() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("All Status");

  useEffect(() => {
    let isMounted = true;

    async function fetchHistory() {
      setLoading(true);
      setError(null);

      try {
        const data = await getScans(page, limit);
        if (!isMounted) return;

        const scanList = Array.isArray(data.scans)
          ? data.scans
          : Array.isArray(data)
          ? data
          : [];

        setScans(scanList);
        setTotal(typeof data.total === "number" ? data.total : scanList.length);
      } catch (err) {
        if (!isMounted) return;
        setError(err.message || "Failed to fetch scan history.");
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchHistory();

    return () => {
      isMounted = false;
    };
  }, [page, limit]);

  // Compute stats summary dynamically from fetched scans
  const totalCount = total || scans.length;
  const passedCount = scans.filter(
    (s) => s.compliance?.status === "COMPLIANT"
  ).length;
  const warningCount = scans.filter(
    (s) => s.compliance?.status === "PARTIAL"
  ).length;
  const failedCount = scans.filter(
    (s) => s.compliance?.status === "NON_COMPLIANT"
  ).length;

  const passedPct = scans.length > 0 ? ((passedCount / scans.length) * 100).toFixed(1) + "%" : "0%";
  const warningPct = scans.length > 0 ? ((warningCount / scans.length) * 100).toFixed(1) + "%" : "0%";
  const failedPct = scans.length > 0 ? ((failedCount / scans.length) * 100).toFixed(1) + "%" : "0%";

  // Filter scans based on search and status select
  const filteredInspections = scans.filter((scan) => {
    const productName = scan.product?.product_name || "";
    const scanId = scan.scan_id || "";

    const matchesSearch =
      productName.toLowerCase().includes(search.toLowerCase()) ||
      scanId.toLowerCase().includes(search.toLowerCase());

    const displayStatus = mapComplianceStatus(scan.compliance?.status);
    const matchesStatus =
      status === "All Status" || displayStatus === status;

    return matchesSearch && matchesStatus;
  });

  const totalPages = Math.max(1, Math.ceil(totalCount / limit));
  const startResult = totalCount === 0 ? 0 : (page - 1) * limit + 1;
  const endResult = Math.min(page * limit, totalCount);

  return (
    <div className="history-page">

      {/* Page Header */}
      <div className="history-header">
        <h1>Inspection History</h1>
        <p>View and track all your past compliance inspections.</p>
      </div>

      {/* Search & Filters */}
      <div className="history-toolbar">

        <div className="history-search">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search by product name, ID or batch..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <button className="filter-btn">
          <CalendarDays size={18} />
          <span>Date Range</span>
          <ChevronDown size={16} />
        </button>

        <select
          className="filter-btn status-filter"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option>All Status</option>
          <option>Passed</option>
          <option>Warning</option>
          <option>Failed</option>
        </select>

        <button className="export-btn">
          <Download size={18} />
          Export Report
        </button>

      </div>

      {/* Summary Cards */}
      <div className="history-stats">

        <div className="history-stat-card">
          <div className="stat-icon stat-blue">
            <FileText size={24} />
          </div>
          <div>
            <span>Total Inspections</span>
            <strong>{totalCount}</strong>
            <small>All time</small>
          </div>
        </div>

        <div className="history-stat-card">
          <div className="stat-icon stat-green">
            <CheckCircle2 size={24} />
          </div>
          <div>
            <span>Passed (This Page)</span>
            <strong>{passedCount}</strong>
            <small className="green-text">{passedPct} of current page</small>
          </div>
        </div>

        <div className="history-stat-card">
          <div className="stat-icon stat-orange">
            <AlertTriangle size={24} />
          </div>
          <div>
            <span>Warnings (This Page)</span>
            <strong>{warningCount}</strong>
            <small className="orange-text">{warningPct} of current page</small>
          </div>
        </div>

        <div className="history-stat-card">
          <div className="stat-icon stat-red">
            <XCircle size={24} />
          </div>
          <div>
            <span>Failed (This Page)</span>
            <strong>{failedCount}</strong>
            <small className="red-text">{failedPct} of current page</small>
          </div>
        </div>

      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-red-800 shadow-sm">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
          <div className="flex-1">
            <h4 className="font-bold text-red-900">Failed to Load History</h4>
            <p className="mt-1 text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Inspection Table Card */}
      <div className="inspection-table-card">

        {loading ? (
          <div className="flex items-center justify-center p-12 text-[#71829b] gap-3">
            <Loader2 size={24} className="animate-spin text-[#2476e8]" />
            <span className="font-medium text-sm">Loading inspection history...</span>
          </div>
        ) : filteredInspections.length === 0 ? (
          <div className="p-12 text-center">
            <FileText size={42} className="mx-auto mb-3 text-[#b0c0d4]" />
            <h3 className="text-base font-bold text-[#142d4c]">No inspections yet</h3>
            <p className="mt-1 text-sm text-[#71829b]">
              {scans.length === 0
                ? "No compliance inspections have been recorded yet."
                : "No inspection records match your search filter."}
            </p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>

              <thead>
                <tr>
                  <th>#</th>
                  <th>Product</th>
                  <th>Inspection ID</th>
                  <th>Date & Time</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {filteredInspections.map((scan, index) => {
                  const displayStatus = mapComplianceStatus(
                    scan.compliance?.status
                  );
                  const config = statusConfig[displayStatus];
                  const { date, time } = formatTimestamp(scan.timestamp);

                  const displayId = scan.scan_id
                    ? `Scan #${scan.scan_id.slice(0, 8)}`
                    : "N/A";

                  return (
                    <tr key={scan.scan_id || index}>

                      <td>{(page - 1) * limit + index + 1}</td>

                      <td>
                        <div className="product-info">
                          <div className="product-placeholder">
                            <FileText size={18} />
                          </div>

                          <div>
                            <strong>
                              {scan.product?.product_name || "Unknown Product"}
                            </strong>
                            <span>{scan.product?.net_quantity || "N/A"}</span>
                          </div>
                        </div>
                      </td>

                      <td className="inspection-id">
                        {displayId}
                      </td>

                      <td>
                        <div className="date-info">
                          <span>{date}</span>
                          <span>{time}</span>
                        </div>
                      </td>

                      <td>
                        <span className={`status-badge ${config.className}`}>
                          {config.icon}
                          {displayStatus}
                        </span>
                      </td>

                      <td>
                        <button className="view-btn">
                          View Details
                          <ChevronRight size={17} />
                        </button>
                      </td>

                    </tr>
                  );
                })}
              </tbody>

            </table>
          </div>
        )}

        {/* Pagination */}
        <div className="pagination">

          <span>
            Showing {startResult} to {endResult} of {totalCount} results
          </span>

          <div className="page-controls">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className={page <= 1 ? "opacity-50 cursor-not-allowed" : ""}
            >
              <ChevronLeft size={17} />
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
              <button
                key={pageNum}
                type="button"
                className={page === pageNum ? "active-page" : ""}
                onClick={() => setPage(pageNum)}
              >
                {pageNum}
              </button>
            ))}

            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className={page >= totalPages ? "opacity-50 cursor-not-allowed" : ""}
            >
              <ChevronRight size={17} />
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}

export default History;