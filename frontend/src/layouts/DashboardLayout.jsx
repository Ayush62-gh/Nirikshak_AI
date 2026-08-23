import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";

function DashboardLayout({ children }) {
  return (
    <div className="h-screen overflow-hidden bg-[#F8FAFC]">
      <Sidebar />

      <main className="min-w-0 flex-1 ml-64 h-screen overflow-y-auto">
        <Navbar />

        {children}
      </main>
    </div>
  );
}

export default DashboardLayout;