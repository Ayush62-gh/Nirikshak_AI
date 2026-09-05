import { BrowserRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";

import DashboardLayout from "./layouts/DashboardLayout";
import Dashboard from "./pages/Dashboard";
import NewInspection from "./pages/NewInspection";
import History from "./pages/History";
import Reports from "./pages/Reports";
import RulesGuidelines from "./pages/RulesGuidelines";
import Settings from "./pages/Settings";
import Login from "./pages/login";
import ForgotPassword from "./pages/ForgotPassword";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />

        {/* Protected Application */}
        <Route
          path="*"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route
                    path="/new-inspection"
                    element={<NewInspection />}
                  />
                  <Route path="/history" element={<History />} />
                  <Route path="/reports" element={<Reports />} />
                  <Route
                    path="/rules-guidelines"
                    element={<RulesGuidelines />}
                  />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;