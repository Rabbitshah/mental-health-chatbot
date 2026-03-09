import { useEffect, useState, createElement } from "react";
import {
  Camera,
  Mail,
  Lock,
  Globe,
  Bell,
  Moon,
  Download,
  Trash2,
  AlertTriangle,
  Check,
  HelpCircle,
} from "lucide-react";
import { motion } from "motion/react";
import Sidebar from "../components/Sidebar";

export default function ManageProfile() {
  const [darkMode, setDarkMode] = useState(false);
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("Jane Doe");
  const [email, setEmail] = useState("jane@example.com");

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        if (user?.name) setFullName(user.name);
        if (user?.email) setEmail(user.email);
      } catch {
        // Keep defaults for malformed local payload.
      }
    }
  }, []);

  const handlePasswordChange = () => {
    if (newPassword === confirmPassword) {
      alert("Password changed successfully!");
      setShowPasswordForm(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } else {
      alert("Passwords do not match");
    }
  };

  const handleDataExport = () => {
    alert("Your data export will be emailed to you within 24 hours.");
  };

  const handleDeleteHistory = () => {
    if (
      confirm(
        "Are you sure you want to delete all conversation history? This cannot be undone.",
      )
    ) {
      alert("Conversation history deleted.");
    }
  };

  const handleDeleteAccount = () => {
    if (
      confirm(
        "Are you absolutely sure? This will permanently delete your account and all data. This action cannot be undone.",
      )
    ) {
      alert(
        "Account deletion initiated. You will receive a confirmation email.",
      );
    }
  };

  const initials =
    fullName
      .split(" ")
      .filter(Boolean)
      .map((part) => part[0]?.toUpperCase())
      .slice(0, 2)
      .join("") || "JD";

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <main
        className="flex-1 overflow-y-auto"
        style={{ background: "#F7FAFD" }}
      >
        <header
          className="px-8 py-4 bg-white flex items-center justify-between"
          style={{
            boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
            height: "64px",
          }}
        >
          <h2 className="text-xl" style={{ color: "var(--aura-text-primary)" }}>
            Settings
          </h2>
          <div className="flex items-center gap-4">
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-all">
              <Bell size={20} style={{ color: "var(--aura-text-secondary)" }} />
            </button>
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-all">
              <HelpCircle
                size={20}
                style={{ color: "var(--aura-text-secondary)" }}
              />
            </button>
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs cursor-pointer"
              style={{ background: "#4A90D9", color: "white" }}
            >
              {initials}
            </div>
          </div>
        </header>

        <div className="p-8">
          <div className="max-w-4xl mx-auto space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <h1
                className="text-4xl mb-2"
                style={{ color: "var(--aura-text-primary)" }}
              >
                Settings
              </h1>
              <p
                className="text-lg"
                style={{ color: "var(--aura-text-secondary)" }}
              >
                Manage your account and preferences
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="bg-white p-8"
              style={{
                borderRadius: "20px",
                boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
              }}
            >
              <h2
                className="text-2xl mb-6"
                style={{ color: "var(--aura-text-primary)" }}
              >
                Profile
              </h2>

              <div className="flex items-start gap-8">
                <div className="relative group cursor-pointer">
                  <div
                    className="w-20 h-20 rounded-full flex items-center justify-center text-2xl"
                    style={{ background: "#4A90D9", color: "white" }}
                  >
                    {initials}
                  </div>
                  <div className="absolute inset-0 rounded-full bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <Camera size={24} className="text-white" />
                  </div>
                </div>

                <div className="flex-1 space-y-4">
                  <div>
                    <label
                      className="block text-sm mb-2"
                      style={{ color: "var(--aura-text-secondary)" }}
                    >
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                      style={{
                        borderRadius: "12px",
                        border: "1px solid #D0DCE8",
                        color: "var(--aura-text-primary)",
                      }}
                    />
                  </div>

                  <div>
                    <label
                      className="block text-sm mb-2"
                      style={{ color: "var(--aura-text-secondary)" }}
                    >
                      Email Address
                    </label>
                    <div className="flex items-center gap-3">
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="flex-1 px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                        style={{
                          borderRadius: "12px",
                          border: "1px solid #D0DCE8",
                          color: "var(--aura-text-primary)",
                        }}
                      />
                      <div
                        className="flex items-center gap-2 px-3 py-2 text-sm"
                        style={{ color: "#7EC8A4" }}
                      >
                        <Check size={16} />
                        Verified
                      </div>
                    </div>
                  </div>

                  <div
                    className="text-sm"
                    style={{ color: "var(--aura-text-secondary)" }}
                  >
                    Member since March 1, 2026
                  </div>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="bg-white p-8"
              style={{
                borderRadius: "20px",
                boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
              }}
            >
              <h2
                className="text-2xl mb-6"
                style={{ color: "var(--aura-text-primary)" }}
              >
                Account
              </h2>

              <div className="space-y-4">
                <div>
                  <button
                    onClick={() => setShowPasswordForm(!showPasswordForm)}
                    className="flex items-center gap-3 text-left w-full p-4 hover:bg-gray-50 transition-all"
                    style={{ borderRadius: "12px" }}
                  >
                    <Lock size={20} style={{ color: "#4A90D9" }} />
                    <div className="flex-1">
                      <div style={{ color: "var(--aura-text-primary)" }}>
                        Change Password
                      </div>
                      <div
                        className="text-sm"
                        style={{ color: "var(--aura-text-secondary)" }}
                      >
                        Update your password regularly for security
                      </div>
                    </div>
                  </button>

                  {showPasswordForm && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="mt-4 pl-11 space-y-3"
                    >
                      <input
                        type="password"
                        placeholder="Current password"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="w-full px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                        style={{
                          borderRadius: "12px",
                          border: "1px solid #D0DCE8",
                          color: "var(--aura-text-primary)",
                        }}
                      />
                      <input
                        type="password"
                        placeholder="New password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                        style={{
                          borderRadius: "12px",
                          border: "1px solid #D0DCE8",
                          color: "var(--aura-text-primary)",
                        }}
                      />
                      <input
                        type="password"
                        placeholder="Confirm new password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="w-full px-4 py-3 focus:outline-none focus:ring-2 transition-all"
                        style={{
                          borderRadius: "12px",
                          border: "1px solid #D0DCE8",
                          color: "var(--aura-text-primary)",
                        }}
                      />
                      <div className="flex gap-3">
                        <button
                          onClick={handlePasswordChange}
                          className="px-6 py-2 text-white hover:opacity-90 transition-all"
                          style={{ background: "#4A90D9", borderRadius: "8px" }}
                        >
                          Update Password
                        </button>
                        <button
                          onClick={() => setShowPasswordForm(false)}
                          className="px-6 py-2 hover:bg-gray-100 transition-all"
                          style={{
                            borderRadius: "8px",
                            color: "var(--aura-text-secondary)",
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </motion.div>
                  )}
                </div>

                <div
                  className="flex items-center gap-3 p-4"
                  style={{ borderRadius: "12px", background: "#F7FAFD" }}
                >
                  <div className="w-10 h-10 rounded-full flex items-center justify-center bg-white">
                    <svg width="20" height="20" viewBox="0 0 24 24">
                      <path
                        fill="#4285F4"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="#34A853"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="#EA4335"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <div style={{ color: "var(--aura-text-primary)" }}>
                      Google
                    </div>
                    <div
                      className="text-sm"
                      style={{ color: "var(--aura-text-secondary)" }}
                    >
                      Connected
                    </div>
                  </div>
                  <button
                    className="text-sm hover:underline"
                    style={{ color: "#E07C6B" }}
                  >
                    Disconnect
                  </button>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="bg-white p-8"
              style={{
                borderRadius: "20px",
                boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
              }}
            >
              <h2
                className="text-2xl mb-6"
                style={{ color: "var(--aura-text-primary)" }}
              >
                Preferences
              </h2>

              <div className="space-y-4">
                <SettingToggle
                  icon={Moon}
                  label="Dark Mode"
                  description="Switch to dark theme"
                  checked={darkMode}
                  onChange={setDarkMode}
                />
                <SettingToggle
                  icon={Mail}
                  label="Email Notifications"
                  description="Receive updates via email"
                  checked={emailNotifications}
                  onChange={setEmailNotifications}
                />
                <SettingToggle
                  icon={Bell}
                  label="Push Notifications"
                  description="Get notified about important updates"
                  checked={pushNotifications}
                  onChange={setPushNotifications}
                />

                <div className="flex items-center gap-3 p-4">
                  <Globe size={20} style={{ color: "#4A90D9" }} />
                  <div className="flex-1">
                    <div style={{ color: "var(--aura-text-primary)" }}>
                      Language
                    </div>
                    <div
                      className="text-sm"
                      style={{ color: "var(--aura-text-secondary)" }}
                    >
                      Choose your preferred language
                    </div>
                  </div>
                  <select
                    className="px-4 py-2 focus:outline-none focus:ring-2 transition-all"
                    style={{
                      borderRadius: "8px",
                      border: "1px solid #D0DCE8",
                      color: "var(--aura-text-primary)",
                    }}
                  >
                    <option>English</option>
                    <option>Spanish</option>
                    <option>French</option>
                    <option>German</option>
                  </select>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              className="bg-white p-8"
              style={{
                borderRadius: "20px",
                boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
              }}
            >
              <h2
                className="text-2xl mb-6"
                style={{ color: "var(--aura-text-primary)" }}
              >
                Privacy & Data
              </h2>

              <div className="space-y-4">
                <button
                  onClick={handleDataExport}
                  className="flex items-center gap-3 w-full p-4 hover:bg-gray-50 transition-all text-left"
                  style={{ borderRadius: "12px" }}
                >
                  <Download size={20} style={{ color: "#4A90D9" }} />
                  <div className="flex-1">
                    <div style={{ color: "var(--aura-text-primary)" }}>
                      Export My Data
                    </div>
                    <div
                      className="text-sm"
                      style={{ color: "var(--aura-text-secondary)" }}
                    >
                      Download a copy of your conversations and data
                    </div>
                  </div>
                </button>

                <button
                  onClick={handleDeleteHistory}
                  className="flex items-center gap-3 w-full p-4 hover:bg-gray-50 transition-all text-left"
                  style={{ borderRadius: "12px" }}
                >
                  <Trash2 size={20} style={{ color: "#F5A962" }} />
                  <div className="flex-1">
                    <div style={{ color: "var(--aura-text-primary)" }}>
                      Delete Conversation History
                    </div>
                    <div
                      className="text-sm"
                      style={{ color: "var(--aura-text-secondary)" }}
                    >
                      Permanently remove all past conversations
                    </div>
                  </div>
                </button>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.5 }}
              className="p-8"
              style={{
                borderRadius: "20px",
                border: "2px solid #E07C6B",
                background: "rgba(224, 124, 107, 0.05)",
              }}
            >
              <div className="flex items-start gap-3 mb-6">
                <AlertTriangle size={24} style={{ color: "#E07C6B" }} />
                <div>
                  <h2 className="text-2xl mb-1" style={{ color: "#E07C6B" }}>
                    Danger Zone
                  </h2>
                  <p
                    className="text-sm"
                    style={{ color: "var(--aura-text-secondary)" }}
                  >
                    These actions are permanent and cannot be undone
                  </p>
                </div>
              </div>

              <button
                onClick={handleDeleteAccount}
                className="px-6 py-3 text-white hover:opacity-90 transition-all"
                style={{ background: "#E07C6B", borderRadius: "12px" }}
              >
                Delete My Account
              </button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.6 }}
              className="bg-white p-8"
              style={{
                borderRadius: "20px",
                boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
              }}
            >
              <h2
                className="text-2xl mb-6"
                style={{ color: "var(--aura-text-primary)" }}
              >
                About
              </h2>

              <div className="space-y-3">
                <div className="flex items-center justify-between py-2">
                  <span style={{ color: "var(--aura-text-secondary)" }}>
                    App Version
                  </span>
                  <span
                    className="px-3 py-1 text-sm"
                    style={{
                      background: "#F7FAFD",
                      borderRadius: "8px",
                      color: "var(--aura-text-primary)",
                      fontFamily: "monospace",
                    }}
                  >
                    v1.0.0
                  </span>
                </div>
                <button
                  className="text-sm hover:underline"
                  style={{ color: "#4A90D9" }}
                >
                  Privacy Policy
                </button>
                <br />
                <button
                  className="text-sm hover:underline"
                  style={{ color: "#4A90D9" }}
                >
                  Terms of Service
                </button>
                <br />
                <button
                  className="text-sm hover:underline"
                  style={{ color: "#4A90D9" }}
                >
                  Help & Support
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}

function SettingToggle({ icon, label, description, checked, onChange }) {
  return (
    <div className="flex items-center gap-3 p-4">
      {createElement(icon, { size: 20, style: { color: "#4A90D9" } })}
      <div className="flex-1">
        <div style={{ color: "var(--aura-text-primary)" }}>{label}</div>
        <div
          className="text-sm"
          style={{ color: "var(--aura-text-secondary)" }}
        >
          {description}
        </div>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className="relative w-12 h-6 rounded-full transition-all"
        style={{ background: checked ? "#4A90D9" : "#D0DCE8" }}
      >
        <motion.div
          className="absolute top-1 w-4 h-4 bg-white rounded-full"
          animate={{ left: checked ? "28px" : "4px" }}
          transition={{ type: "spring", stiffness: 500, damping: 30 }}
        />
      </button>
    </div>
  );
}
