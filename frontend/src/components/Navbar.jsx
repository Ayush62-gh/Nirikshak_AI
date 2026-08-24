import { useState, useEffect, useRef } from "react";
import {
  Bell,
  ChevronDown,
  Sun,
  Settings,
  LogOut,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
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
  const { logout } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();

    const isDashboard = location.pathname === "/";

    const [profileOpen, setProfileOpen] = useState(false);
    const profileRef = useRef(null);

   useEffect(() => {
    function handleClickOutside(event) {
      if (
        profileRef.current &&
        !profileRef.current.contains(event.target)
      ) {
        setProfileOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleSettings = () => {
    setProfileOpen(false);
    navigate("/settings");
  };

  const handleLogout = () => {
  setProfileOpen(false);
  logout();
  navigate("/login");
};
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
<div ref={profileRef} className="relative">

  <button
    onClick={() => setProfileOpen(!profileOpen)}
    className="flex items-center gap-3 rounded-xl px-2 py-1.5 transition hover:bg-[#F8FAFC]"
  >
    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#12355B] text-sm font-semibold text-white">
      IN
    </div>

    <p className="text-sm font-semibold text-[#172033]">
      Inspector
    </p>

    <ChevronDown
      size={17}
      className={`text-[#64748B] transition-transform duration-200 ${
        profileOpen ? "rotate-180" : ""
      }`}
      strokeWidth={1.8}
    />
  </button>

  {/* Dropdown */}
  {profileOpen && (
    <div className="absolute right-0 top-full z-50 mt-2 w-48 overflow-hidden rounded-xl border border-[#E2E8F0] bg-white shadow-lg">

      {/* Settings */}
      <button
        onClick={handleSettings}
        className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-medium text-[#172033] transition hover:bg-[#F8FAFC]"
      >
        <Settings
          size={18}
          className="text-[#0F766E]"
          strokeWidth={1.8}
        />

        <span>Settings</span>
      </button>

      {/* Divider */}
      <div className="h-px bg-[#E2E8F0]" />

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-medium text-[#D64545] transition hover:bg-red-50"
      >
        <LogOut
          size={18}
          strokeWidth={1.8}
        />

        <span>Logout</span>
      </button>

    </div>
  )}

</div>
</div>
    </header>
  );
}

export default Navbar;