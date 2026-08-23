import React from "react";

import ProfileSettings from "../components/settings/ProfileSettings";
import NotificationSettings from "../components/settings/NotificationSettings";
import InspectionSettings from "../components/settings/InspectionSettings";
import SecuritySettings from "../components/settings/SecuritySettings";
import SystemInformation from "../components/settings/SystemInformation";
import AccountSettings from "../components/settings/AccountSettings";

function Settings() {
  return (
    <div className="min-h-full bg-[#f5f8fc] px-6 py-6 lg:px-8">

      {/* Page Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#17233d]">
            Settings
          </h1>

          <p className="mt-1 text-base text-[#6680a3]">
            Manage your account and inspection preferences.
          </p>
        </div>
      </div>

      {/* Profile - Full Width */}
      <div className="mb-5">
        <ProfileSettings />
      </div>

      {/* Notification + Inspection */}
<div
  style={{
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: "20px",
  }}
>
  <NotificationSettings />
  <InspectionSettings />
</div>

{/* Security + System */}
<div
  style={{
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: "20px",
    marginTop: "20px",
  }}
>
  <SecuritySettings />
  <SystemInformation />
</div>

      {/* Account - Full Width */}
      <div className="mt-5">
        <AccountSettings />
      </div>

    </div>
  );
}

export default Settings;