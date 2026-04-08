import { useState, useEffect } from "react";
import {
  TrendingUp,
  Activity,
  Heart,
  Brain,
  Award,
  Target,
  CheckCircle2,
} from "lucide-react";
import { motion } from "motion/react";
import Sidebar from "../components/Sidebar";
import API from "../api";

export default function Insights() {
  const [selectedPeriod, setSelectedPeriod] = useState("week");
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [moodTrends, setMoodTrends] = useState([
    { day: "Mon", mood: 7.2, energy: 6.8, stress: 4.5 },
    { day: "Tue", mood: 8.5, energy: 8.0, stress: 3.2 },
    { day: "Wed", mood: 6.0, energy: 5.5, stress: 6.8 },
    { day: "Thu", mood: 5.5, energy: 5.0, stress: 7.5 },
    { day: "Fri", mood: 7.8, energy: 7.5, stress: 4.0 },
    { day: "Sat", mood: 9.0, energy: 8.8, stress: 2.5 },
    { day: "Sun", mood: 8.2, energy: 7.8, stress: 3.0 },
  ]);

  const [insights, setInsights] = useState([
    {
      title: "Mood Trend",
      description: "Start completing daily check-ins to unlock personalized wellness insights.",
      trend: "neutral",
      percentage: "0%",
      icon: TrendingUp,
      color: "#7EC8A4",
    },
    {
      title: "Energy Levels",
      description: "We need a few check-ins before we can identify your energy patterns.",
      trend: "neutral",
      percentage: "0%",
      icon: Activity,
      color: "#4A90D9",
    },
    {
      title: "Stress Levels",
      description: "Track stress for a few days and this card will begin showing real changes.",
      trend: "neutral",
      percentage: "0%",
      icon: Brain,
      color: "#F5A962",
    },
    {
      title: "Check-in Consistency",
      description: "Keep checking in regularly so we can identify meaningful patterns over time.",
      trend: "neutral",
      percentage: "0%",
      icon: Heart,
      color: "#F5A962",
    },
  ]);

  const [weeklyStats, setWeeklyStats] = useState([
    {
      label: "Average Mood",
      value: "7.6",
      max: "10",
      icon: Heart,
      color: "#7EC8A4",
      progress: 76,
    },
    {
      label: "Energy Levels",
      value: "7.1",
      max: "10",
      icon: Activity,
      color: "#4A90D9",
      progress: 71,
    },
    {
      label: "Check-in Rate",
      value: "0",
      max: "%",
      icon: CheckCircle2,
      color: "#2C5F8A",
      progress: 0,
    },
    {
      label: "Stress Level",
      value: "4.5",
      max: "10",
      icon: Brain,
      color: "#F5A962",
      progress: 45,
    },
  ]);
  const [topTopics, setTopTopics] = useState([
    { topic: "General", count: 0, color: "#9BAABB" },
  ]);
  const [achievements, setAchievements] = useState([
    {
      title: "7-Day Streak",
      description: "Checked in daily for a full week",
      icon: Flame,
      earned: false,
      color: "#F5A962",
      progress: 0,
      target: 7,
    },
    {
      title: "Mood Master",
      description: "Tracked mood 30 times",
      icon: Award,
      earned: false,
      color: "#7EC8A4",
      progress: 0,
      target: 30,
    },
    {
      title: "Early Bird",
      description: "Completed 5 morning check-ins",
      icon: CheckCircle2,
      earned: false,
      color: "#4A90D9",
      progress: 0,
      target: 5,
    },
    {
      title: "Conversation Starter",
      description: "Started 10 support sessions",
      icon: Target,
      earned: false,
      color: "#E07C6B",
      progress: 0,
      target: 10,
    },
  ]);
  const [patterns, setPatterns] = useState({
    currentStreak: 0,
    longestStreak: 0,
    bestDay: "No data yet",
    correlations: [],
  });

  const fetchInsightsData = async () => {
    setIsLoading(true);
    setLoadError("");

    try {
      const daysParam = selectedPeriod === 'week' ? 7 : (selectedPeriod === 'month' ? 30 : 365);
      const [moodRes, summaryRes, topicsRes, achievementsRes, patternsRes] = await Promise.all([
        API.get(`/insights/mood?days=${daysParam}`),
        API.get(`/insights/summary?days=${daysParam}`),
        API.get("/insights/topics"),
        API.get("/insights/achievements"),
        API.get(`/insights/patterns?days=${daysParam}`),
      ]);
      const entries = moodRes.data;
      
      if (entries && entries.length > 0) {
        const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        const trends = entries.slice(-7).map(e => ({
           day: daysOfWeek[new Date(e.date).getDay()],
           mood: e.mood_score,
           energy: e.energy_level,
           stress: e.stress_level
        }));
        setMoodTrends(trends);
        
        const avgMood = (entries.reduce((acc, e) => acc + e.mood_score, 0) / entries.length).toFixed(1);
        const avgEnergy = (entries.reduce((acc, e) => acc + e.energy_level, 0) / entries.length).toFixed(1);
        const avgStress = (entries.reduce((acc, e) => acc + e.stress_level, 0) / entries.length).toFixed(1);
        const uniqueCheckInDays = new Set(
          entries.map((entry) => new Date(entry.date).toDateString()),
        ).size;
        const checkInRate = Math.round((uniqueCheckInDays / daysParam) * 100);
        
        setWeeklyStats([
           { label: "Average Mood", value: avgMood, max: "10", icon: Heart, color: "#7EC8A4", progress: avgMood * 10 },
           { label: "Energy Levels", value: avgEnergy, max: "10", icon: Activity, color: "#4A90D9", progress: avgEnergy * 10 },
           { label: "Check-in Rate", value: checkInRate.toString(), max: "%", icon: CheckCircle2, color: "#2C5F8A", progress: checkInRate },
           { label: "Stress Level", value: avgStress, max: "10", icon: Brain, color: "#F5A962", progress: avgStress * 10 },
        ]);
      } else {
        setMoodTrends([]);
        setWeeklyStats([
          { label: "Average Mood", value: "0.0", max: "10", icon: Heart, color: "#7EC8A4", progress: 0 },
          { label: "Energy Levels", value: "0.0", max: "10", icon: Activity, color: "#4A90D9", progress: 0 },
          { label: "Check-in Rate", value: "0", max: "%", icon: CheckCircle2, color: "#2C5F8A", progress: 0 },
          { label: "Stress Level", value: "0.0", max: "10", icon: Brain, color: "#F5A962", progress: 0 },
        ]);
      }

      if (summaryRes.data?.insights) {
        setInsights(
          summaryRes.data.insights.map((item) => ({
            title: item.title,
            description: item.description,
            trend: item.direction,
            percentage: item.percentage,
            icon:
              item.metric === "mood"
                ? TrendingUp
                : item.metric === "energy"
                ? Activity
                : item.metric === "stress"
                ? Brain
                : Heart,
            color:
              item.metric === "mood"
                ? "#7EC8A4"
                : item.metric === "energy"
                ? "#4A90D9"
                : item.metric === "stress"
                ? "#F5A962"
                : "#E07C6B",
          })),
        );
      }

      if (topicsRes.data?.topics) {
        setTopTopics(topicsRes.data.topics);
      }

      if (achievementsRes.data?.achievements) {
        setAchievements(
          achievementsRes.data.achievements.map((item) => ({
            ...item,
            icon:
              item.key === "streak_7"
                ? Flame
                : item.key === "mood_30"
                ? Award
                : item.key === "morning_5"
                ? CheckCircle2
                : Target,
          })),
        );
      }

      if (patternsRes.data) {
        setPatterns({
          currentStreak: patternsRes.data.current_streak ?? 0,
          longestStreak: patternsRes.data.longest_streak ?? 0,
          bestDay: patternsRes.data.best_day || "No data yet",
          correlations: patternsRes.data.correlations || [],
        });
      }
    } catch (e) {
      console.error("Insights fetch error", e);
      setLoadError("We couldn't load your insights right now.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInsightsData();
  }, [selectedPeriod]);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main
        className="flex-1 overflow-y-auto p-10"
        style={{ background: "#F7FAFD" }}
      >
        <div className="max-w-[1400px] mx-auto space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <h1
              className="text-4xl mb-2"
              style={{ color: "var(--aura-text-primary)" }}
            >
              Wellness Insights
            </h1>
            <p
              className="text-base"
              style={{ color: "var(--aura-text-secondary)" }}
            >
              Track your progress and discover patterns in your wellness journey
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="flex gap-2"
          >
            {["week", "month", "year"].map((period) => (
              <button
                key={period}
                onClick={() => setSelectedPeriod(period)}
                className="px-5 py-2 text-sm transition-all capitalize"
                style={{
                  background: selectedPeriod === period ? "#4A90D9" : "white",
                  color:
                    selectedPeriod === period
                      ? "white"
                      : "var(--aura-text-secondary)",
                  borderRadius: "12px",
                  border:
                    selectedPeriod === period ? "none" : "1px solid #E0E7EF",
                }}
              >
                This {period}
              </button>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6"
          >
            {isLoading || loadError ? (
              <div className="md:col-span-2 xl:col-span-4">
                <StateCard
                  title={isLoading ? "Loading your insights" : "Insights are temporarily unavailable"}
                  description={
                    isLoading
                      ? "We're building your latest mood and activity summary."
                      : loadError
                  }
                  actionLabel={loadError ? "Try Again" : ""}
                  onAction={loadError ? fetchInsightsData : undefined}
                />
              </div>
            ) : (
              insights.map((insight, index) => (
                <motion.div
                  key={insight.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.25 + index * 0.05 }}
                  className="bg-white p-6"
                  style={{
                    borderRadius: "20px",
                    boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
                  }}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center"
                      style={{ background: `${insight.color}15` }}
                    >
                      <insight.icon size={24} style={{ color: insight.color }} />
                    </div>
                    <div
                      className="px-3 py-1 text-sm font-medium"
                      style={{
                        background: "rgba(126, 200, 164, 0.1)",
                        color: "#7EC8A4",
                        borderRadius: "8px",
                      }}
                    >
                      {insight.percentage}
                    </div>
                  </div>
                  <h3
                    className="text-lg mb-2"
                    style={{ color: "var(--aura-text-primary)" }}
                  >
                    {insight.title}
                  </h3>
                  <p
                    className="text-sm"
                    style={{
                      color: "var(--aura-text-secondary)",
                      lineHeight: "1.6",
                    }}
                  >
                    {insight.description}
                  </p>
                </motion.div>
              ))
            )}
          </motion.div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="xl:col-span-2 bg-white p-8"
              style={{
                borderRadius: "20px",
                boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
              }}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3
                    className="text-xl mb-1"
                    style={{ color: "var(--aura-text-primary)" }}
                  >
                    Weekly Mood Trends
                  </h3>
                  <p
                    className="text-sm"
                    style={{ color: "var(--aura-text-secondary)" }}
                  >
                    Track your emotional patterns over time
                  </p>
                </div>
                <div className="flex gap-4">
                  <Legend color="#7EC8A4" label="Mood" />
                  <Legend color="#4A90D9" label="Energy" />
                  <Legend color="#E07C6B" label="Stress" />
                </div>
              </div>

              <div className="relative" style={{ height: "280px" }}>
                <div className="absolute inset-0 flex flex-col justify-between">
                  {[0, 1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="w-full border-t"
                      style={{ borderColor: "#F0F4F8" }}
                    />
                  ))}
                </div>

                <div className="absolute inset-0 flex items-end justify-between gap-4 px-2">
                  {moodTrends.length > 0 ? (
                    moodTrends.map((data, index) => (
                      <div
                        key={data.day}
                        className="flex-1 flex flex-col items-center gap-3"
                        style={{ height: "100%" }}
                      >
                        <div className="flex-1 flex items-end justify-center gap-1 w-full">
                          <TrendBar
                            value={data.mood}
                            delay={0.4 + index * 0.05}
                            color="#7EC8A4"
                          />
                          <TrendBar
                            value={data.energy}
                            delay={0.45 + index * 0.05}
                            color="#4A90D9"
                          />
                          <TrendBar
                            value={data.stress}
                            delay={0.5 + index * 0.05}
                            color="#E07C6B"
                          />
                        </div>
                        <span className="text-xs" style={{ color: "#9BAABB" }}>
                          {data.day}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-sm" style={{ color: "var(--aura-text-secondary)" }}>
                      Complete a few mood check-ins to unlock trend charts.
                    </div>
                  )}
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.35 }}
              className="space-y-6"
            >
              <Card title="Weekly Averages">
                <div className="space-y-5">
                  {weeklyStats.map((stat, index) => (
                    <div key={stat.label}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <stat.icon size={16} style={{ color: stat.color }} />
                          <span
                            className="text-sm"
                            style={{ color: "var(--aura-text-secondary)" }}
                          >
                            {stat.label}
                          </span>
                        </div>
                        <span
                          className="text-sm"
                          style={{ color: "var(--aura-text-primary)" }}
                        >
                          {stat.value}/{stat.max}
                        </span>
                      </div>
                      <div
                        className="w-full h-2 rounded-full overflow-hidden"
                        style={{ background: "#F0F4F8" }}
                      >
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${stat.progress}%` }}
                          transition={{
                            duration: 0.8,
                            delay: 0.4 + index * 0.1,
                          }}
                          className="h-full rounded-full"
                          style={{ background: stat.color }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              <Card title="Top Discussion Topics">
                <div className="space-y-3">
                  {topTopics.map((item, index) => (
                    <motion.div
                      key={item.topic}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: 0.5 + index * 0.05 }}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="w-2 h-2 rounded-full"
                          style={{ background: item.color }}
                        />
                        <span
                          className="text-sm"
                          style={{ color: "var(--aura-text-secondary)" }}
                        >
                          {item.topic}
                        </span>
                      </div>
                      <span
                        className="text-sm font-medium px-2 py-1"
                        style={{
                          background: `${item.color}15`,
                          color: item.color,
                          borderRadius: "6px",
                        }}
                      >
                        {item.count}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </Card>

              <Card title="Patterns and Correlations">
                <div className="space-y-4">
                  <div
                    className="p-4"
                    style={{ background: "#F7FAFD", borderRadius: "14px" }}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm" style={{ color: "var(--aura-text-secondary)" }}>
                        Current Streak
                      </span>
                      <span style={{ color: "#F5A962" }}>
                        <Flame size={16} />
                      </span>
                    </div>
                    <div className="text-lg" style={{ color: "var(--aura-text-primary)" }}>
                      {patterns.currentStreak} days
                    </div>
                  </div>

                  <div
                    className="p-4"
                    style={{ background: "#F7FAFD", borderRadius: "14px" }}
                  >
                    <div className="text-sm mb-1" style={{ color: "var(--aura-text-secondary)" }}>
                      Longest Streak
                    </div>
                    <div className="text-lg" style={{ color: "var(--aura-text-primary)" }}>
                      {patterns.longestStreak} days
                    </div>
                  </div>

                  <div
                    className="p-4"
                    style={{ background: "#F7FAFD", borderRadius: "14px" }}
                  >
                    <div className="text-sm mb-1" style={{ color: "var(--aura-text-secondary)" }}>
                      Best Check-In Day
                    </div>
                    <div className="text-lg" style={{ color: "var(--aura-text-primary)" }}>
                      {patterns.bestDay}
                    </div>
                  </div>

                  {patterns.correlations.map((item) => (
                    <div
                      key={item.label}
                      className="p-4"
                      style={{ background: "#F7FAFD", borderRadius: "14px" }}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm" style={{ color: "var(--aura-text-primary)" }}>
                          {item.label}
                        </span>
                        <span className="text-sm" style={{ color: "#4A90D9" }}>
                          {item.score}%
                        </span>
                      </div>
                      <div className="text-xs mb-1" style={{ color: "#4A90D9" }}>
                        {item.summary}
                      </div>
                      <div className="text-xs" style={{ color: "var(--aura-text-secondary)" }}>
                        {item.description}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          </div>

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
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3
                  className="text-xl mb-1"
                  style={{ color: "var(--aura-text-primary)" }}
                >
                  Achievements
                </h3>
                <p
                  className="text-sm"
                  style={{ color: "var(--aura-text-secondary)" }}
                >
                  Celebrate your wellness milestones
                </p>
              </div>
              <span className="text-sm" style={{ color: "#4A90D9" }}>
                {achievements.filter((a) => a.earned).length} of{" "}
                {achievements.length} earned
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
              {achievements.map((achievement, index) => (
                <motion.div
                  key={achievement.title}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3, delay: 0.5 + index * 0.05 }}
                  className="p-6 text-center"
                  style={{
                    background: achievement.earned
                      ? "rgba(126, 200, 164, 0.05)"
                      : "rgba(155, 170, 187, 0.05)",
                    borderRadius: "16px",
                    border: achievement.earned
                      ? "2px solid rgba(126, 200, 164, 0.2)"
                      : "2px solid rgba(155, 170, 187, 0.1)",
                    opacity: achievement.earned ? 1 : 0.6,
                  }}
                >
                  <div
                    className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                    style={{ background: `${achievement.color}20` }}
                  >
                    <achievement.icon
                      size={28}
                      style={{ color: achievement.color }}
                    />
                  </div>
                  <h4
                    className="text-base mb-2"
                    style={{ color: "var(--aura-text-primary)" }}
                  >
                    {achievement.title}
                  </h4>
                  <p
                    className="text-xs"
                    style={{ color: "var(--aura-text-secondary)" }}
                  >
                    {achievement.description}
                  </p>
                  {!achievement.earned && (
                    <div
                      className="mt-3 text-xs"
                      style={{ color: "var(--aura-text-secondary)" }}
                    >
                      {achievement.progress}/{achievement.target}
                    </div>
                  )}
                  {achievement.earned && (
                    <div
                      className="mt-3 text-xs font-medium"
                      style={{ color: "#7EC8A4" }}
                    >
                      ✓ Earned
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}

function Legend({ color, label }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-3 h-3 rounded-full" style={{ background: color }}></div>
      <span className="text-sm" style={{ color: "var(--aura-text-secondary)" }}>
        {label}
      </span>
    </div>
  );
}

function TrendBar({ value, delay, color }) {
  return (
    <motion.div
      initial={{ height: 0 }}
      animate={{ height: `${value * 10}%` }}
      transition={{ duration: 0.6, delay }}
      className="flex-1 rounded-t"
      style={{ background: color, maxWidth: "8px" }}
    />
  );
}

function Card({ title, children }) {
  return (
    <div
      className="bg-white p-6"
      style={{
        borderRadius: "20px",
        boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
      }}
    >
      <h3
        className="text-lg mb-5"
        style={{ color: "var(--aura-text-primary)" }}
      >
        {title}
      </h3>
      {children}
    </div>
  );
}

function StateCard({ title, description, actionLabel, onAction }) {
  return (
    <div
      className="bg-white p-10 text-center"
      style={{
        borderRadius: "20px",
        boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
      }}
    >
      <h3 className="text-xl mb-2" style={{ color: "var(--aura-text-primary)" }}>
        {title}
      </h3>
      <p className="text-base mb-5" style={{ color: "var(--aura-text-secondary)" }}>
        {description}
      </p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-5 py-2.5 text-white hover:opacity-90 transition-all"
          style={{ background: "#4A90D9", borderRadius: "12px" }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

function Flame({ size, style }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={style}
    >
      <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
    </svg>
  );
}
