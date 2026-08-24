import React, { useState } from "react";

const rules = [
  {
    id: "LM-001",
    title: "Mandatory Declarations",
    category: "Mandatory",
    description:
      "All required product declarations must be clearly visible and accurate on the package.",
    authority: "Legal Metrology",
    updated: "Aug 20, 2026",
  },
  {
    id: "LM-002",
    title: "Maximum Retail Price (MRP)",
    category: "Mandatory",
    description:
      "The maximum retail price must be displayed clearly and must not be misleading.",
    authority: "Legal Metrology",
    updated: "Aug 18, 2026",
  },
  {
    id: "LM-003",
    title: "Net Quantity Declaration",
    category: "Standards",
    description:
      "Net quantity must be declared using the appropriate unit and remain clearly readable.",
    authority: "Legal Metrology",
    updated: "Aug 15, 2026",
  },
  {
    id: "LM-004",
    title: "Package Readability",
    category: "Best Practices",
    description:
      "Mandatory information should remain legible, visible and easy to identify.",
    authority: "Packaging Standards",
    updated: "Aug 12, 2026",
  },
  {
    id: "LM-005",
    title: "Manufacturer Details",
    category: "Mandatory",
    description:
      "Manufacturer or importer details should be provided according to applicable requirements.",
    authority: "Legal Metrology",
    updated: "Aug 10, 2026",
  },
];

const categories = [
  { name: "Legal Metrology", count: 24 },
  { name: "Packaging Standards", count: 12 },
  { name: "Consumer Protection", count: 8 },
  { name: "Product Labelling", count: 16 },
];

function RulesGuidelines() {
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("All Rules");

  const filteredRules = rules.filter((rule) => {
    const searchMatch =
      rule.title.toLowerCase().includes(search.toLowerCase()) ||
      rule.id.toLowerCase().includes(search.toLowerCase()) ||
      rule.description.toLowerCase().includes(search.toLowerCase());

    const tabMatch =
      activeTab === "All Rules" || rule.category === activeTab;

    return searchMatch && tabMatch;
  });

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-8 lg:px-10">

      {/* HEADER */}
      <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Rules & Guidelines
          </h1>
          <p className="mt-2 text-base text-slate-500">
            Stay updated with the latest compliance rules and regulatory
            requirements.
          </p>
        </div>

        <button className="rounded-lg bg-teal-600 px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-teal-700">
          ↓ &nbsp; Download All
        </button>
      </div>

      {/* SEARCH + FILTERS */}
      <div className="mb-6 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:flex-row">

        <div className="flex flex-1 items-center rounded-xl border border-slate-200 px-4 py-3">
          <span className="mr-3 text-xl text-slate-400">⌕</span>

          <input
            type="text"
            placeholder="Search rules, regulations or keywords..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-transparent text-slate-700 outline-none placeholder:text-slate-400"
          />
        </div>

        <button className="rounded-xl border border-slate-200 px-5 py-3 text-slate-600 hover:bg-slate-50">
          All Categories ▾
        </button>

        <button className="rounded-xl border border-slate-200 px-5 py-3 text-slate-600 hover:bg-slate-50">
          Recently Updated ▾
        </button>
      </div>

      {/* STAT CARDS */}
      <div className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

        <StatCard
          icon="▤"
          title="Total Rules"
          value="48"
          subtitle="Active regulations"
          iconClass="bg-blue-100 text-blue-600"
        />

        <StatCard
          icon="✓"
          title="Mandatory"
          value="24"
          subtitle="Must comply"
          iconClass="bg-emerald-100 text-emerald-600"
        />

        <StatCard
          icon="!"
          title="Updated"
          value="8"
          subtitle="This month"
          iconClass="bg-orange-100 text-orange-600"
        />

        <StatCard
          icon="◈"
          title="Categories"
          value="4"
          subtitle="Regulatory areas"
          iconClass="bg-purple-100 text-purple-600"
        />
      </div>

      {/* MAIN GRID */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_330px]">

        {/* LEFT */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">

          {/* TABS */}
          <div className="flex flex-wrap gap-2 border-b border-slate-200 px-5 pt-5">
            {["All Rules", "Mandatory", "Standards", "Best Practices"].map(
              (tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`rounded-t-lg px-4 py-3 text-sm font-semibold transition ${
                    activeTab === tab
                      ? "border-b-2 border-teal-600 text-teal-700"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  {tab}
                </button>
              )
            )}
          </div>

          {/* RULES */}
          <div className="divide-y divide-slate-100">
            {filteredRules.length > 0 ? (
              filteredRules.map((rule) => (
                <div
                  key={rule.id}
                  className="flex flex-col gap-4 p-5 transition hover:bg-slate-50 lg:flex-row lg:items-start"
                >
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-xl text-blue-600">
                    ▤
                  </div>

                  <div className="min-w-0 flex-1">

                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="text-lg font-bold text-slate-800">
                        {rule.title}
                      </h3>

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${
                          rule.category === "Mandatory"
                            ? "bg-red-50 text-red-600"
                            : rule.category === "Standards"
                            ? "bg-blue-50 text-blue-600"
                            : "bg-orange-50 text-orange-600"
                        }`}
                      >
                        {rule.category}
                      </span>
                    </div>

                    <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
                      {rule.description}
                    </p>

                    <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-400">
                      <span>{rule.id}</span>
                      <span>{rule.authority}</span>
                      <span>Updated {rule.updated}</span>
                    </div>
                  </div>

                  <button className="shrink-0 self-start rounded-lg border border-teal-600 px-4 py-2 text-sm font-semibold text-teal-700 transition hover:bg-teal-50">
                    View Details →
                  </button>
                </div>
              ))
            ) : (
              <div className="p-10 text-center text-slate-500">
                No rules found matching your search.
              </div>
            )}
          </div>
        </div>

        {/* RIGHT SIDEBAR */}
        <div className="space-y-6">

          {/* CATEGORIES */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold text-slate-800">
              Regulatory Categories
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Browse rules by compliance area.
            </p>

            <div className="mt-5 space-y-2">
              {categories.map((category) => (
                <div
                  key={category.name}
                  className="flex items-center justify-between rounded-xl p-3 transition hover:bg-slate-50"
                >
                  <div>
                    <p className="font-semibold text-slate-700">
                      {category.name}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      {category.count} rules
                    </p>
                  </div>

                  <span className="text-teal-600">→</span>
                </div>
              ))}
            </div>
          </div>

          {/* COMPLIANCE CARD */}
          <div className="rounded-2xl bg-teal-50 p-6">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-white text-xl text-teal-600">
              ✓
            </div>

            <h2 className="text-xl font-bold text-slate-800">
              Stay Compliant
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-600">
              Keep your inspection process aligned with the latest regulatory
              requirements.
            </p>

            <button className="mt-5 font-semibold text-teal-700 hover:text-teal-800">
              View Latest Updates →
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, title, value, subtitle, iconClass }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div
        className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-full text-xl font-bold ${iconClass}`}
      >
        {icon}
      </div>

      <div>
        <p className="text-sm text-slate-500">{title}</p>
        <h2 className="mt-1 text-2xl font-bold text-slate-900">{value}</h2>
        <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
      </div>
    </div>
  );
}

export default RulesGuidelines;