import { useState, useEffect } from "react";
import {
  TrendingUp,
  Activity,
  Heart,
  Brain,
  Moon,
  Award,
  Target,
  CheckCircle2,
} from "lucide-react";
import { motion } from "motion/react";
import Sidebar from "../components/Sidebar";
import API from "../api";

export default function Insights() {
  const [selectedPeriod, setSelectedPeriod] = useState("week");
  const [moodTrends, setMoodTrends] = useState([
    { day: "Mon", mood: 7.2, energy: 6.8, stress: 4.5 },
    { day: "Tue", mood: 8.5, energy: 8.0, stress: 3.2 },
    { day: "Wed", mood: 6.0, energy: 5.5, stress: 6.8 },
    { day: "Thu", mood: 5.5, energy: 5.0, stress: 7.5 },
    { day: "Fri", mood: 7.8, energy: 7.5, stress: 4.0 },
    { day: "Sat", mood: 9.0, energy: 8.8, stress: 2.5 },
    { day: "Sun", mood: 8.2, energy: 7.8, stress: 3.0 },
  ]);

  const insights = [
    {
      title: "Mood Improving",
      description:
        "Your average mood has increased by 15% this week compared to last week.",
      trend: "up",
      percentage: "+15%",
      icon: TrendingUp,
      color: "#7EC8A4",
    },
    {
      title: "Sleep Quality",
      description:
        "You've been sleeping better. Average sleep quality improved significantly.",
      trend: "up",
      percentage: "+22%",
      icon: Moon,
      color: "#4A90D9",
    },
    {
      title: "Stress Levels",
      description:
        "Stress has decreased after implementing breathing exercises.",
      trend: "down",
      percentage: "-18%",
      icon: Activity,
      color: "#7EC8A4",
    },
    {
      title: "Engagement",
      description: "You're engaging more with wellness activities this month.",
      trend: "up",
      percentage: "+30%",
      icon: Heart,
      color: "#F5A962",
    },
  ];

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
      label: "Sleep Quality",
      value: "8.2",
      max: "10",
      icon: Moon,
      color: "#2C5F8A",
      progress: 82,
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

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        const daysParam = selectedPeriod === 'week' ? 7 : (selectedPeriod === 'month' ? 30 : 365);
        const res = await API.get(`/insights/mood?days=${daysParam}`);
        const entries = res.data;
        
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
          
          setWeeklyStats([
             { label: "Average Mood", value: avgMood, max: "10", icon: Heart, color: "#7EC8A4", progress: avgMood * 10 },
             { label: "Energy Levels", value: avgEnergy, max: "10", icon: Activity, color: "#4A90D9", progress: avgEnergy * 10 },
             { label: "Sleep Quality", value: "8.2", max: "10", icon: Moon, color: "#2C5F8A", progress: 82 },
             { label: "Stress Level", value: avgStress, max: "10", icon: Brain, color: "#F5A962", progress: avgStress * 10 },
          ]);
        }
      } catch (e) {
        console.error("Insights fetch error", e);
      }
    };
    fetchInsights();
  }, [selectedPeriod]);

  const achievements = [
    {
      title: "7-Day Streak",
      description: "Checked in daily for a full week",
      icon: Flame,
      earned: true,
      color: "#F5A962",
    },
    {
      title: "Mood Master",
      description: "Tracked mood 30 times",
      icon: Award,
      earned: true,
      color: "#7EC8A4",
    },
    {
      title: "Early Bird",
      description: "Completed 5 morning check-ins",
      icon: CheckCircle2,
      earned: true,
      color: "#4A90D9",
    },
    {
      title: "Wellness Warrior",
      description: "Used app for 30 consecutive days",
      icon: Target,
      earned: false,
      color: "#9BAABB",
    },
  ];

  const topTopics = [
    { topic: "Work Stress", count: 12, color: "#4A90D9" },
    { topic: "Sleep Issues", count: 8, color: "#2C5F8A" },
    { topic: "Anxiety", count: 7, color: "#7EC8A4" },
    { topic: "Goal Setting", count: 5, color: "#F5A962" },
    { topic: "Relationships", count: 4, color: "#4A90D9" },
  ];

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
            {insights.map((insight, index) => (
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
            ))}
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
                  {moodTrends.map((data, index) => (
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
                  ))}
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
