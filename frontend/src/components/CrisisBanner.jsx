import { useState } from "react";
import { AlertTriangle, Phone, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

export default function CrisisBanner({ onDismiss }) {
  const [visible, setVisible] = useState(true);

  const handleDismiss = () => {
    setVisible(false);
    onDismiss?.();
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className="mx-8 mt-4 p-4 flex items-start gap-3"
          style={{
            background: "rgba(224, 124, 107, 0.1)",
            border: "1px solid rgba(224, 124, 107, 0.4)",
            borderRadius: "16px",
          }}
        >
          <AlertTriangle
            size={20}
            className="shrink-0 mt-0.5"
            style={{ color: "#E07C6B" }}
          />
          <div className="flex-1 min-w-0">
            <p
              className="text-sm font-medium mb-1"
              style={{ color: "#C15A4B" }}
            >
              We noticed you may be going through something difficult.
            </p>
            <p className="text-sm mb-3" style={{ color: "#7A3A2E" }}>
              You are not alone. Please reach out to a crisis support line if
              you need immediate help.
            </p>
            <div className="flex flex-wrap gap-3">
              <a
                href="tel:988"
                className="inline-flex items-center gap-2 px-4 py-2 text-sm text-white transition-all hover:opacity-90"
                style={{ background: "#E07C6B", borderRadius: "10px" }}
              >
                <Phone size={14} />
                Call or Text 988
              </a>
              <a
                href="sms:741741"
                className="inline-flex items-center gap-2 px-4 py-2 text-sm transition-all hover:opacity-90"
                style={{
                  background: "rgba(224, 124, 107, 0.15)",
                  color: "#C15A4B",
                  borderRadius: "10px",
                  border: "1px solid rgba(224, 124, 107, 0.3)",
                }}
              >
                Text HOME to 741741
              </a>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="p-1 rounded-full hover:bg-red-100 transition-all shrink-0"
            aria-label="Dismiss crisis banner"
          >
            <X size={16} style={{ color: "#E07C6B" }} />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
