import React, { useState } from "react";
import jsPDF from "jspdf";
import confetti from "canvas-confetti";
const rules = [
  {
    id: "LM-RULE-NAME-004",
    title: "Generic / Commodity Name Declaration Check",
    category: "Mandatory",
    targetField: "productName",
    severity: "HIGH",
    description:
      "Checks whether the generic or common name of the commodity is declared on the principal display panel.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011",
    remediation:
      "Declare the generic or common name of the commodity on the principal display panel.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-MFGNAME-005",
    title: "Manufacturer or Packer Name Declaration Check",
    category: "Mandatory",
    targetField: "manufacturerName",
    severity: "CRITICAL",
    description:
      "Checks whether the name of the Manufacturer or Packer is clearly declared on the package label.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011",
    remediation:
      "Declare the name of the Manufacturer or Packer clearly on the package label.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-MFGADDR-006",
    title: "Manufacturer or Packer Address Declaration Check",
    category: "Mandatory",
    targetField: "manufacturerAddress",
    severity: "HIGH",
    description:
      "Checks whether the complete address of the Manufacturer or Packer is declared on the package label.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011",
    remediation:
      "Declare complete address of Manufacturer/Packer including premises, city, state and pincode.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-NETQTY-002",
    title: "Net Quantity Declaration Check",
    category: "Standards",
    targetField: "netQuantity",
    severity: "HIGH",
    description:
      "Checks whether Net Quantity is declared using appropriate standard metric units.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 6(1)(c), Rule 11 & Rule 12, Legal Metrology (Packaged Commodities) Rules, 2011",
    remediation:
      "Declare Net Quantity in standard metric units such as g/kg, ml/L, m/cm, square metre or number/count.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-MRP-001",
    title: "Maximum Retail Price (MRP) Declaration Check",
    category: "Mandatory",
    targetField: "mrp",
    severity: "CRITICAL",
    description:
      "Checks the presence, numeric representation and statutory presentation of the Maximum Retail Price.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 6(1)(e) & Rule 2(m), Legal Metrology (Packaged Commodities) Rules, 2011",
    remediation:
      "Declare MRP in statutory format including the applicable tax inclusion statement.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-DATE-007",
    title: "Month and Year of Packing / Manufacture Check",
    category: "Mandatory",
    targetField: "monthOfPacking",
    severity: "HIGH",
    description:
      "Checks whether the month and year of packing or manufacture are completely and correctly declared.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011",
    remediation:
      "Declare Month and Year of packing/manufacture in standard format such as 07/2026 or July 2026.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-CARE-008",
    title: "Consumer Care Details Declaration Check",
    category: "Mandatory",
    targetField: "consumerCare",
    severity: "HIGH",
    description:
      "Checks whether Consumer Care contact details such as name, address, telephone number and email are declared.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 6(1)(h) & Rule 6(2), Legal Metrology (Packaged Commodities) Rules, 2011",
    remediation:
      "Declare name, complete address, telephone number and email address of the Consumer Care officer or office.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-COO-009",
    title: "Country of Origin Declaration Check",
    category: "Mandatory",
    targetField: "countryOfOrigin",
    severity: "CRITICAL",
    description:
      "Checks Country of Origin declaration for imported packaged commodities.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 6(1)(ab), Legal Metrology (Packaged Commodities) Rules, 2011 (as amended)",
    remediation:
      "Declare Country of Origin prominently on imported package labels.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-IMP-003",
    title: "Importer Name & Address Check for Foreign Commodities",
    category: "Mandatory",
    targetField: "importerName",
    severity: "CRITICAL",
    description:
      "Checks whether the Importer name and address are declared on imported packaged commodities.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011",
    remediation:
      "Declare the name and complete Indian office address of the Importer on imported package labels.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-EXP-011",
    title: "Best Before / Expiry Date Declaration Check",
    category: "Standards",
    targetField: "expiryDate",
    severity: "HIGH",
    description:
      "Checks Best Before or Expiry Date declarations for applicable perishable product categories.",
    authority: "Legal Metrology / FSSAI",
    legalReference:
      "Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011 & FSSAI Packaging Guidelines",
    remediation:
      "Declare Best Before period or Expiry Date on applicable perishable package labels.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-USP-010",
    title: "Unit Sale Price (USP) Declaration Check",
    category: "Standards",
    targetField: "unitSalePrice",
    severity: "HIGH",
    description:
      "Checks Unit Sale Price declaration on applicable retail packaged commodities.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 6(11), Legal Metrology (Packaged Commodities) Rules, 2011 (2021 DoCA Amendment)",
    remediation:
      "Declare Unit Sale Price in standard format alongside MRP on package labels.",
    updated: "Rule Engine",
  },
  {
    id: "LM-RULE-FONT-012",
    title: "Font Size & Readability Analysis Check",
    category: "Best Practices",
    targetField: "fontSizeMm",
    severity: "HIGH",
    description:
      "Checks the physical font height of mandatory declarations against statutory readability requirements.",
    authority: "Legal Metrology",
    legalReference:
      "Rule 7 & Rule 9, Legal Metrology (Packaged Commodities) Rules, 2011",
    remediation:
      "Ensure font height of mandatory declarations meets minimum statutory millimeter requirements under Rule 7 & 9.",
    updated: "Rule Engine",
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
  const [sortOrder, setSortOrder] = useState("Recently Updated");
  const [selectedRule, setSelectedRule] = useState(null);
const handleDownloadAll = async () => {
  const doc = new jsPDF();
  const logo = new Image();
  logo.src = "/nirikshak-icon-2.png";

  await new Promise((resolve, reject) => {
  logo.onload = resolve;
  logo.onerror = reject;
});
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  const margin = 18;
  const contentWidth = pageWidth - margin * 2;

  const colors = {
    navy: [18, 53, 91],
    teal: [13, 148, 136],
    tealLight: [240, 253, 250],
    text: [30, 41, 59],
    muted: [100, 116, 139],
    border: [226, 232, 240],
    light: [248, 250, 252],
    white: [255, 255, 255],
    red: [220, 38, 38],
    redLight: [254, 242, 242],
    orange: [234, 88, 12],
    orangeLight: [255, 247, 237],
    blue: [37, 99, 235],
    blueLight: [239, 246, 255],
  };

  let y = 18;

  const addFooter = () => {
    const totalPages = doc.internal.getNumberOfPages();

    for (let page = 1; page <= totalPages; page++) {
      doc.setPage(page);

      doc.setDrawColor(...colors.border);
      doc.line(margin, pageHeight - 15, pageWidth - margin, pageHeight - 15);

      doc.setFontSize(8);
      doc.setFont(undefined, "normal");
      doc.setTextColor(...colors.muted);

      doc.text(
        "Generated by NIRIKSHAK — Prototype System",
        margin,
        pageHeight - 8
      );

      doc.text(
        `Page ${page} of ${totalPages}`,
        pageWidth - margin,
        pageHeight - 8,
        { align: "right" }
      );
    }
  };

  const addNewPage = () => {
    doc.addPage();
    y = 16;

    doc.setFillColor(...colors.navy);
    doc.rect(0, 0, pageWidth, 9, "F");

    doc.setFontSize(8);
    doc.setFont(undefined, "bold");
    doc.setTextColor(...colors.white);

    doc.text(
      "NIRIKSHAK  |  RULES & GUIDELINES",
      margin,
      6
    );
  };

  const checkSpace = (height) => {
    if (y + height > pageHeight - 22) {
      addNewPage();
    }
  };

  // =========================
  // COVER / HEADER
  // =========================

  doc.setFillColor(...colors.navy);
  doc.rect(0, 0, pageWidth, 40, "F");
  doc.addImage(
  logo,
  "PNG",
  margin,
  7,
  25,
  25
);

  doc.setFontSize(19);
  doc.setTextColor(203, 213, 225);
  doc.setFont(undefined, "bold");
  doc.text("NIRIKSHAK", margin + 28, 17);

  doc.setFontSize(8.5);
  doc.setFont(undefined, "normal");
  doc.setTextColor(203, 213, 225);
  doc.text(
    "Smart Compliance. Fair Trade.",
    margin + 28,
    24
  );

  y = 51;

  doc.setFontSize(20);
  doc.setFont(undefined, "bold");
  doc.setTextColor(...colors.navy);
  doc.text("Rules & Guidelines", margin, y);

  y += 6;

  doc.setFontSize(9);
  doc.setFont(undefined, "normal");
  doc.setTextColor(...colors.muted);

  doc.text(
    "Compliance rules currently available in the application",
    margin,
    y
  );

  y += 6;
  y += 8;

  // =========================
  // SUMMARY
  // =========================

  const summaryHeight = 27;

  doc.setFillColor(...colors.light);
  doc.setDrawColor(...colors.border);

  doc.roundedRect(
    margin,
    y,
    contentWidth,
    summaryHeight,
    4,
    4,
    "FD"
  );

  doc.setFontSize(8);
  doc.setFont(undefined, "bold");
  doc.setTextColor(...colors.muted);

  doc.text(
    "RULE ENGINE SUMMARY",
    margin + 7,
    y + 7
  );

  doc.setFontSize(16);
  doc.setTextColor(...colors.navy);
  doc.text("12", margin + 7, y + 18);

  doc.setFontSize(8);
  doc.setFont(undefined, "normal");
  doc.setTextColor(...colors.muted);

  doc.text(
    "Active rules",
    margin + 7,
    y + 24
  );

  const summaryItems = [
    ["8", "Mandatory"],
    ["3", "Standards"],
    ["1", "Best Practices"],
  ];

  summaryItems.forEach((item, index) => {
    const x = margin + 55 + index * 42;

    doc.setFontSize(12);
    doc.setFont(undefined, "bold");
    doc.setTextColor(...colors.text);
    doc.text(item[0], x, y + 16);

    doc.setFontSize(7);
    doc.setFont(undefined, "normal");
    doc.setTextColor(...colors.muted);

    doc.text(item[1], x, y + 23);
  });

  y += summaryHeight + 9;

  // =========================
  // RULE CARD
  // =========================
const drawRuleCard = (rule, index) => {
  const padding = 8;
  const innerWidth = contentWidth - padding * 2;

  // ---------- TEXT WRAPPING ----------
  const titleLines = doc.splitTextToSize(
    rule.title,
    contentWidth - 70
  );

  const legalLines = doc.splitTextToSize(
    rule.legalReference,
    innerWidth
  );

  const descriptionLines = doc.splitTextToSize(
    rule.description,
    innerWidth
  );

  const remediationLines = doc.splitTextToSize(
    rule.remediation,
    innerWidth
  );

  // ---------- HEIGHT CALCULATION ----------
  // Increased line spacing because font sizes are larger
  const titleHeight = titleLines.length * 5.8;
  const legalHeight = legalLines.length * 4.8;
  const descriptionHeight = descriptionLines.length * 4.8;
  const remediationHeight = remediationLines.length * 4.8;

  /*
   * Calculate the card height from the actual content.
   * This avoids reserving unnecessary empty space.
   */
  const cardHeight =
    padding +
    12 +
    titleHeight +
    5 +
    5 +
    legalHeight +
    4 +
    5 +
    descriptionHeight +
    4 +
    5 +
    remediationHeight +
    padding;

  // ---------- PAGE BREAK ----------
  checkSpace(cardHeight + 4);

  // ---------- CARD ----------
  doc.setFillColor(...colors.white);
  doc.setDrawColor(...colors.border);

  doc.roundedRect(
    margin,
    y,
    contentWidth,
    cardHeight,
    3,
    3,
    "FD"
  );

  // Left accent
  doc.setFillColor(...colors.teal);

  doc.roundedRect(
    margin,
    y,
    2,
    cardHeight,
    1,
    1,
    "F"
  );

  // ---------- RULE NUMBER ----------
  doc.setFillColor(...colors.tealLight);

  doc.roundedRect(
    margin + padding,
    y + padding,
    13,
    13,
    3,
    3,
    "F"
  );

  doc.setFontSize(8.5);
  doc.setFont(undefined, "bold");
  doc.setTextColor(...colors.teal);

  doc.text(
    String(index + 1).padStart(2, "0"),
    margin + padding + 3.2,
    y + padding + 8.7
  );

  // ---------- TITLE ----------
  doc.setFontSize(12);
  doc.setFont(undefined, "bold");
  doc.setTextColor(...colors.text);

  doc.text(
    titleLines,
    margin + padding + 18,
    y + padding + 6
  );

  // ---------- SEVERITY ----------
  const severity =
    rule.severity === "CRITICAL"
      ? {
          bg: colors.redLight,
          text: colors.red,
        }
      : rule.severity === "HIGH"
      ? {
          bg: colors.orangeLight,
          text: colors.orange,
        }
      : {
          bg: colors.blueLight,
          text: colors.blue,
        };

  const badgeX = pageWidth - margin - 30;

  doc.setFillColor(...severity.bg);

  doc.roundedRect(
    badgeX,
    y + padding,
    30,
    8,
    4,
    4,
    "F"
  );

  doc.setFontSize(7);
  doc.setFont(undefined, "bold");
  doc.setTextColor(...severity.text);

  doc.text(
    rule.severity,
    badgeX + 15,
    y + padding + 5.5,
    {
      align: "center",
    }
  );

  // ---------- CONTENT START ----------
  let currentY =
    y +
    padding +
    16 +
    titleHeight;

  // ---------- ID + FIELD ----------
  doc.setFontSize(8);
  doc.setFont(undefined, "normal");
  doc.setTextColor(...colors.muted);

  doc.text(
    `ID: ${rule.id}`,
    margin + padding,
    currentY
  );

  doc.text(
    `Field: ${rule.targetField}`,
    margin + 75,
    currentY
  );

  currentY += 7;

  // ---------- LEGAL REFERENCE ----------
  doc.setFontSize(7.8);
  doc.setFont(undefined, "bold");
  doc.setTextColor(...colors.teal);

  doc.text(
    "LEGAL REFERENCE",
    margin + padding,
    currentY
  );

  currentY += 4.5;

  doc.setFont(undefined, "normal");
  doc.setTextColor(...colors.text);

  doc.text(
    legalLines,
    margin + padding,
    currentY
  );

  currentY += legalHeight + 3;

  // ---------- DESCRIPTION ----------
  doc.setFont(undefined, "bold");
  doc.setTextColor(...colors.teal);

  doc.text(
    "DESCRIPTION",
    margin + padding,
    currentY
  );

  currentY += 4.5;

  doc.setFont(undefined, "normal");
  doc.setTextColor(...colors.text);

  doc.text(
    descriptionLines,
    margin + padding,
    currentY
  );

  currentY += descriptionHeight + 3;

  // ---------- REMEDIATION ----------
  doc.setFont(undefined, "bold");
  doc.setTextColor(...colors.teal);

  doc.text(
    "REMEDIATION",
    margin + padding,
    currentY
  );

  currentY += 4.5;

  doc.setFont(undefined, "normal");
  doc.setTextColor(...colors.text);

  doc.text(
    remediationLines,
    margin + padding,
    currentY
  );

  // ---------- NEXT CARD ----------
  // Small gap between cards
  y += cardHeight + 4;
};
  // =========================
  // ALL RULES
  // =========================

  rules.forEach((rule, index) => {
    drawRuleCard(rule, index);
  });

  // Footer
  addFooter();

  // Download
  doc.save("NIRIKSHAK-Rules-Guidelines.pdf");

  // 🎉 Success effect
  confetti({
    particleCount: 120,
    spread: 70,
    origin: {
      x: 0.5,
      y: 0.7,
    },
  });
};
    const filteredRules = rules
  .filter((rule) => { 
    const searchMatch =
    rule.title.toLowerCase().includes(search.toLowerCase()) ||
    rule.id.toLowerCase().includes(search.toLowerCase()) ||
    rule.description.toLowerCase().includes(search.toLowerCase()) ||
    rule.targetField.toLowerCase().includes(search.toLowerCase()) ||
    rule.severity.toLowerCase().includes(search.toLowerCase());

    const tabMatch =
      activeTab === "All Rules" || rule.category === activeTab;

    return searchMatch && tabMatch;
  })
  .sort((a, b) => {
    const dateA = new Date(a.updated);
    const dateB = new Date(b.updated);

    return sortOrder === "Recently Updated"
      ? dateB - dateA
      : dateA - dateB;
  });
  return (
    <div className="min-h-screen bg-[#E3F5F2] px-6 py-8 lg:px-10">


      {/* HEADER */}
      <div className="mb-7 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Rules & Guidelines
          </h1>
          <p className="mt-2 text-base text-slate-500">
            Stay updated with the latest compliance rules and regulatory
            requirements.
          </p>
        </div>
        <div className="flex justify-end mt-11">
        <button
          onClick={handleDownloadAll}
          className="rounded-lg bg-teal-600 px-4 py-2 font-semibold text-white shadow-sm transition hover:bg-teal-700"
        >
          ↓ &nbsp; Download All
        </button>
        </div>
      </div>

      {/* SEARCH + FILTERS */}
      <div className="mb-6 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-[#F1FAF8] p-4 shadow-sm lg:flex-row">

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

<div className="relative">
  <select
    value={sortOrder}
    onChange={(e) => setSortOrder(e.target.value)}
    className="appearance-none rounded-xl border border-slate-200 bg-white px-5 py-3 pr-10 text-slate-600 outline-none transition hover:bg-slate-50 focus:border-teal-500"
  >
    <option value="Recently Updated">Recently Updated</option>
    <option value="Oldest First">Oldest First</option>
  </select>

  <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-slate-400">
    ▾
  </span>
</div>
      </div>

      {/* STAT CARDS */}
      <div className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 bg-[#F1FAF8]">

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
        <div className="rounded-2xl border border-slate-200 bg-[#F1FAF8] shadow-sm">

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
                  <button
                       onClick={() => setSelectedRule(rule)}
                        className="shrink-0 self-start rounded-lg border border-teal-600 px-4 py-2 text-sm font-semibold text-teal-700 transition hover:bg-teal-50"
                  >
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
          <div className="rounded-2xl border border-slate-200 bg-[#F1FAF8] p-6 shadow-sm">
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
      {selectedRule && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          // className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 pt-10"
          onClick={() => setSelectedRule(null)}
         >
        <div
          // className="w-full max-w-2xl rounded-2xl bg-white shadow-xl"
          // className="my-auto w-full max-w-2xl rounded-2xl bg-white shadow-xl"
          className="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl bg-white shadow-xl"
          onClick={(e) => e.stopPropagation()}
        >
    {/* Header */}
      <div className="flex items-start justify-between border-b border-slate-200 p-6">
        <div>
          <h2 className="text-xl font-bold text-slate-800">
            {selectedRule.title}
          </h2>

          <div className="mt-2 flex gap-2">
            <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-700">
              {selectedRule.id}
            </span>

            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              {selectedRule.category}
            </span>
          </div>
        </div>

        <button
          onClick={() => setSelectedRule(null)}
          className="text-2xl leading-none text-slate-400 transition hover:text-slate-700"
        >
          ×
        </button>
      </div>
       {/* Details */}
       {/* Details */}
<div className="flex-1 space-y-5 overflow-y-auto p-6 scrollbar-hide">
{/* <div className="space-y-5 p-6"> */}
  <div>
    <p className="mb-1 text-sm font-semibold text-slate-500">
      Description
    </p>
    <p className="text-sm leading-6 text-slate-700">
      {selectedRule.description}
    </p>
  </div>

  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
    <div>
      <p className="mb-1 text-sm font-semibold text-slate-500">
        Severity
      </p>
      <span
        className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
          selectedRule.severity === "CRITICAL"
            ? "bg-red-50 text-red-600"
            : selectedRule.severity === "HIGH"
            ? "bg-orange-50 text-orange-600"
            : "bg-blue-50 text-blue-600"
        }`}
      >
        {selectedRule.severity}
      </span>
    </div>

    <div>
      <p className="mb-1 text-sm font-semibold text-slate-500">
        Target Field
      </p>
      <p className="text-sm font-medium text-slate-700">
        {selectedRule.targetField}
      </p>
    </div>
  </div>

  <div>
    <p className="mb-1 text-sm font-semibold text-slate-500">
      Legal Reference
    </p>
    <p className="text-sm leading-6 text-slate-700">
      {selectedRule.legalReference}
    </p>
  </div>

  <div>
    <p className="mb-1 text-sm font-semibold text-slate-500">
      Authority
    </p>
    <p className="text-sm text-slate-700">
      {selectedRule.authority}
    </p>
  </div>

  <div>
    <p className="mb-1 text-sm font-semibold text-slate-500">
      Remediation
    </p>
    <p className="text-sm leading-6 text-slate-700">
      {selectedRule.remediation}
    </p>
  </div>

  <div>
    <p className="mb-1 text-sm font-semibold text-slate-500">
      Source
    </p>
    <p className="text-sm text-slate-700">
      Rule Engine
    </p>
  </div>
</div>
      {/* Footer */}
      <div className="flex justify-end border-t border-slate-200 p-4">
        <button
          onClick={() => setSelectedRule(null)}
          className="rounded-lg bg-teal-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-teal-700"
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