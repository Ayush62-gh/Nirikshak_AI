import React, { useState } from "react";
import {
  Search,
  CalendarDays,
  SlidersHorizontal,
  Download,
  FileText,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
} from "lucide-react";
import "../styles/History.css";

const inspections = [
  {
    id: "INS-2026-000128",
    product: "Sunlite Refined Oil",
    quantity: "1L Pouch",
    date: "Aug 23, 2026",
    time: "09:45 PM",
    status: "Passed",
    score: "92%",
  },
  {
    id: "INS-2026-000127",
    product: "Amul Taaza Milk",
    quantity: "500ml",
    date: "Aug 23, 2026",
    time: "07:30 PM",
    status: "Passed",
    score: "95%",
  },
  {
    id: "INS-2026-000126",
    product: "Maggi 2-Minute Noodles",
    quantity: "70g",
    date: "Aug 22, 2026",
    time: "10:15 PM",
    status: "Warning",
    score: "68%",
  },
  {
    id: "INS-2026-000125",
    product: "Parle-G Original",
    quantity: "250g",
    date: "Aug 22, 2026",
    time: "06:50 PM",
    status: "Passed",
    score: "89%",
  },
  {
    id: "INS-2026-000124",
    product: "Coca-Cola Original",
    quantity: "500ml",
    date: "Aug 21, 2026",
    time: "08:20 PM",
    status: "Failed",
    score: "45%",
  },
];

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

function History() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("All Status");

  const filteredInspections = inspections.filter((inspection) => {
    const matchesSearch =
      inspection.product.toLowerCase().includes(search.toLowerCase()) ||
      inspection.id.toLowerCase().includes(search.toLowerCase());

    const matchesStatus =
      status === "All Status" || inspection.status === status;

    return matchesSearch && matchesStatus;
  });

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
            <strong>128</strong>
            <small>All time</small>
          </div>
        </div>

        <div className="history-stat-card">
          <div className="stat-icon stat-green">
            <CheckCircle2 size={24} />
          </div>
          <div>
            <span>Passed</span>
            <strong>98</strong>
            <small className="green-text">76.6%</small>
          </div>
        </div>

        <div className="history-stat-card">
          <div className="stat-icon stat-orange">
            <AlertTriangle size={24} />
          </div>
          <div>
            <span>Warnings</span>
            <strong>18</strong>
            <small className="orange-text">14.1%</small>
          </div>
        </div>

        <div className="history-stat-card">
          <div className="stat-icon stat-red">
            <XCircle size={24} />
          </div>
          <div>
            <span>Failed</span>
            <strong>12</strong>
            <small className="red-text">9.3%</small>
          </div>
        </div>

      </div>

      {/* Inspection Table */}
      <div className="inspection-table-card">

        <div className="table-wrapper">
          <table>

            <thead>
              <tr>
                <th>#</th>
                <th>Product</th>
                <th>Inspection ID</th>
                <th>Date & Time</th>
                <th>Status</th>
                <th>Compliance Score</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {filteredInspections.map((inspection, index) => {
                const config = statusConfig[inspection.status];

                return (
                  <tr key={inspection.id}>

                    <td>{index + 1}</td>

                    <td>
                      <div className="product-info">
                        <div className="product-placeholder">
                          <FileText size={18} />
                        </div>

                        <div>
                          <strong>{inspection.product}</strong>
                          <span>{inspection.quantity}</span>
                        </div>
                      </div>
                    </td>

                    <td className="inspection-id">
                      {inspection.id}
                    </td>

                    <td>
                      <div className="date-info">
                        <span>{inspection.date}</span>
                        <span>{inspection.time}</span>
                      </div>
                    </td>

                    <td>
                      <span className={`status-badge ${config.className}`}>
                        {config.icon}
                        {inspection.status}
                      </span>
                    </td>

                    <td>
                      <strong
                        className={`score ${
                          inspection.status === "Failed"
                            ? "score-red"
                            : inspection.status === "Warning"
                            ? "score-orange"
                            : "score-green"
                        }`}
                      >
                        {inspection.score}
                      </strong>
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

        {/* Pagination */}
        <div className="pagination">

          <span>
            Showing 1 to {filteredInspections.length} of 128 results
          </span>

          <div className="page-controls">
            <button>
              <ChevronLeft size={17} />
            </button>

            <button className="active-page">1</button>
            <button>2</button>
            <button>3</button>
            <span>...</span>
            <button>26</button>

            <button>
              <ChevronRight size={17} />
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}

export default History;