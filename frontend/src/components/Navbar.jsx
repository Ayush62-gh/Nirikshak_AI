import { Bell, ChevronDown, Sun } from "lucide-react";
import { useLocation } from "react-router-dom";
function getGreeting() {
  const hour = new Date().getHours();

  if (hour < 12) {
    return "Good Morning";
  }

  if (hour < 17) {
    return "Good Afternoon";
  }

  return "Good Evening";
}

function Navbar() {
    const location = useLocation();
    const isDashboard = location.pathname === "/";
  return (
    <header className="flex min-h-24 items-center justify-between border-b border-[#E2E8F0] bg-white px-8">
      {/* Greeting - Dashboard only */}
       {isDashboard && (
        <div className="flex items-center gap-4">
    
       {/* Sun Icon */}
         <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#F0FDFA] text-[#0F766E]">
        <Sun size={28} strokeWidth={1.8} />
        </div>

        <div>
        <h1 className="text-2xl font-bold text-[#172033]">
            {getGreeting()}, Inspector
        </h1>

        <p className="mt-1 text-sm text-[#64748B]">
        Here's your compliance overview for today.
      </p>
    </div>

  </div>
)}

      {/* Right Side */}
      <div className="ml-auto flex items-center gap-5">

        {/* Notification */}
        <button
          className="relative flex h-10 w-10 items-center justify-center rounded-xl text-[#12355B] transition hover:bg-[#F8FAFC]"
          aria-label="Notifications"
        >
          <Bell size={23} strokeWidth={1.8} />

          <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#0F766E] text-[9px] font-bold text-white">
            3
          </span>
        </button>

        {/* Divider */}
        <div className="h-9 w-px bg-[#E2E8F0]" />

        {/* Profile */}
        <button className="flex items-center gap-3 rounded-xl px-2 py-1.5 transition hover:bg-[#F8FAFC]">

          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#12355B] text-sm font-semibold text-white">
            IN
          </div>

          <p className="text-sm font-semibold text-[#172033]">
            Inspector
          </p>

          <ChevronDown
            size={17}
            className="text-[#64748B]"
            strokeWidth={1.8}
          />
        </button>

      </div>
    </header>
  );
}

export default Navbar;