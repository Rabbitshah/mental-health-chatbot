import { useState, useEffect } from "react";
import { updateProfile } from "../api";
import { useNavigate } from "react-router-dom";

export default function ManageProfile() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [bio, setBio] = useState("");
  const [botPersonality, setBotPersonality] = useState(50);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [activeSection, setActiveSection] = useState("general");
  const navigate = useNavigate();

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        const nameParts = (user.name || "").split(" ");
        setFirstName(nameParts[0] || "");
        setLastName(nameParts.slice(1).join(" ") || "");
        setEmail(user.email || "");
        setBio(user.bio || "");
      } catch {}
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    try {
      const res = await updateProfile({
        name: `${firstName} ${lastName}`.trim(),
        email,
        bio,
        bot_personality: botPersonality,
      });
      setMsg("Profile updated!");
      localStorage.setItem("user", JSON.stringify(res.data.user));
    } catch (err) {
      setMsg(err.response?.data?.detail || "Update failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  const getUserInitials = () => {
    const first = firstName.charAt(0).toUpperCase();
    const last = lastName.charAt(0).toUpperCase();
    return first + (last || "");
  };

  const getUserName = () => {
    if (firstName || lastName) {
      return `${firstName} ${lastName}`.trim();
    }
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        return user.name || "User";
      } catch {}
    }
    return "User";
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-200 flex flex-col">
      {/* Top Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg
            className="w-6 h-6 text-blue-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
          <span className="font-bold text-xl text-white">MindfulBot</span>
        </div>
        <nav className="flex items-center gap-6">
          <button
            onClick={() => navigate("/dashboard")}
            className="text-gray-400 hover:text-white transition"
          >
            Dashboard
          </button>
          <button className="text-blue-400 font-medium">Settings</button>
          <button className="text-gray-400 hover:text-white transition">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.21 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
          </button>
          <div className="w-8 h-8 rounded-full bg-orange-400 border-2 border-white flex items-center justify-center">
            <span className="text-white font-bold text-sm">
              {getUserInitials() || "U"}
            </span>
          </div>
        </nav>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
          {/* User Profile Section */}
          <div className="p-6 border-b border-gray-700">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 rounded-full bg-orange-400 border-2 border-white flex items-center justify-center">
                <span className="text-white font-bold">
                  {getUserInitials() || "U"}
                </span>
              </div>
              <div>
                <div className="font-semibold text-white">{getUserName()}</div>
                <div className="text-sm text-gray-400">Free Plan</div>
              </div>
            </div>
          </div>

          {/* Navigation Menu */}
          <div className="flex-1 overflow-y-auto p-4">
            <nav className="space-y-1">
              <button
                onClick={() => setActiveSection("general")}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  activeSection === "general"
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-gray-700"
                }`}
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
                <span className="font-medium">General</span>
              </button>
              <button
                onClick={() => setActiveSection("chat")}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  activeSection === "chat"
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-gray-700"
                }`}
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
                <span className="font-medium">Chat Preferences</span>
              </button>
              <button
                onClick={() => setActiveSection("notifications")}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  activeSection === "notifications"
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-gray-700"
                }`}
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.21 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <span className="font-medium">Notifications</span>
              </button>
              <button
                onClick={() => setActiveSection("privacy")}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  activeSection === "privacy"
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-gray-700"
                }`}
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
                <span className="font-medium">Privacy & Security</span>
              </button>
              <button
                onClick={() => setActiveSection("goals")}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  activeSection === "goals"
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-gray-700"
                }`}
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"
                  />
                </svg>
                <span className="font-medium">My Goals</span>
              </button>
            </nav>
          </div>

          {/* Sign Out Button */}
          <div className="p-4 border-t border-gray-700">
            <button
              onClick={handleSignOut}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-700 transition"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
              <span className="font-medium">Sign Out</span>
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-4xl mx-auto">
            {activeSection === "general" && (
              <form onSubmit={handleSubmit}>
                <h1 className="text-3xl font-bold text-white mb-2">
                  General Settings
                </h1>
                <p className="text-gray-400 mb-8">
                  Manage your personal details and account configuration.
                </p>

                {/* Profile Photo Section */}
                <div className="bg-gray-800 rounded-lg p-6 mb-6 border border-gray-700">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="w-24 h-24 rounded-full bg-orange-400 border-2 border-white flex items-center justify-center flex-shrink-0">
                        <span className="text-white font-bold text-2xl">
                          {getUserInitials() || "U"}
                        </span>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white mb-1">
                          Profile Photo
                        </h3>
                        <p className="text-sm text-gray-400 mb-3">
                          This will be displayed on your profile.
                        </p>
                        <div className="flex items-center gap-4">
                          <button
                            type="button"
                            className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                          >
                            Update
                          </button>
                          <button
                            type="button"
                            className="text-red-400 hover:text-red-300 text-sm font-medium"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition"
                    >
                      Upload New
                    </button>
                  </div>
                </div>

                {/* Personal Information Section */}
                <div className="bg-gray-800 rounded-lg p-6 mb-6 border border-gray-700">
                  <h3 className="text-lg font-semibold text-white mb-4">
                    Personal Information
                  </h3>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        First Name
                      </label>
                      <input
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Alex"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Last Name
                      </label>
                      <input
                        type="text"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Morgan"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                        <svg
                          className="w-5 h-5 text-gray-400"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                          />
                        </svg>
                      </div>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full pl-12 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="alex.morgan@email.com"
                      />
                    </div>
                  </div>
                </div>

                {/* Bio & Focus Areas Section */}
                <div className="bg-gray-800 rounded-lg p-6 mb-6 border border-gray-700">
                  <h3 className="text-lg font-semibold text-white mb-4">
                    Bio & Focus Areas
                  </h3>
                  <textarea
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    rows={4}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    placeholder="Tell us a bit about your journey..."
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    Brief description for your journal header.
                  </p>
                </div>

                {/* Chat Experience Section */}
                <div className="bg-gray-800 rounded-lg p-6 mb-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">
                      Chat Experience
                    </h3>
                    <button
                      type="button"
                      className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                    >
                      Reset to Default
                    </button>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      Bot Personality
                    </label>
                    <div className="flex items-center gap-4">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={botPersonality}
                        onChange={(e) => setBotPersonality(parseInt(e.target.value))}
                        className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                      />
                      <span className="text-blue-400 font-medium min-w-[100px] text-right">
                        {botPersonality < 33
                          ? "Professional"
                          : botPersonality < 67
                          ? "Empathetic"
                          : "Friendly"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Save Button */}
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold disabled:opacity-50 transition"
                  >
                    {loading ? "Saving..." : "Save Changes"}
                  </button>
                </div>

                {msg && (
                  <div
                    className={`mt-4 text-center text-sm ${
                      msg.includes("updated") ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {msg}
                  </div>
                )}
              </form>
            )}

            {activeSection !== "general" && (
              <div className="text-center py-12">
                <p className="text-gray-400">
                  {activeSection === "chat" && "Chat Preferences coming soon..."}
                  {activeSection === "notifications" &&
                    "Notifications settings coming soon..."}
                  {activeSection === "privacy" &&
                    "Privacy & Security settings coming soon..."}
                  {activeSection === "goals" && "My Goals coming soon..."}
                </p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
