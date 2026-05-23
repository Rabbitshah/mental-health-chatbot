import { useState, useEffect, useRef } from "react";
import { Bell, X, Check } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import API from "../api";

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const fetchNotifications = async () => {
    try {
      const { data } = await API.get("/notifications");
      setNotifications(Array.isArray(data) ? data : data.notifications || []);
    } catch {
      // Silently fail — notifications are non-critical
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAsRead = async (id) => {
    try {
      await API.put(`/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
      );
    } catch {
      // Silently fail
    }
  };

  const markAllRead = async () => {
    const unread = notifications.filter((n) => !n.read);
    await Promise.allSettled(unread.map((n) => API.put(`/notifications/${n.id}/read`)));
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative p-2 hover:bg-gray-100 rounded-lg transition-all"
        aria-label={`Notifications${unreadCount > 0 ? `, ${unreadCount} unread` : ""}`}
      >
        <Bell size={20} style={{ color: "var(--aura-text-secondary)" }} />
        {unreadCount > 0 && (
          <span
            className="absolute top-1 right-1 flex items-center justify-center text-white"
            style={{
              background: "#E07C6B",
              borderRadius: "50%",
              width: "16px",
              height: "16px",
              fontSize: "10px",
              fontWeight: 600,
              lineHeight: 1,
            }}
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -8 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 bg-white z-50"
            style={{
              borderRadius: "16px",
              boxShadow: "0 8px 32px rgba(44, 95, 138, 0.15)",
              width: "320px",
              maxHeight: "400px",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              className="flex items-center justify-between px-4 py-3"
              style={{ borderBottom: "1px solid #E0E7EF" }}
            >
              <span className="font-medium" style={{ color: "var(--aura-text-primary)" }}>
                Notifications
              </span>
              {unreadCount > 0 && (
                <button
                  onClick={markAllRead}
                  className="text-xs flex items-center gap-1 hover:opacity-80 transition-all"
                  style={{ color: "#4A90D9" }}
                >
                  <Check size={12} />
                  Mark all read
                </button>
              )}
            </div>

            <div className="overflow-y-auto flex-1">
              {notifications.length === 0 ? (
                <div className="px-4 py-8 text-center">
                  <Bell size={24} className="mx-auto mb-2 opacity-30" style={{ color: "var(--aura-text-secondary)" }} />
                  <p className="text-sm" style={{ color: "var(--aura-text-secondary)" }}>
                    No notifications yet
                  </p>
                </div>
              ) : (
                notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className="flex items-start gap-3 px-4 py-3 transition-all"
                    style={{
                      background: notification.read ? "transparent" : "rgba(74, 144, 217, 0.05)",
                      borderBottom: "1px solid #F0F4F8",
                    }}
                  >
                    <div
                      className="w-2 h-2 rounded-full mt-1.5 shrink-0"
                      style={{
                        background: notification.read ? "transparent" : "#4A90D9",
                      }}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm" style={{ color: "var(--aura-text-primary)" }}>
                        {notification.message}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: "var(--aura-text-secondary)" }}>
                        {new Date(notification.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    {!notification.read && (
                      <button
                        onClick={() => markAsRead(notification.id)}
                        className="p-1 hover:bg-gray-100 rounded transition-all shrink-0"
                        aria-label="Dismiss notification"
                      >
                        <X size={14} style={{ color: "#9BAABB" }} />
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
