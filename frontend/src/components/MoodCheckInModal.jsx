import { useState } from "react";
import { X, Heart, Activity, Brain } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import API from "../api";

export default function MoodCheckInModal({ isOpen, onClose, onRefresh }) {
  const [mood, setMood] = useState(7);
  const [energy, setEnergy] = useState(7);
  const [stress, setStress] = useState(3);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await API.post("/insights/mood", {
        mood_score: mood,
        energy_level: energy,
        stress_level: stress,
      });
      onRefresh();
      onClose();
    } catch (error) {
      console.error("Failed to submit mood", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="bg-white w-full max-w-md overflow-hidden relative"
          style={{ borderRadius: "24px", boxShadow: "0 20px 40px rgba(0,0,0,0.1)" }}
        >
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-full transition-all"
          >
            <X size={20} className="text-gray-400" />
          </button>

          <div className="p-8">
            <h2 className="text-2xl font-semibold mb-2 text-gray-800">Daily Check-in</h2>
            <p className="text-gray-500 mb-8">How are you feeling today?</p>

            <div className="space-y-8">
              {/* Mood Slider */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-gray-700 font-medium">
                    <Heart size={18} className="text-red-400" />
                    <span>Mood</span>
                  </div>
                  <span className="text-sm font-semibold bg-red-50 text-red-500 px-2 py-1 rounded-lg">
                    {mood}/10
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="0.5"
                  value={mood}
                  onChange={(e) => setMood(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-red-400"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Low</span>
                  <span>High</span>
                </div>
              </div>

              {/* Energy Slider */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-gray-700 font-medium">
                    <Activity size={18} className="text-blue-400" />
                    <span>Energy</span>
                  </div>
                  <span className="text-sm font-semibold bg-blue-50 text-blue-500 px-2 py-1 rounded-lg">
                    {energy}/10
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="0.5"
                  value={energy}
                  onChange={(e) => setEnergy(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-blue-400"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Drained</span>
                  <span>Vibrant</span>
                </div>
              </div>

              {/* Stress Slider */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-gray-700 font-medium">
                    <Brain size={18} className="text-purple-400" />
                    <span>Stress</span>
                  </div>
                  <span className="text-sm font-semibold bg-purple-50 text-purple-500 px-2 py-1 rounded-lg">
                    {stress}/10
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="0.5"
                  value={stress}
                  onChange={(e) => setStress(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-purple-400"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Calm</span>
                  <span>Overwhelmed</span>
                </div>
              </div>
            </div>

            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="w-full mt-10 py-4 text-white font-medium transition-all disabled:opacity-50"
              style={{ 
                background: "linear-gradient(135deg, #4A90D9, #2C5F8A)",
                borderRadius: "16px",
                boxShadow: "0 8px 20px rgba(44, 95, 138, 0.2)"
              }}
            >
              {isSubmitting ? "Saving..." : "Save Check-in"}
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
