import { useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { Menu, X } from "lucide-react";

function DashboardLayout({ children }) {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="h-screen overflow-hidden bg-[#F8FAFC]">
      <Sidebar
        isMobileOpen={mobileSidebarOpen}
        onClose={() => setMobileSidebarOpen(false)}
      />

      {/* Mobile Overlay */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      <main className="min-w-0 h-screen overflow-y-auto md:ml-64">
        {/* Mobile Header */}
        <div className="sticky top-0 z-30 flex h-14 items-center border-b border-[#E2E8F0] bg-white px-4 md:hidden">
          <button
            onClick={() => setMobileSidebarOpen(true)}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-[#12355B] transition hover:bg-[#F8FAFC]"
            aria-label="Open menu"
          >
            <Menu size={24} />
          </button>

          <div className="ml-3 text-base font-bold text-[#12355B]">
            NIRIKSHAK
          </div>
        </div>

        <Navbar />

        {children}
      </main>
    </div>
  );
}

export default DashboardLayout;