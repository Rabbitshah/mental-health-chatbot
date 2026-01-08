import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const [userName, setUserName] = useState("Alex");
  const [timeOfDay, setTimeOfDay] = useState("evening");
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) navigate("/login");

    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        if (user.name) {
          const nameParts = user.name.split(" ");
          setUserName(nameParts[0] || "User");
        }
      } catch {}
    }

    // Determine time of day
    const hour = new Date().getHours();
    if (hour < 12) setTimeOfDay("morning");
    else if (hour < 17) setTimeOfDay("afternoon");
    else setTimeOfDay("evening");
  }, [navigate]);

  const getUserInitials = () => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        const name = user.name || "";
        const parts = name.split(" ");
        return parts.length > 1
          ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
          : name.charAt(0).toUpperCase();
      } catch {}
    }
    return "U";
  };

  const handleSignOut = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-200 flex">
      {/* Left Sidebar */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col min-h-screen">
        {/* Branding */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
              <span className="text-white font-bold text-lg">M</span>
            </div>
            <div>
              <span className="font-bold text-xl text-white">MindfulBot</span>
              <p className="text-sm text-gray-400">Your Wellness Companion</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4">
          <div className="space-y-1">
            <button
              onClick={() => navigate("/dashboard")}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-blue-600 text-white transition"
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
                  d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                />
              </svg>
              <span className="font-medium">Home</span>
            </button>
            <button
              onClick={() => navigate("/chat")}
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
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              <span className="font-medium">Chat History</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-700 transition">
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
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
              <span className="font-medium">Mood Journal</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-700 transition">
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
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
              <span className="font-medium">Resources</span>
            </button>
            <button
              onClick={() => navigate("/profile")}
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
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <span className="font-medium">Settings</span>
            </button>
          </div>
        </nav>

        {/* Daily Tip */}
        <div className="p-4 border-t border-gray-700">
          <div className="bg-gray-700 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2 mb-2">
              <svg
                className="w-5 h-5 text-yellow-400"
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
              <span className="text-sm font-semibold text-white">Daily Tip</span>
            </div>
            <p className="text-sm text-gray-300">
              "Take a deep breath. Focus on the present moment, one step at a time."
            </p>
          </div>
          <button className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-3 rounded-lg font-medium transition flex items-center justify-center gap-2">
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
            Get Immediate Help
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-8">
          {/* Top Header */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">
                Good {timeOfDay}, {userName}.
              </h1>
              <p className="text-gray-400">
                Ready to check in? Remember, one step at a time.
              </p>
            </div>
            <div className="flex items-center gap-4">
              <button className="text-gray-400 hover:text-gray-300 transition">
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </button>
              <div className="w-10 h-10 rounded-full bg-orange-400 border-2 border-white flex items-center justify-center">
                <span className="text-white font-bold text-sm">
                  {getUserInitials()}
                </span>
              </div>
            </div>
          </div>

          {/* Current Status Card */}
          <div className="bg-gray-800 rounded-lg p-6 mb-6 border border-gray-700">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                CURRENT STATUS
              </span>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Start a New Session
            </h2>
            <p className="text-gray-400 mb-6">
              Continue where you left off or start a fresh topic today. I'm here to listen.
            </p>
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/chat")}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition flex items-center gap-2"
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
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
                Start Chatting
              </button>
              <button className="bg-gray-700 hover:bg-gray-600 text-gray-300 px-6 py-3 rounded-lg font-medium transition">
                Resume: Work Anxiety
              </button>
            </div>
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-3 gap-6 mb-6">
            {/* Recent Conversations - Takes 2 columns */}
            <div className="col-span-2">
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">
                    Recent Conversations
                  </h3>
                  <button className="text-gray-400 hover:text-gray-300">
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
                        d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                      />
                    </svg>
                  </button>
                </div>
                <div className="space-y-4">
                  {/* Conversation Card 1 */}
                  <div className="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition cursor-pointer flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      <div className="w-12 h-12 rounded-lg bg-gray-600 flex items-center justify-center">
                        <svg
                          className="w-6 h-6 text-gray-400"
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
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-white mb-1">
                          Managing Work Stress
                        </h4>
                        <p className="text-sm text-gray-400 mb-2">
                          We discussed breathing techniques for anxiety...
                        </p>
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-gray-500">2 hours ago</span>
                          <span className="px-2 py-1 bg-gray-600 text-gray-300 text-xs rounded-full">
                            Anxiety
                          </span>
                        </div>
                      </div>
                    </div>
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
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>

                  {/* Conversation Card 2 */}
                  <div className="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition cursor-pointer flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      <div className="w-12 h-12 rounded-lg bg-gray-600 flex items-center justify-center">
                        <svg
                          className="w-6 h-6 text-gray-400"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                          />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-white mb-1">
                          Sleep Improvement Plan
                        </h4>
                        <p className="text-sm text-gray-400 mb-2">
                          Review of last night's routine and sleep quality.
                        </p>
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-gray-500">Yesterday</span>
                          <span className="px-2 py-1 bg-gray-600 text-gray-300 text-xs rounded-full">
                            Health
                          </span>
                        </div>
                      </div>
                    </div>
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
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>

                  {/* Conversation Card 3 */}
                  <div className="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition cursor-pointer flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      <div className="w-12 h-12 rounded-lg bg-gray-600 flex items-center justify-center">
                        <svg
                          className="w-6 h-6 text-gray-400"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
                          />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-white mb-1">
                          Weekly Goal Setting
                        </h4>
                        <p className="text-sm text-gray-400 mb-2">
                          Setting achievable targets for the upcoming week.
                        </p>
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-gray-500">3 days ago</span>
                          <span className="px-2 py-1 bg-gray-600 text-gray-300 text-xs rounded-full">
                            Goals
                          </span>
                        </div>
                      </div>
                    </div>
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
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Mood Trends & Recommended */}
            <div className="space-y-6">
              {/* Mood Trends */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">Mood Trends</h3>
                  <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
                    View All
                  </button>
                </div>
                {/* Simple Bar Chart */}
                <div className="h-32 flex items-end justify-between gap-1 mb-4">
                  <div className="flex-1 bg-blue-500 rounded-t" style={{ height: "60%" }}></div>
                  <div className="flex-1 bg-blue-500 rounded-t" style={{ height: "80%" }}></div>
                  <div className="flex-1 bg-blue-500 rounded-t" style={{ height: "45%" }}></div>
                  <div className="flex-1 bg-red-500 rounded-t" style={{ height: "30%" }}></div>
                  <div className="flex-1 bg-blue-500 rounded-t" style={{ height: "70%" }}></div>
                  <div className="flex-1 bg-green-500 rounded-t" style={{ height: "90%" }}></div>
                  <div className="flex-1 bg-blue-500 rounded-t" style={{ height: "65%" }}></div>
                </div>
                <div className="flex items-center gap-2">
                  <svg
                    className="w-5 h-5 text-green-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                  <div>
                    <div className="text-sm text-gray-400">Weekly Average</div>
                    <div className="text-white font-semibold">Generally Positive</div>
                  </div>
                </div>
              </div>

              {/* Recommended */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">Recommended</h3>
                  <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
                    Browse All
                  </button>
                </div>
                <div className="space-y-4">
                  {/* Meditation Card */}
                  <div className="bg-gray-700 rounded-lg overflow-hidden">
                    <div className="h-32 bg-gradient-to-br from-blue-600 to-blue-800 relative">
                      <div className="absolute inset-0 bg-black bg-opacity-20"></div>
                      <div className="absolute top-3 left-3">
                        <span className="px-2 py-1 bg-blue-500 text-white text-xs font-semibold rounded">
                          MEDITATION
                        </span>
                      </div>
                    </div>
                    <div className="p-4">
                      <h4 className="font-semibold text-white mb-1">
                        5-Minute Breathing Reset
                      </h4>
                      <p className="text-sm text-gray-400">
                        A quick guided session to help you center yourself during a busy day.
                      </p>
                    </div>
                  </div>

                  {/* Understanding Anxiety Card */}
                  <div className="bg-gray-700 rounded-lg p-4 flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-gray-600 flex items-center justify-center flex-shrink-0">
                      <svg
                        className="w-6 h-6 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-white mb-1">
                        Understanding Anxiety
                      </h4>
                      <p className="text-sm text-gray-400">3 min read</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* User Statistics */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
              <div className="text-3xl font-bold text-white mb-2">12</div>
              <div className="text-sm text-gray-400 uppercase tracking-wider">
                DAY STREAK
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
              <div className="text-3xl font-bold text-white mb-2">4</div>
              <div className="text-sm text-gray-400 uppercase tracking-wider">
                SESSIONS
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
              <div className="text-3xl font-bold text-white mb-2">85%</div>
              <div className="text-sm text-gray-400 uppercase tracking-wider">
                MOOD SCORE
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
              <div className="text-3xl font-bold text-white mb-2">5</div>
              <div className="text-sm text-gray-400 uppercase tracking-wider">
                JOURNALS
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

