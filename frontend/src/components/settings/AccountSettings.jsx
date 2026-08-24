import React from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, UserRoundCog } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

function AccountSettings() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleSignOut = () => {
    logout();
    navigate("/login");
  };

  return (
    <section className="mt-5 flex flex-col justify-between gap-4 rounded-2xl border border-red-100 bg-white p-6 shadow-sm sm:flex-row sm:items-center">

      <div className="flex items-center gap-4">

        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-500">
          <UserRoundCog size={20} />
        </div>

        <div>
          <h2 className="text-[17px] font-bold text-[#17233d]">
            Account
          </h2>

          <p className="mt-1 text-xs text-[#7890ae]">
            Manage your account session and access.
          </p>
        </div>

      </div>

      <button
        type="button"
        onClick={handleSignOut}
        className="flex h-10 items-center justify-center gap-2 rounded-lg border border-red-300 bg-white px-5 text-sm font-semibold text-red-500 transition hover:bg-red-50 cursor-pointer"
      >
        <LogOut size={17} />
        Sign Out
      </button>

    </section>
  );
}

export default AccountSettings;