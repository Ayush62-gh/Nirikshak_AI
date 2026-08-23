import React, { useState } from "react";
import { Bell } from "lucide-react";

function NotificationSettings() {
  const [inspectionNotifications, setInspectionNotifications] = useState(true);
  const [emailAlerts, setEmailAlerts] = useState(true);

  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm">

      {/* Header */}
      <div className="mb-3 flex items-center gap-3">

        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-50 text-teal-600">
          <Bell size={19} />
        </div>

        <div>
          <h2 className="text-[17px] font-bold text-[#17233d]">
            Notification Preferences
          </h2>

          <p className="text-xs text-[#7890ae]">
            Choose how you receive inspection updates.
          </p>
        </div>

      </div>

      {/* Inspection Notifications */}
      <ToggleRow
        title="Inspection Notifications"
        description="Receive alerts when inspections are completed."
        enabled={inspectionNotifications}
        onToggle={() =>
          setInspectionNotifications(!inspectionNotifications)
        }
      />

      {/* Email Alerts */}
      <ToggleRow
        title="Email Alerts"
        description="Receive important compliance updates via email."
        enabled={emailAlerts}
        onToggle={() => setEmailAlerts(!emailAlerts)}
      />

    </section>
  );
}


/* Toggle Component */
function ToggleRow({
  title,
  description,
  enabled,
  onToggle,
}) {
  return (
    <div className="flex items-center justify-between gap-5 py-4">

      <div>
        <p className="text-sm font-semibold text-[#17233d]">
          {title}
        </p>

        <p className="mt-1 text-xs leading-5 text-[#7890ae]">
          {description}
        </p>
      </div>

     <div
  onClick={onToggle}
  style={{
    width: "44px",
    height: "24px",
    minWidth: "44px",
    backgroundColor: enabled ? "#12988d" : "#cbd5e1",
    borderRadius: "999px",
    position: "relative",
    flexShrink: 0,
    cursor: "pointer",
    transition: "background-color 0.2s ease",
  }}
>
  <span
    style={{
      position: "absolute",
      top: "4px",
      left: enabled ? "24px" : "4px",
      width: "16px",
      height: "16px",
      backgroundColor: "white",
      borderRadius: "50%",
      transition: "left 0.2s ease",
    }}
  />
</div>

    </div>
  );
}

export default NotificationSettings;