import { BrowserRouter, Routes, Route } from "react-router-dom";

import DashboardLayout from "./layouts/DashboardLayout";
import Dashboard from "./pages/Dashboard";
import NewInspection from "./pages/NewInspection";
import History from "./pages/History";
import Reports from "./pages/Reports";

function App() {
  return (
    <BrowserRouter>
      <DashboardLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new-inspection" element={<NewInspection />} />
          <Route path="/history" element={<History />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </DashboardLayout>
    </BrowserRouter>
  );
}

export default App;