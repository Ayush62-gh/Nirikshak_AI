import { useState, useEffect, useRef } from "react";
import {
  Bell,
  ChevronDown,
  Sun,
  Settings,
  LogOut,
  AlertTriangle,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getScans } from "../services/api";
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
    const [notifications, setNotifications] = useState([]);
    const [notificationsOpen, setNotificationsOpen] = useState(false);
    const profileRef = useRef(null);
    const notificationRef = useRef(null);

   useEffect(() => {
    function handleClickOutside(event) {
      if (
        profileRef.current &&
        !profileRef.current.contains(event.target)
      ) {
        setProfileOpen(false);
      }
      if (
      notificationRef.current &&
      !notificationRef.current.contains(event.target)
      ) {
      setNotificationsOpen(false);
    }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  useEffect(() => {
  const fetchNotifications = async () => {
    try {
      const data = await getScans(1, 20);

      const problematicScans = (data.scans || [])
        .filter(
          (scan) =>
            scan.compliance?.status === "NON_COMPLIANT" ||
            scan.compliance?.status === "PARTIAL"
        )
        .slice(0, 5);

      setNotifications(problematicScans);
     } catch (error) {
      console.error("Failed to fetch notifications:", error);
      setNotifications([]);
     }
     };

      fetchNotifications();
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
    // <header className="flex min-h-24 items-center justify-between border-b border-[#E2E8F0] bg-white px-8">
    return (
  <header
    className={
      isDashboard
        ? "flex min-h-24 items-center justify-between border-b border-[#E2E8F0] bg-white px-8"
        : "relative h-0"
    }
  >
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
      {/* <div className="ml-auto flex items-center gap-5"> */}
      <div
       className={
       isDashboard
       ? "ml-auto flex items-center gap-5"
        : "absolute right-8 top-4 z-50 flex items-center gap-5"
  }
>
      <div ref={notificationRef} className="relative">
        {/* Notification */}
        <button
           onClick={() => setNotificationsOpen((prev) => !prev)}
          className="relative flex h-10 w-10 items-center justify-center rounded-xl text-[#12355B] transition hover:bg-[#F8FAFC]"
           aria-label="Notifications"
        >
          <Bell size={23} strokeWidth={1.8} />

         {notifications.length > 0 && (
         <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#0F766E] text-[9px] font-bold text-white">
          {notifications.length}
        </span>
      )}
        </button>

{/* Notifications Dropdown */}
{notificationsOpen && (
  <div className="absolute right-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-xl border border-[#E2E8F0] bg-white shadow-lg">
    <div className="border-b border-[#E2E8F0] px-4 py-3">
      <h3 className="text-sm font-bold text-[#172033]">
        Notifications
      </h3>
    </div>

    {notifications.length === 0 ? (
      <div className="px-4 py-8 text-center">
        <Bell
          size={24}
          className="mx-auto mb-2 text-[#94A3B8]"
        />

        <p className="text-sm font-medium text-[#64748B]">
          No new notifications
        </p>
      </div>
    ) : (
      <div className="max-h-80 overflow-y-auto">
        {notifications.map((scan) => {
          const isNonCompliant =
            scan.compliance?.status === "NON_COMPLIANT";

          return (
            <div
              key={scan.scan_id}
              className="border-b border-[#F1F5F9] px-4 py-3 hover:bg-[#F8FAFC]"
            >
              <div className="flex items-start gap-3">
                <div
                  className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                    isNonCompliant
                      ? "bg-red-50 text-red-600"
                      : "bg-amber-50 text-amber-600"
                  }`}
                >
                  <AlertTriangle size={16} />
                </div>

                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[#172033]">
                    {isNonCompliant
                      ? "Non-compliant inspection"
                      : "Inspection needs review"}
                  </p>

                  <p className="mt-0.5 truncate text-xs text-[#64748B]">
                    {scan.product?.product_name ||
                      scan.product?.name ||
                      "Product inspection"}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    )}
  </div>
)}
</div>
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