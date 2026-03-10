import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Mail, Lock, User, Eye, EyeOff } from "lucide-react";
import API from "../api";
import GoogleLoginButton from "../components/GoogleLoginButton";

export default function Signup() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const getPasswordStrength = () => {
    if (!password) return 0;
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    return strength;
  };

  const passwordStrength = getPasswordStrength();
  const strengthColors = ["#E07C6B", "#E07C6B", "#F5A962", "#7EC8A4"];
  const strengthLabels = ["Weak", "Weak", "Good", "Strong"];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      const usernameBase = fullName
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "");
      const fallback = email
        .split("@")[0]
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_");
      const username = usernameBase || fallback || "user";

      await API.post("/signup", {
        email,
        password,
        name: fullName,
        username,
      });

      const res = await API.post("/login", { identifier: email, password });
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("user", JSON.stringify(res.data.user));
      navigate("/dashboard");
    } catch (err) {
      alert(err.response?.data?.detail || "Signup failed");
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
        className="w-full max-w-md bg-white p-10 space-y-6"
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
            Create your account
          </h2>
          <p
            className="text-sm"
            style={{ color: "var(--aura-text-secondary)" }}
          >
            Free forever. No credit card needed.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label
              htmlFor="fullName"
              className="block text-sm"
              style={{ color: "var(--aura-text-primary)" }}
            >
              Full Name
            </label>
            <div className="relative">
              <User
                className="absolute left-4 top-1/2 -translate-y-1/2"
                size={20}
                style={{ color: "var(--aura-text-secondary)" }}
              />
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Doe"
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
            <label
              htmlFor="password"
              className="block text-sm"
              style={{ color: "var(--aura-text-primary)" }}
            >
              Password
            </label>
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
                placeholder="••••••••"
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

            {password && (
              <div className="space-y-1">
                <div className="flex gap-1">
                  {[0, 1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="h-1 flex-1 rounded-full transition-all"
                      style={{
                        background:
                          i < passwordStrength
                            ? strengthColors[passwordStrength - 1]
                            : "#E0E0E0",
                      }}
                    />
                  ))}
                </div>
                <p
                  className="text-xs"
                  style={{ color: "var(--aura-text-secondary)" }}
                >
                  Password strength:{" "}
                  {strengthLabels[passwordStrength - 1] || "Too weak"}
                </p>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label
              htmlFor="confirmPassword"
              className="block text-sm"
              style={{ color: "var(--aura-text-primary)" }}
            >
              Confirm Password
            </label>
            <div className="relative">
              <Lock
                className="absolute left-4 top-1/2 -translate-y-1/2"
                size={20}
                style={{ color: "var(--aura-text-secondary)" }}
              />
              <input
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
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
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2"
                style={{ color: "var(--aura-text-secondary)" }}
              >
                {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
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
              marginTop: "24px",
            }}
            disabled={loading}
          >
            {loading ? "Creating..." : "Create Account"}
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
            Already have an account?{" "}
          </span>
          <button
            type="button"
            onClick={() => navigate("/login")}
            className="hover:underline"
            style={{ color: "#4A90D9" }}
          >
            Sign in
          </button>
        </div>
      </div>
    </div>
  );
}
