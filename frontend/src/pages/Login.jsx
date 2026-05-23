import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Mail, Lock, Eye, EyeOff } from "lucide-react";
import API from "../api";
import GoogleLoginButton from "../components/GoogleLoginButton";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await API.post("/login", { email, password });
      localStorage.setItem("isLoggedIn", "true");
      localStorage.setItem("user", JSON.stringify(res.data.user));
      navigate("/dashboard");
    } catch (err) {
      alert(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-8"
      style={{ background: "#F5F0EB" }}
    >
      <div
        className="w-full max-w-md bg-white p-10 space-y-8"
        style={{
          borderRadius: "20px",
          boxShadow: "0 8px 32px rgba(44, 95, 138, 0.1)",
        }}
      >
        <div className="text-center">
          <h1
            className="text-3xl mb-2"
            style={{
              fontFamily: "var(--font-display)",
              color: "var(--aura-text-primary)",
            }}
          >
            AuraChat
          </h1>
        </div>

        <div>
          <h2
            className="text-3xl mb-2"
            style={{ color: "var(--aura-text-primary)" }}
          >
            Welcome back {"\uD83D\uDC4B"}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label
              htmlFor="email"
              className="block text-sm"
              style={{ color: "var(--aura-text-primary)" }}
            >
              Email Address
            </label>
            <div className="relative">
              <Mail
                className="absolute left-4 top-1/2 -translate-y-1/2"
                size={20}
                style={{ color: "var(--aura-text-secondary)" }}
              />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full pl-12 pr-4 focus:outline-none focus:ring-2 transition-all"
                style={{
                  borderRadius: "12px",
                  border: "1px solid #D0DCE8",
                  height: "48px",
                  color: "var(--aura-text-primary)",
                  background: "white",
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = "#4A90D9";
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = "#D0DCE8";
                }}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label
                htmlFor="password"
                className="block text-sm"
                style={{ color: "var(--aura-text-primary)" }}
              >
                Password
              </label>
              <button
                type="button"
                onClick={() =>
                  alert("Forgot password flow is not implemented yet")
                }
                className="text-sm hover:underline"
                style={{ color: "#4A90D9" }}
              >
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <Lock
                className="absolute left-4 top-1/2 -translate-y-1/2"
                size={20}
                style={{ color: "var(--aura-text-secondary)" }}
              />
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="........"
                className="w-full pl-12 pr-12 focus:outline-none focus:ring-2 transition-all"
                style={{
                  borderRadius: "12px",
                  border: "1px solid #D0DCE8",
                  height: "48px",
                  color: "var(--aura-text-primary)",
                  background: "white",
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = "#4A90D9";
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = "#D0DCE8";
                }}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2"
                style={{ color: "var(--aura-text-secondary)" }}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="w-full text-white transition-all hover:opacity-90"
            style={{
              background: "#4A90D9",
              borderRadius: "12px",
              height: "52px",
              boxShadow: "0 4px 12px rgba(74, 144, 217, 0.3)",
            }}
            disabled={loading}
          >
            {loading ? "Signing In..." : "Sign In"}
          </button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div
              className="w-full border-t"
              style={{ borderColor: "#D0DCE8" }}
            ></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span
              className="px-4 bg-white"
              style={{ color: "var(--aura-text-secondary)" }}
            >
              or continue with
            </span>
          </div>
        </div>

        <div className="flex justify-center">
          <GoogleLoginButton />
        </div>

        <div className="text-center text-sm">
          <span style={{ color: "var(--aura-text-secondary)" }}>
            Don&apos;t have an account?{" "}
          </span>
          <button
            type="button"
            onClick={() => navigate("/signup")}
            className="hover:underline"
            style={{ color: "#4A90D9" }}
          >
            Create one
          </button>
        </div>
      </div>
    </div>
  );
}
