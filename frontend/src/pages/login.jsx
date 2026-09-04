import React from "react";
import LoginBrandPanel from "../components/login/LoginBrandPanel";
import LoginForm from "../components/login/LoginForm";

function Login() {
  return (
    <main className="h-screen overflow-hidden bg-white">
    <div className="flex h-screen w-full">
        {/* Left Branding + Inspection Visual */}
        <LoginBrandPanel />

        {/* Right Login Form */}
        <LoginForm />

      </div>
    </main>
  );
}

export default Login;
