import { useState } from "react";
import API from "../api";
import { useNavigate, Link } from "react-router-dom";
import GoogleLoginButton from "../components/GoogleLoginButton";

export default function Login() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSignupPrompt, setShowSignupPrompt] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async () => {
    setLoading(true);
    try {
      const res = await API.post("/login", { identifier, password });
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("user", JSON.stringify(res.data.user));
      navigate("/chat");
    } catch (err) {
      alert(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-tr from-[#232946] via-[#393e46] to-[#18181b]">
      <div className="flex w-full max-w-5xl bg-[#232946]/80 rounded-lg shadow-lg overflow-hidden">
        {/* Left: Branding and Info */}
        <div className="hidden md:flex flex-col w-1/2 p-10 text-white bg-gradient-to-br from-[#18181b] via-[#232946] to-[#393e46]">
          <h1 className="text-3xl font-bold mb-6 tracking-wide">AuraChat</h1>
        </div>
        {/* Right: Login Form or Signup Prompt */}
        <div className="w-full md:w-1/2 bg-[#232946] p-10 flex flex-col justify-center">
          {showSignupPrompt ? (
            <div className="flex flex-col items-center justify-center h-full">
              <h2 className="text-2xl font-bold mb-4 text-gray-900">
                Don't have an account?
              </h2>
              <p className="mb-6 text-gray-600 text-sm">
                Sign up to get started with your free account.
              </p>
              <button
                className="w-full bg-gradient-to-r from-[#6a8dff] to-[#a259ff] hover:from-[#5a7be0] hover:to-[#8e47d6] text-white py-2 rounded mb-4 font-semibold transition-colors"
                onClick={() => navigate("/signup")}
              >
                Go to Signup
              </button>
              <button
                className="text-[#e4acfc] hover:underline text-sm"
                onClick={() => setShowSignupPrompt(false)}
              >
                Back to Login
              </button>
            </div>
          ) : (
            <>
              <h2 className="text-2xl font-bold mb-2 text-gray-100">Sign in</h2>
              <p className="mb-6 text-gray-300 text-sm">
                Welcome back! Please sign in to your account
              </p>
              <label className="block mb-2 text-sm font-medium text-gray-200">
                Username or Email*
              </label>
              <input
                className="w-full mb-4 p-2 border rounded bg-[#232946] text-white focus:outline-none focus:ring-2 focus:ring-[#e4acfc]"
                placeholder="Enter your username or email"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
              />
              <label className="block mb-2 text-sm font-medium text-gray-200">
                Password*
              </label>
              <input
                type="password"
                className="w-full mb-6 p-2 border rounded bg-[#232946] text-white focus:outline-none focus:ring-2 focus:ring-[#e4acfc]"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                className="w-full bg-gradient-to-r from-[#6a8dff] to-[#a259ff] hover:from-[#5a7be0] hover:to-[#8e47d6] text-white py-2 rounded mb-4 font-semibold transition-all duration-200 cursor-pointer transform hover:scale-105 hover:shadow-lg"
                onClick={handleLogin}
                disabled={loading}
              >
                {loading ? "Logging in..." : "Login"}
              </button>
              <div className="flex items-center my-4">
                <div className="flex-grow h-px bg-gray-300" />
                <span className="mx-2 text-gray-400 text-xs">or</span>
                <div className="flex-grow h-px bg-gray-300" />
              </div>
              <div className="mb-4">
                <GoogleLoginButton />
              </div>
              <div className="text-center text-xs text-gray-500 mb-2">
                Don't have an account?{" "}
                <button
                  className="text-[#e4acfc] font-medium hover:font-bold hover:text-[#e4acfc] hover:underline cursor-pointer transition-all duration-200"
                  onClick={() => navigate("/signup")}
                >
                  Sign up
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
