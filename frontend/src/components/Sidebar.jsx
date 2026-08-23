import {
  LayoutDashboard,
  Camera,
  History,
  FileText,
  BookOpen,
  Settings,
} from "lucide-react";
import { NavLink } from "react-router-dom";
const navigationItems = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    path: "/",
  },
  {
    label: "New Inspection",
    icon: Camera,
    path: "/new-inspection",
  },
  {
    label: "History",
    icon: History,
    path: "/history",
  },
  {
    label: "Reports",
    icon: FileText,
    path: "/reports",
  },
];
 const bottomItems = [
  {
    label: "Rules & Guidelines",
    icon: BookOpen,
    path: "/rules-guidelines",
  },
  {
    label: "Settings",
    icon: Settings,
    path: "/settings",
  },

];

function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-50 flex h-screen w-64 flex-col overflow-hidden bg-[#12355B] text-white">
      
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 text-2xl">
          ⚖
        </div>

        <div>
          <h1 className="text-xl font-bold tracking-tight">
            NIRIKSHAK AI
          </h1>

          <p className="text-xs text-white/70">
            Smart Compliance. Fair Trade.
          </p>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="mt-3 flex-1 px-4">
        <div className="space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.label}
                to={item.path}
                 className={({ isActive }) =>
              `flex w-full items-center gap-3 rounded-xl px-4 py-2 text-sm font-medium transition-all duration-200 ${
             isActive
                ? "bg-[#0F766E] text-white shadow-sm"
             : "text-white/80 hover:bg-white/10 hover:text-white"
             }`
             }
            >
            <Icon size={21} strokeWidth={1.8} />
            <span>{item.label}</span>
            </NavLink>
            );
          })}
        </div>

        {/* Divider */}
        <div className="my-3 border-t border-white/15" />

        {/* Bottom Navigation */}
        <div className="space-y-2">
          {bottomItems.map((item) => {
            const Icon = item.icon;

           return (
             <NavLink
             key={item.label}
             to={item.path}
              className={({ isActive }) =>
           `flex w-full items-center gap-4 rounded-xl px-4 py-3 text-sm font-medium transition ${
            isActive
              ? "bg-teal-600 text-white"
           : "text-white/80 hover:bg-white/10"
         }`
     }
  >
    <Icon size={21} strokeWidth={1.8} />
    <span>{item.label}</span>
  </NavLink>
);
          })}
        </div>
      </nav>

      {/* Trust Card */}
      <div className="mx-4 mb-4 rounded-2xl border border-white/15 bg-white/5 p-3.5">
        <div className="mb-3 text-2xl">🛡️</div>

        <h3 className="text-sm font-semibold">
          AI-Powered Compliance
        </h3>

        <p className="mt-1.5 text-xs leading-4.5 text-white/65">
          Accurate. Fast. Reliable.
          <br />
          Built for Legal Metrology
          <br />
          Inspections.
        </p>
      </div>
    </aside>
  );
}

export default Sidebar;