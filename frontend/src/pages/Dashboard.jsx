import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  MessageCircle,
  Settings as SettingsIcon,
  Moon,
  CheckCircle,
  TrendingUp,
  Flame,
  Book,
  ArrowUp,
  MoreVertical,
  ChevronRight,
  Eye,
} from "lucide-react";
import { motion } from "motion/react";
import Sidebar from "../components/Sidebar";
import API from "../api";
import MoodCheckInModal from "../components/MoodCheckInModal";

export default function Dashboard() {
  const navigate = useNavigate();
  const [userName, setUserName] = useState("Alex");
  const [conversations, setConversations] = useState([]);
  const [latestConversation, setLatestConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [recommendations, setRecommendations] = useState({
    featured: {
      category: "Meditation",
      title: "5-Minute Breathing Reset",
      description: "Quick guided meditation for stress relief",
    },
    items: [
      { type: "article", title: "Understanding Anxiety", meta: "3 min read" },
    ],
  });
  const [isMoodModalOpen, setIsMoodModalOpen] = useState(false);
  const [stats, setStats] = useState([
    { number: "-", label: "DAY STREAK", icon: Flame, color: "#F5A962" },
    {
      number: "-",
      label: "TOTAL SESSIONS",
      icon: MessageCircle,
      color: "#4A90D9",
    },
    {
      number: "-%",
      label: "MOOD SCORE",
      icon: ArrowUp,
      color: "#7EC8A4",
      showProgress: true,
      progressTarget: 0
    },
    { number: "-", label: "JOURNALS", icon: Book, color: "#4A90D9" },
  ]);

  const [moodTrend, setMoodTrend] = useState([]);

  const fetchDashboardData = async ({ showLoading = false } = {}) => {
    if (showLoading) {
      setIsLoading(true);
    }
    setLoadError("");

    try {
      const [historyRes, statsRes, moodRes, recommendationsRes] = await Promise.all([
        API.get("/history/"),
        API.get("/insights/stats"),
        API.get("/insights/mood?days=7"),
        API.get("/insights/recommendations"),
      ]);

      setConversations(historyRes.data.slice(0, 3).map(chat => ({
        id: chat.id,
        title: chat.title,
        preview: chat.preview,
        tag: chat.tag || "General",
        time: new Date(chat.created_at).toLocaleDateString(),
        icon: MessageCircle,
        color: "#4A90D9"
      })));
      setLatestConversation(
        historyRes.data.length > 0
          ? {
              id: historyRes.data[0].id,
              title: historyRes.data[0].title,
            }
          : null,
      );
      setRecommendations(recommendationsRes.data);

      const data = statsRes.data;
      setStats([
        { number: data.day_streak.toString(), label: "DAY STREAK", icon: Flame, color: "#F5A962" },
        { number: data.total_sessions.toString(), label: "TOTAL SESSIONS", icon: MessageCircle, color: "#4A90D9" },
        { number: Math.round(data.mood_score_percent) + "%", label: "MOOD SCORE", icon: ArrowUp, color: "#7EC8A4", showProgress: true, progressTarget: data.mood_score_percent / 100 },
        { number: data.journals.toString(), label: "JOURNALS", icon: Book, color: "#4A90D9" },
      ]);

      const days = ["S", "M", "T", "W", "T", "F", "S"];
      const trend = moodRes.data.map(entry => ({
        day: days[new Date(entry.date).getDay()],
        value: entry.mood_score * 10,
        color: entry.mood_score > 7 ? "#7EC8A4" : entry.mood_score > 4 ? "#4A90D9" : "#E07C6B"
      }));
      setMoodTrend(trend);
    } catch (e) {
      console.error("Dashboard fetch error", e);
      setLoadError("We couldn't load your latest dashboard data right now.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        if (user?.name) setUserName(user.name.split(" ")[0]);
      } catch (e) {}
    }
    fetchDashboardData({ showLoading: true });
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main
        className="flex-1 overflow-y-auto p-10"
        style={{ background: "#F7FAFD" }}
      >
        <div className="max-w-[1200px] mx-auto space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="flex items-start justify-between"
          >
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1
                  className="text-4xl"
                  style={{ color: "var(--aura-text-primary)" }}
                >
                  Good evening, {userName}.
                </h1>
                <motion.span
                  className="text-3xl"
                  animate={{ rotate: [0, 15, 0] }}
                  transition={{ duration: 1, repeat: Infinity, repeatDelay: 3 }}
                >
                  {"\uD83D\uDC4B"}
                </motion.span>
              </div>
              <p
                className="text-base"
                style={{ color: "var(--aura-text-secondary)" }}
              >
                Ready to check in? Remember, one step at a time.
              </p>
            </div>

              <div className="flex items-center gap-3">
                <button 
                  onClick={() => setIsMoodModalOpen(true)}
                  className="px-6 py-2.5 text-white font-medium transition-all hover:scale-105 active:scale-95"
                  style={{ 
                    background: "linear-gradient(135deg, #4A90D9, #2C5F8A)",
                    borderRadius: "12px",
                    boxShadow: "0 4px 12px rgba(44, 95, 138, 0.2)"
                  }}
                >
                  Check In Now
                </button>
                <div className="flex items-center gap-3">
                  <button className="p-2 hover:bg-gray-100 rounded-lg transition-all">
                    <Eye
                  size={20}
                  style={{ color: "var(--aura-text-secondary)" }}
                />
              </button>
              <div
                className="w-11 h-11 rounded-full flex items-center justify-center text-sm text-white"
                style={{
                  background:
                    "linear-gradient(135deg, #F5A962 0%, #E8834A 100%)",
                  boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                  border: "2px solid white",
                }}
              >
                AD
              </div>
            </div>
          </div>
        </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="bg-white p-8 relative overflow-hidden"
            style={{
              borderRadius: "20px",
              boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
            }}
          >
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ background: "#4A90D9" }}
                ></div>
                <span
                  className="text-xs uppercase tracking-wider"
                  style={{ color: "#4A90D9", letterSpacing: "0.1em" }}
                >
                  CURRENT STATUS
                </span>
              </div>

              <h2
                className="text-2xl mb-2"
                style={{ color: "var(--aura-text-primary)" }}
              >
                Start a New Session
              </h2>
              <p
                className="text-base mb-6"
                style={{ color: "var(--aura-text-secondary)" }}
              >
                Continue where you left off or start a fresh topic today.
                I&apos;m here to listen.
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => navigate("/chat")}
                  className="flex items-center gap-2 px-6 text-white hover:opacity-90 transition-all"
                  style={{
                    background: "#4A90D9",
                    borderRadius: "12px",
                    height: "48px",
                  }}
                >
                  <MessageCircle size={18} />
                  <span>Start Chatting</span>
                </button>

                <button
                  onClick={() =>
                    navigate(
                      latestConversation
                        ? `/chat/${latestConversation.id}`
                        : "/chat",
                    )
                  }
                  className="flex items-center gap-2 px-6 hover:bg-opacity-80 transition-all"
                  style={{
                    background: "rgba(74, 144, 217, 0.08)",
                    color: "#4A90D9",
                    border: "1px solid rgba(74, 144, 217, 0.3)",
                    borderRadius: "12px",
                    height: "48px",
                  }}
                >
                  <span>
                    {latestConversation
                      ? `Resume: ${latestConversation.title}`
                      : "Resume Latest Session"}
                  </span>
                </button>
              </div>
            </div>

            <div
              className="absolute -right-8 top-1/2 -translate-y-1/2 w-64 h-64 opacity-20"
              style={{
                background: "linear-gradient(135deg, #4A90D9 0%, #7EC8A4 100%)",
                borderRadius: "50%",
                filter: "blur(40px)",
              }}
            />
            <div
              className="absolute right-12 top-1/2 -translate-y-1/2 w-32 h-32 opacity-30"
              style={{
                background: "linear-gradient(135deg, #7EC8A4 0%, #4A90D9 100%)",
                borderRadius: "50%",
                filter: "blur(20px)",
              }}
            />
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="lg:col-span-2 bg-white p-7"
              style={{
                borderRadius: "20px",
                boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
              }}
            >
              <div className="flex items-center justify-between mb-6">
                <h3
                  className="text-xl"
                  style={{ color: "var(--aura-text-primary)" }}
                >
                  Recent Conversations
                </h3>
                <button className="p-1 hover:bg-gray-100 rounded-lg transition-all">
                  <MoreVertical
                    size={20}
                    style={{ color: "var(--aura-text-secondary)" }}
                  />
                </button>
              </div>

              <div className="space-y-3">
                {isLoading ? (
                  <PageMessage
                    title="Loading your recent activity"
                    description="Pulling in your latest conversations and progress."
                  />
                ) : loadError ? (
                  <PageMessage
                    title="Dashboard data is temporarily unavailable"
                    description={loadError}
                    actionLabel="Try Again"
                    onAction={() => fetchDashboardData({ showLoading: true })}
                  />
                ) : conversations.length === 0 ? (
                  <PageMessage
                    title="No conversations yet"
                    description="Start your first chat and it will show up here for quick access."
                    actionLabel="Start Chatting"
                    onAction={() => navigate("/chat")}
                  />
                ) : (
                  conversations.map((conv, index) => (
                    <motion.button
                      key={conv.id ?? conv.title}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: 0.3 + index * 0.1 }}
                      className="w-full flex items-center gap-4 p-4 hover:-translate-y-0.5 transition-all text-left"
                      style={{
                        border: "1px solid #EEF2F7",
                        borderRadius: "12px",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.boxShadow =
                          "0 4px 16px rgba(44, 95, 138, 0.10)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.boxShadow = "none";
                      }}
                      onClick={() => navigate(conv.id ? `/chat/${conv.id}` : "/chat")}
                    >
                      <div
                        className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                        style={{ background: "rgba(74, 144, 217, 0.08)" }}
                      >
                        <conv.icon size={22} style={{ color: conv.color }} />
                      </div>

                      <div className="flex-1 min-w-0">
                        <h4
                          className="text-base mb-1"
                          style={{ color: "var(--aura-text-primary)" }}
                        >
                          {conv.title}
                        </h4>
                        <p
                          className="text-sm mb-2 truncate"
                          style={{ color: "var(--aura-text-secondary)" }}
                        >
                          {conv.preview}
                        </p>
                        <div className="flex items-center gap-2">
                          <span
                            className="text-xs px-2 py-1"
                            style={{
                              background: "rgba(74, 144, 217, 0.1)",
                              color: "#4A90D9",
                              borderRadius: "8px",
                            }}
                          >
                            {conv.tag}
                          </span>
                          <span className="text-xs" style={{ color: "#9BAABB" }}>
                            {conv.time}
                          </span>
                        </div>
                      </div>

                      <ChevronRight size={20} style={{ color: "#C0CDD8" }} />
                    </motion.button>
                  ))
                )}
              </div>
            </motion.div>

            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.25 }}
                className="bg-white p-6"
                style={{
                  borderRadius: "20px",
                  boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
                }}
              >
                <div className="flex items-center justify-between mb-5">
                  <h3
                    className="text-lg"
                    style={{ color: "var(--aura-text-primary)" }}
                  >
                    Mood Trends
                  </h3>
                  <button
                    className="text-sm hover:underline"
                    style={{ color: "#4A90D9" }}
                  >
                    View All
                  </button>
                </div>

                <div className="mb-5">
                  <div className="flex items-end justify-between gap-2 h-32">
                    {moodTrend.length > 0 ? (
                      moodTrend.map((bar, index) => (
                        <div
                          key={`${bar.day}-${index}`}
                          className="flex-1 flex flex-col items-center gap-2"
                        >
                          <motion.div
                            initial={{ height: 0 }}
                            animate={{ height: `${bar.value}%` }}
                            transition={{
                              duration: 0.6,
                              delay: 0.4 + index * 0.05,
                            }}
                            className="w-full rounded-t-lg"
                            style={{ background: bar.color }}
                          />
                          <span className="text-xs" style={{ color: "#9BAABB" }}>
                            {bar.day}
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-sm" style={{ color: "var(--aura-text-secondary)" }}>
                        No data yet this week
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <TrendingUp size={18} style={{ color: "#7EC8A4" }} />
                  <span
                    className="text-sm"
                    style={{ color: "var(--aura-text-secondary)" }}
                  >
                    Weekly Average:
                  </span>
                  <span
                    className="text-sm"
                    style={{ color: "var(--aura-text-primary)" }}
                  >
                    Generally Positive
                  </span>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.3 }}
                className="bg-white p-6"
                style={{
                  borderRadius: "20px",
                  boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
                }}
              >
                <div className="flex items-center justify-between mb-5">
                  <h3
                    className="text-lg"
                    style={{ color: "var(--aura-text-primary)" }}
                  >
                    Recommended
                  </h3>
                  <button
                    className="text-sm hover:underline"
                    style={{ color: "#4A90D9" }}
                  >
                    Browse All
                  </button>
                </div>

                <div
                  className="mb-4 relative overflow-hidden"
                  style={{ borderRadius: "12px", height: "128px" }}
                >
                  <div
                    className="absolute inset-0"
                    style={{
                      background:
                        "linear-gradient(135deg, #4A90D9 0%, #2C5F8A 100%)",
                    }}
                  />
                  <div className="relative p-4 h-full flex flex-col justify-between">
                    <span
                      className="text-xs px-3 py-1 inline-block w-fit"
                      style={{
                        background: "rgba(255, 255, 255, 0.25)",
                        color: "white",
                        borderRadius: "8px",
                        letterSpacing: "0.05em",
                      }}
                    >
                      {recommendations.featured.category.toUpperCase()}
                    </span>
                    <div>
                      <h4 className="text-base text-white mb-1">
                        {recommendations.featured.title}
                      </h4>
                      <p
                        className="text-sm"
                        style={{ color: "rgba(255, 255, 255, 0.8)" }}
                      >
                        {recommendations.featured.description}
                      </p>
                    </div>
                  </div>
                </div>

                <button className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition-all text-left">
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                    style={{ background: "rgba(74, 144, 217, 0.08)" }}
                  >
                    <Book size={20} style={{ color: "#4A90D9" }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4
                      className="text-sm mb-0.5"
                      style={{ color: "var(--aura-text-primary)" }}
                    >
                      {recommendations.items[0]?.title || "Understanding Anxiety"}
                    </h4>
                    <p
                      className="text-xs"
                      style={{ color: "var(--aura-text-secondary)" }}
                    >
                      {recommendations.items[0]?.meta || "3 min read"}
                    </p>
                  </div>
                </button>
              </motion.div>
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.35 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
          >
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="bg-white p-6 flex flex-col items-center text-center relative"
                style={{
                  borderRadius: "20px",
                  boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
                }}
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                  style={{
                    background: `${stat.color}15`,
                  }}
                >
                  <stat.icon size={24} style={{ color: stat.color }} />
                </div>

                {stat.showProgress ? (
                  <div className="relative w-24 h-24 flex items-center justify-center mb-2">
                    <svg
                      width="96"
                      height="96"
                      viewBox="0 0 96 96"
                      className="transform -rotate-90 absolute inset-0"
                    >
                      <circle
                        cx="48"
                        cy="48"
                        r="42"
                        fill="none"
                        stroke="#EEF2F7"
                        strokeWidth="6"
                      />
                      <motion.circle
                        cx="48"
                        cy="48"
                        r="42"
                        fill="none"
                        stroke="#7EC8A4"
                        strokeWidth="6"
                        strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 42}`}
                        initial={{ strokeDashoffset: 2 * Math.PI * 42 }}
                        animate={{
                          strokeDashoffset: 2 * Math.PI * 42 * (1 - (stat.progressTarget || 0)),
                        }}
                        transition={{
                          duration: 1,
                          delay: 0.5,
                          ease: "easeOut",
                        }}
                      />
                    </svg>
                    <div
                      className="text-4xl relative z-10"
                      style={{ color: "var(--aura-text-primary)" }}
                    >
                      {stat.number}
                    </div>
                  </div>
                ) : (
                  <div
                    className="text-4xl mb-2"
                    style={{ color: "var(--aura-text-primary)" }}
                  >
                    {stat.number}
                  </div>
                )}

                <div
                  className="text-xs uppercase tracking-wider"
                  style={{
                    color: "var(--aura-text-secondary)",
                    letterSpacing: "0.1em",
                  }}
                >
                  {stat.label}
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </main>

      <MoodCheckInModal 
        isOpen={isMoodModalOpen} 
        onClose={() => setIsMoodModalOpen(false)} 
        onRefresh={() => {
          fetchDashboardData();
        }}
      />
    </div>
  );
}

function PageMessage({ title, description, actionLabel, onAction }) {
  return (
    <div
      className="p-6 text-center"
      style={{
        border: "1px dashed #D0DCE8",
        borderRadius: "16px",
        background: "#F7FAFD",
      }}
    >
      <h4 className="text-base mb-2" style={{ color: "var(--aura-text-primary)" }}>
        {title}
      </h4>
      <p className="text-sm mb-4" style={{ color: "var(--aura-text-secondary)" }}>
        {description}
      </p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 text-sm text-white hover:opacity-90 transition-all"
          style={{ background: "#4A90D9", borderRadius: "10px" }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
