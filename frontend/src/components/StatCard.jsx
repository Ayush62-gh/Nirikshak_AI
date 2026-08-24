import {
  ClipboardList,
  CheckCircle2,
  ShieldAlert,
  Hourglass,
} from "lucide-react";

const iconMap = {
  total: ClipboardList,
  compliant: CheckCircle2,
  nonCompliant: ShieldAlert,
  review: Hourglass,
};

const themeMap = {
  total: {
    iconBg: "bg-blue-100",
    iconColor: "text-blue-600",
    border: "border-blue-100",
  },
  compliant: {
    iconBg: "bg-emerald-100",
    iconColor: "text-emerald-600",
    border: "border-emerald-100",
  },
  nonCompliant: {
    iconBg: "bg-red-100",
    iconColor: "text-red-600",
    border: "border-red-100",
  },
  review: {
    iconBg: "bg-orange-100",
    iconColor: "text-orange-600",
    border: "border-orange-100",
  },
};

function StatCard({
  type,
  title,
  value,
  description,
  trend,
}) {
  const Icon = iconMap[type];
  const theme = themeMap[type];

  return (
    <div
      className={`rounded-2xl border ${theme.border} bg-white p-5 shadow-sm`}
    >
      <div className="flex items-center gap-4">
        
        {/* Icon */}
        <div
          className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-full ${theme.iconBg} ${theme.iconColor}`}
        >
          <Icon size={27} strokeWidth={1.8} />
        </div>

        {/* Content */}
        <div>
          <p className="text-sm font-semibold text-[#12355B]">
            {title}
          </p>

          <p className="mt-1 text-3xl font-bold text-[#172033]">
            {value}
          </p>
        </div>
      </div>

      {/* Bottom information */}
      <div className="mt-3 pl-[4.5rem] text-sm">
        {trend && (
          <span className="font-semibold text-emerald-600">
            {trend}
          </span>
        )}

        {description && (
          <span className="text-[#64748B]">
            {trend ? " " : ""}
            {description}
          </span>
        )}
      </div>
    </div>
  );
}

export default StatCard;