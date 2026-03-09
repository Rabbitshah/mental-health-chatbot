import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";

export default function SplashScreen() {
  const navigate = useNavigate();

  return (
    <div
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{
        background: "linear-gradient(180deg, #EAF4FF 0%, #D8EDD8 100%)",
      }}
    >
      <div className="max-w-2xl mx-auto px-8 text-center z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8 flex flex-col items-center"
        >
          <motion.div
            className="relative mb-6"
            animate={{
              scale: [1, 1.05, 1],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <div className="relative w-24 h-24">
              <div
                className="absolute top-0 left-0 w-20 h-20 rounded-full opacity-40"
                style={{ background: "#4A90D9" }}
              />
              <div
                className="absolute bottom-0 right-0 w-20 h-20 rounded-full opacity-40"
                style={{ background: "#7EC8A4" }}
              />
              <div
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 rounded-full"
                style={{
                  background:
                    "radial-gradient(circle, rgba(74, 144, 217, 0.6) 0%, transparent 70%)",
                  filter: "blur(8px)",
                }}
              />
            </div>
          </motion.div>

          <h1
            className="text-6xl mb-4"
            style={{
              fontFamily: "var(--font-display)",
              color: "var(--aura-text-primary)",
            }}
          >
            AuraChat
          </h1>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="text-xl mb-12"
          style={{ color: "var(--aura-text-secondary)" }}
        >
          Your safe space to think, feel, and heal.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16"
        >
          <button
            onClick={() => navigate("/signup")}
            className="px-8 py-4 text-white transition-all hover:opacity-90 min-w-[200px]"
            style={{
              background: "#4A90D9",
              borderRadius: "24px",
              boxShadow: "0 4px 24px rgba(74, 144, 217, 0.3)",
            }}
          >
            Get Started
          </button>

          <button
            onClick={() => navigate("/login")}
            className="px-8 py-4 transition-all hover:bg-white/50 min-w-[200px]"
            style={{
              background: "transparent",
              border: "2px solid rgba(74, 144, 217, 0.3)",
              borderRadius: "24px",
              color: "var(--aura-text-primary)",
            }}
          >
            I already have an account
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="flex items-center justify-center gap-2 text-sm"
          style={{ color: "var(--aura-text-secondary)" }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M8 1L3 3v4c0 3.5 2.5 6.5 5 7 2.5-.5 5-3.5 5-7V3l-5-2z"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          </svg>
          <span>Your conversations are private.</span>
        </motion.div>
      </div>

      <div className="absolute bottom-0 left-0 right-0">
        <svg
          viewBox="0 0 1440 120"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full"
        >
          <path
            d="M0 60C240 20 480 0 720 20C960 40 1200 80 1440 60V120H0V60Z"
            fill="white"
            fillOpacity="0.3"
          />
          <path
            d="M0 80C240 100 480 100 720 80C960 60 1200 40 1440 60V120H0V80Z"
            fill="white"
            fillOpacity="0.5"
          />
        </svg>
      </div>
    </div>
  );
}
