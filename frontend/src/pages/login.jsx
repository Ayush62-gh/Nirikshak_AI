import React from "react";
import LoginBrandPanel from "../components/login/LoginBrandPanel";
import LoginForm from "../components/login/LoginForm";

function Login() {
  return (
    <main className="min-h-screen bg-white">
      <div className="flex min-h-screen w-full">
        {/* Left Branding + Inspection Visual */}
        <LoginBrandPanel />

        {/* Right Login Form */}
        <LoginForm />

      </div>
    </main>
  );
}

export default Login;

// function Login() {
//   return (
//     <div
//       style={{
//         minHeight: "100vh",
//         display: "flex",
//         alignItems: "center",
//         justifyContent: "center",
//         background: "#f0f8f7",
//       }}
//     >
//       <h1
//         style={{
//           fontSize: "48px",
//           fontWeight: "700",
//           color: "#173b63",
//         }}
//       >
//         NIRIKSHAK AI LOGIN
//       </h1>
//     </div>
//   );
// }

// export default Login;