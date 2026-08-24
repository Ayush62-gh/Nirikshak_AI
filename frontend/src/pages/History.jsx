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
  AlertCircle,
  Loader2,
  ChevronRight,
  ChevronLeft,
  X,
  ShieldAlert,
  RefreshCw,
} from "lucide-react";
import { getScans, getScanById } from "../services/api";
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

  // Modal details state
  const [selectedScanId, setSelectedScanId] = useState(null);
  const [scanDetails, setScanDetails] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState(null);

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

  const handleOpenDetails = async (scanId) => {
    setSelectedScanId(scanId);
    setDetailsLoading(true);
    setDetailsError(null);
    setScanDetails(null);

    try {
      const data = await getScanById(scanId);
      setScanDetails(data);
    } catch (err) {
      console.error("Failed to fetch scan details:", err);
      setDetailsError(err.message || "Failed to load scan details.");
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleCloseDetails = () => {
    setSelectedScanId(null);
    setScanDetails(null);
    setDetailsError(null);
  };

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
                        <button
                          onClick={() => handleOpenDetails(scan.scan_id)}
                          className="view-btn cursor-pointer transition-colors"
                        >
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

      {/* View Details Modal Overlay */}
      {selectedScanId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="relative w-full max-w-3xl rounded-2xl bg-white p-6 shadow-2xl transition-all my-8 border border-slate-200">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-xl font-bold text-slate-800">
                  Inspection Details
                </h2>
                <p className="mt-0.5 text-xs text-slate-500 font-mono">
                  ID: {selectedScanId}
                </p>
              </div>

              <button
                onClick={handleCloseDetails}
                className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Content */}
            {detailsLoading ? (
              <div className="flex flex-col items-center justify-center py-16 text-slate-500">
                <Loader2 size={32} className="animate-spin text-teal-600 mb-3" />
                <p className="text-sm font-medium">Fetching detailed scan report...</p>
              </div>
            ) : detailsError ? (
              <div className="py-8">
                <div className="flex items-start gap-3 rounded-xl bg-red-50 p-4 text-red-800 border border-red-200">
                  <AlertCircle size={20} className="mt-0.5 shrink-0 text-red-600" />
                  <div className="flex-1">
                    <h4 className="font-bold">Error Loading Details</h4>
                    <p className="mt-1 text-xs text-red-700">{detailsError}</p>
                  </div>
                  <button
                    onClick={() => handleOpenDetails(selectedScanId)}
                    className="flex items-center gap-1 rounded-lg bg-red-100 px-3 py-1 text-xs font-semibold text-red-800 hover:bg-red-200"
                  >
                    <RefreshCw size={12} /> Retry
                  </button>
                </div>
              </div>
            ) : scanDetails ? (
              <div className="mt-5 space-y-6">

                {/* Status & Timestamp Header Banner */}
                <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-slate-50 p-4 border border-slate-200/80">
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Compliance Status
                    </span>
                    <div className="mt-1 flex items-center gap-2">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-bold ${
                          scanDetails.compliance?.status === "COMPLIANT"
                            ? "bg-emerald-100 text-emerald-800"
                            : scanDetails.compliance?.status === "NON_COMPLIANT"
                            ? "bg-red-100 text-red-800"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {scanDetails.compliance?.status === "COMPLIANT" && <CheckCircle2 size={14} />}
                        {scanDetails.compliance?.status === "NON_COMPLIANT" && <XCircle size={14} />}
                        {scanDetails.compliance?.status !== "COMPLIANT" && scanDetails.compliance?.status !== "NON_COMPLIANT" && <AlertTriangle size={14} />}
                        {scanDetails.compliance?.status || "PARTIAL"}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Scanned On
                    </span>
                    <p className="mt-1 text-sm font-semibold text-slate-700">
                      {formatTimestamp(scanDetails.timestamp).date} at {formatTimestamp(scanDetails.timestamp).time}
                    </p>
                  </div>
                </div>

                {/* Mandated Declarations Grid */}
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">
                    LMPC Mandated Declarations
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                    <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-2xs">
                      <p className="text-xs text-slate-400 font-medium">Product Name</p>
                      <p className="mt-1 font-semibold text-slate-800">
                        {scanDetails.product?.product_name || scanDetails.extracted_fields?.product_name || "Not Detected"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-2xs">
                      <p className="text-xs text-slate-400 font-medium">Manufacturer / Packer</p>
                      <p className="mt-1 font-semibold text-slate-800">
                        {scanDetails.product?.manufacturer || scanDetails.extracted_fields?.manufacturer || "Not Detected"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-2xs sm:col-span-2">
                      <p className="text-xs text-slate-400 font-medium">Manufacturer Address</p>
                      <p className="mt-1 font-semibold text-slate-800">
                        {scanDetails.extracted_fields?.manufacturer_address || "Not Detected"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-2xs">
                      <p className="text-xs text-slate-400 font-medium">Net Quantity</p>
                      <p className="mt-1 font-semibold text-slate-800">
                        {scanDetails.product?.net_quantity || scanDetails.extracted_fields?.net_quantity || "Not Declared"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-2xs">
                      <p className="text-xs text-slate-400 font-medium">Maximum Retail Price (MRP)</p>
                      <p className="mt-1 font-semibold text-slate-800">
                        {scanDetails.product?.mrp || scanDetails.extracted_fields?.mrp || "Not Declared"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-2xs">
                      <p className="text-xs text-slate-400 font-medium">Month & Year of Mfg / Packing</p>
                      <p className="mt-1 font-semibold text-slate-800">
                        {scanDetails.product?.mfg_date || scanDetails.extracted_fields?.mfg_date || "Not Declared"}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-2xs">
                      <p className="text-xs text-slate-400 font-medium">Consumer Care Details</p>
                      <p className="mt-1 font-semibold text-slate-800">
                        {scanDetails.product?.consumer_care || scanDetails.extracted_fields?.consumer_care || "Not Declared"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Violations List Section */}
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">
                    Rule Violations ({scanDetails.compliance?.violations?.length || 0})
                  </h3>

                  {!scanDetails.compliance?.violations || scanDetails.compliance.violations.length === 0 ? (
                    <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-4 text-emerald-800 border border-emerald-200">
                      <CheckCircle2 size={18} className="text-emerald-600 shrink-0" />
                      <p className="text-sm font-medium">Fully compliant. No LMPC rule violations detected on package label.</p>
                    </div>
                  ) : (
                    <div className="space-y-2.5">
                      {scanDetails.compliance.violations.map((v, idx) => (
                        <div key={idx} className="rounded-xl border border-red-200 bg-red-50/70 p-3.5">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-xs text-red-900">
                              {v.rule || "Compliance Rule Violation"}
                            </span>
                            {v.field && (
                              <span className="rounded bg-red-100 px-2 py-0.5 text-[10px] font-mono font-semibold text-red-800">
                                field: {v.field}
                              </span>
                            )}
                          </div>
                          <p className="mt-1.5 text-xs text-red-800 leading-relaxed">
                            {v.description}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

              </div>
            ) : null}

            {/* Modal Footer */}
            <div className="mt-6 flex justify-end border-t border-slate-100 pt-4">
              <button
                onClick={handleCloseDetails}
                className="rounded-xl bg-slate-100 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-200 transition-colors"
              >
                Close
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}

export default History;