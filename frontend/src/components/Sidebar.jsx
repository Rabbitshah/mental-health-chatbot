import { useNavigate, useLocation } from "react-router-dom";
import {
  Home,
  MessageCircle,
  Clock,
  BarChart3,
  Settings,
  LogOut,
  Bell,
  BookOpen,
  ClipboardList,
  MoreVertical,
  Edit3,
  Trash2,
  X,
  Pin,
  Archive,
  RotateCcw,
  Phone,
  ShieldAlert,
  HeartHandshake,
} from "lucide-react";
import { useState, createElement, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import API from "../api";
import { useAuth } from "../contexts/AuthContext";

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [showRecents, setShowRecents] = useState(true);
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [recentChats, setRecentChats] = useState([]);
  const { user: authUser, logout } = useAuth();
  const userName = authUser?.name || "Jane Doe";

  const fetchRecentChats = async () => {
    try {
      const { data } = await API.get("/history/");
      const sessions = data.sessions ?? data; // handle both paginated and legacy array
      setRecentChats(
        sessions.slice(0, 5).map((chat) => ({
          id: chat.id.toString(),
          title: chat.title,
          time: formatRelativeDate(chat.updated_at || chat.created_at),
          isPinned: chat.is_pinned,
          isArchived: chat.is_archived,
          tag: chat.tag || "General",
        })),
      );
    } catch (error) {
      console.error("Failed to load recent chats", error);
    }
  };

  useEffect(() => {
    fetchRecentChats();
    window.addEventListener("sessions-updated", fetchRecentChats);

    return () => {
      window.removeEventListener("sessions-updated", fetchRecentChats);
    };
  }, []);

  const getActiveNav = () => {
    const path = location.pathname;
    if (path === "/dashboard") return "home";
    if (path.startsWith("/chat")) return "chat";
    if (path === "/history") return "history";
    if (path === "/insights") return "insights";
    if (path === "/journal") return "journal";
    if (path === "/safety-plan") return "safety";
    if (path === "/profile") return "settings";
    return "chat";
  };

  const activeNav = getActiveNav();

  const handleDelete = async (id) => {
    if (confirm("Are you sure you want to delete this chat?")) {
      try {
        await API.delete(`/history/${id}`);
        setRecentChats((prev) => prev.filter((chat) => chat.id !== id));
        window.dispatchEvent(new Event("sessions-updated"));
        if (location.pathname === `/chat/${id}`) {
          navigate("/chat");
        }
      } catch (error) {
        alert(error.response?.data?.detail || "Failed to delete chat");
      }
      setMenuOpen(null);
    }
  };

  const handleRename = (id, currentTitle) => {
    setEditingId(id);
    setEditTitle(currentTitle);
    setMenuOpen(null);
  };

  const saveRename = async (id) => {
    if (editTitle.trim()) {
      try {
        await API.put(`/history/${id}`, { title: editTitle.trim() });
        setRecentChats((prev) =>
          prev.map((chat) =>
            chat.id === id ? { ...chat, title: editTitle.trim() } : chat,
          ),
        );
        window.dispatchEvent(new Event("sessions-updated"));
      } catch (error) {
        alert(error.response?.data?.detail || "Failed to rename chat");
      }
    }
    setEditingId(null);
    setEditTitle("");
  };

  const cancelRename = () => {
    setEditingId(null);
    setEditTitle("");
  };

  const handleStatusUpdate = async (id, updates) => {
    try {
      const { data } = await API.patch(`/history/${id}/status`, updates);
      setRecentChats((prev) =>
        prev
          .map((chat) =>
            chat.id === id
              ? {
                  ...chat,
                  isPinned: data.is_pinned,
                  isArchived: data.is_archived,
                }
              : chat,
          )
          .filter((chat) => !chat.isArchived)
          .sort((a, b) => {
            if (a.isPinned !== b.isPinned) {
              return Number(b.isPinned) - Number(a.isPinned);
            }
            return 0;
          }),
      );
      setMenuOpen(null);
      window.dispatchEvent(new Event("sessions-updated"));
      if (location.pathname === `/chat/${id}` && data.is_archived) {
        navigate("/chat");
      }
    } catch (error) {
      alert(error.response?.data?.detail || "Failed to update chat status");
    }
  };

  return (
    <>
    <aside
      className="hidden md:flex flex-col h-screen"
      style={{ width: "260px", background: "#1C2B3A", color: "white" }}
    >
      <nav className="px-2 py-3">
        <NavItem
          icon={Home}
          label="Home"
          active={activeNav === "home"}
          onClick={() => navigate("/dashboard")}
        />
        <NavItem
          icon={Clock}
          label="History"
          active={activeNav === "history"}
          onClick={() => navigate("/history")}
        />
        <NavItem
          icon={Settings}
          label="Settings"
          active={activeNav === "settings"}
          onClick={() => navigate("/profile")}
        />

        <div
          className="my-2"
          style={{ borderTop: "1px solid rgba(255, 255, 255, 0.1)" }}
        />

        <NavItem
          icon={MessageCircle}
          label="Chats"
          active={activeNav === "chat"}
          onClick={() => navigate("/chat")}
        />
        <NavItem
          icon={BarChart3}
          label="Insights"
          active={activeNav === "insights"}
          onClick={() => navigate("/insights")}
        />
        <NavItem
          icon={BookOpen}
          label="Journal"
          active={activeNav === "journal"}
          onClick={() => navigate("/journal")}
        />
        <NavItem
          icon={ClipboardList}
          label="Safety Plan"
          active={activeNav === "safety"}
          onClick={() => navigate("/safety-plan")}
        />
      </nav>

      <div className="flex-1 min-h-0 overflow-y-auto px-2 mt-2">
        <div
          className="flex items-center justify-between px-3 py-2 cursor-pointer"
          onClick={() => setShowRecents(!showRecents)}
        >
          <span className="text-xs opacity-60">Recents</span>
          <span className="text-xs opacity-60">
            {showRecents ? "Hide" : "Show"}
          </span>
        </div>
        {showRecents && (
          <div className="mt-1">
            {recentChats.map((chat) => (
              <RecentChatItem
                key={chat.id}
                chat={chat}
                onClick={() => navigate(`/chat/${chat.id}`)}
                isEditing={editingId === chat.id}
                editTitle={editTitle}
                setEditTitle={setEditTitle}
                onSaveRename={() => saveRename(chat.id)}
                onCancelRename={cancelRename}
                menuOpen={menuOpen === chat.id}
                onMenuToggle={() =>
                  setMenuOpen(menuOpen === chat.id ? null : chat.id)
                }
                onRename={() => handleRename(chat.id, chat.title)}
                onTogglePin={() =>
                  handleStatusUpdate(chat.id, { is_pinned: !chat.isPinned })
                }
                onToggleArchive={() =>
                  handleStatusUpdate(chat.id, { is_archived: !chat.isArchived })
                }
                onDelete={() => handleDelete(chat.id)}
              />
            ))}
          </div>
        )}
      </div>

      <div className="px-2 mb-3 shrink-0">
        <div
          className="mx-1 p-3"
          style={{
            background: "rgba(255, 255, 255, 0.06)",
            borderRadius: "8px",
          }}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-base">💡</span>
            <span className="text-xs" style={{ color: "#F5A962" }}>
              Daily Tip
            </span>
          </div>
          <p
            className="text-xs"
            style={{ color: "#A8B8C8", lineHeight: "1.4" }}
          >
            Take a deep breath. Focus on the present moment.
          </p>
        </div>
      </div>

      <div className="px-2 mb-3 shrink-0">
        <button
          onClick={() => setShowHelpModal(true)}
          className="w-full flex items-center justify-center gap-2 text-white transition-all hover:opacity-90"
          style={{
            background: "#E07C6B",
            height: "40px",
            borderRadius: "8px",
            fontSize: "13px",
          }}
        >
          <Bell size={16} />
          <span>Get Help</span>
        </button>
      </div>

      <div
        className="flex items-center gap-3 px-3 py-3 cursor-pointer transition-all hover:bg-white/5 shrink-0"
        style={{ borderTop: "1px solid rgba(255, 255, 255, 0.1)" }}
        onClick={() => navigate("/profile")}
      >
        <div
          className="w-9 h-9 rounded-full flex items-center justify-center text-sm"
          style={{ background: "#4A90D9" }}
        >
          {userName
            .split(" ")
            .filter(Boolean)
            .map((part) => part[0]?.toUpperCase())
            .slice(0, 2)
            .join("") || "JD"}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm truncate">{userName}</div>
          <div className="text-xs opacity-50 truncate">Free plan</div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (confirm("Are you sure you want to log out?")) {
              logout();
              navigate("/");
            }
          }}
        >
          <LogOut
            size={14}
            className="opacity-40 hover:opacity-100 transition-opacity"
          />
        </button>
      </div>

      <AnimatePresence>
        {showHelpModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-md bg-white text-left"
              style={{ borderRadius: "20px", color: "#1C2B3A" }}
            >
              <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100">
                <div>
                  <h3 className="text-xl font-semibold">Get Help Now</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    If this feels urgent, please reach out to immediate support.
                  </p>
                </div>
                <button
                  onClick={() => setShowHelpModal(false)}
                  className="p-2 rounded-full hover:bg-gray-100 transition-all"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="px-6 py-5 space-y-4">
                <div
                  className="p-4"
                  style={{
                    background: "rgba(224, 124, 107, 0.08)",
                    borderRadius: "14px",
                    border: "1px solid rgba(224, 124, 107, 0.2)",
                  }}
                >
                  <div className="flex items-start gap-3">
                    <ShieldAlert size={20} style={{ color: "#E07C6B" }} />
                    <div>
                      <div className="font-medium">Emergency Support</div>
                      <p className="text-sm text-gray-600 mt-1">
                        If you might hurt yourself or someone else, call your local emergency number immediately.
                      </p>
                    </div>
                  </div>
                </div>

                <a
                  href="tel:988"
                  className="flex items-center gap-3 p-4 hover:bg-gray-50 transition-all"
                  style={{ borderRadius: "14px", border: "1px solid #E5E7EB" }}
                >
                  <Phone size={18} style={{ color: "#4A90D9" }} />
                  <div>
                    <div className="font-medium">Call or Text 988</div>
                    <p className="text-sm text-gray-600">
                      Suicide & Crisis Lifeline in the U.S. and Canada.
                    </p>
                  </div>
                </a>

                <div
                  className="flex items-start gap-3 p-4"
                  style={{ borderRadius: "14px", border: "1px solid #E5E7EB" }}
                >
                  <HeartHandshake size={18} style={{ color: "#7EC8A4" }} />
                  <div>
                    <div className="font-medium">Reach Someone You Trust</div>
                    <p className="text-sm text-gray-600 mt-1">
                      Consider messaging a friend, family member, counselor, or local mental health professional.
                    </p>
                  </div>
                </div>

                <p className="text-xs text-gray-500 leading-relaxed">
                  AuraChat can support reflection, but it is not a replacement for emergency or clinical care.
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </aside>
    <MobileBottomNav activeNav={activeNav} navigate={navigate} />
    </>
  );
}

function formatRelativeDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) return "Just now";
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString();
}

function NavItem({ icon: Icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 px-3 py-2 transition-all hover:bg-white/5"
      style={{
        background: active ? "rgba(74, 144, 217, 0.12)" : "transparent",
        color: active ? "#ffffff" : "rgba(255, 255, 255, 0.7)",
        borderRadius: "6px",
        fontSize: "14px",
      }}
    >
      {createElement(Icon, { size: 18 })}
      <span>{label}</span>
    </button>
  );
}

function MobileBottomNav({ activeNav, navigate }) {
  const items = [
    { id: "home", label: "Home", icon: Home, path: "/dashboard" },
    { id: "chat", label: "Chat", icon: MessageCircle, path: "/chat" },
    { id: "journal", label: "Journal", icon: BookOpen, path: "/journal" },
    { id: "safety", label: "Plan", icon: ClipboardList, path: "/safety-plan" },
    { id: "insights", label: "Insights", icon: BarChart3, path: "/insights" },
  ];

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 px-2 py-2"
      style={{
        background: "rgba(255, 255, 255, 0.96)",
        borderTop: "1px solid #E0E7EF",
        boxShadow: "0 -8px 28px rgba(44, 95, 138, 0.10)",
      }}
      aria-label="Mobile navigation"
    >
      <div className="grid grid-cols-5 gap-1">
        {items.map((item) => {
          const Icon = item.icon;
          const active = activeNav === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => navigate(item.path)}
              className="flex flex-col items-center justify-center gap-1 py-2 text-xs"
              style={{
                borderRadius: "12px",
                color: active ? "#2C5F8A" : "#66768F",
                background: active ? "rgba(74, 144, 217, 0.1)" : "transparent",
              }}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function RecentChatItem({
  chat,
  onClick,
  isEditing,
  editTitle,
  setEditTitle,
  onSaveRename,
  onCancelRename,
  menuOpen,
  onMenuToggle,
  onRename,
  onDelete,
  onTogglePin,
  onToggleArchive,
}) {
  return (
    <div className="relative group">
      {isEditing ? (
        <div
          className="px-3 py-2 rounded-lg"
          style={{ background: "rgba(255, 255, 255, 0.1)" }}
        >
          <input
            type="text"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onSaveRename();
              if (e.key === "Escape") onCancelRename();
            }}
            className="w-full bg-transparent text-sm outline-none mb-2"
            style={{ color: "white" }}
            autoFocus
          />
          <div className="flex gap-2">
            <button
              onClick={onSaveRename}
              className="flex-1 px-2 py-1 text-xs text-white"
              style={{ background: "#4A90D9", borderRadius: "6px" }}
            >
              Save
            </button>
            <button
              onClick={onCancelRename}
              className="flex-1 px-2 py-1 text-xs"
              style={{
                background: "rgba(255, 255, 255, 0.1)",
                borderRadius: "6px",
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          <div
            role="button"
            tabIndex={0}
            onClick={onClick}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick();
              }
            }}
            className="w-full px-3 py-2 rounded-lg hover:bg-white/5 transition-all text-left cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="text-sm truncate opacity-90 flex items-center gap-2">
                  <span className="truncate">{chat.title}</span>
                  {chat.isPinned && <Pin size={12} />}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <div className="text-xs opacity-50">{chat.time}</div>
                  {chat.tag && chat.tag !== "General" && (
                    <span
                      className="text-xs px-1.5 py-0.5 rounded"
                      style={{
                        background: "rgba(74, 144, 217, 0.2)",
                        color: "#A8C8E8",
                        fontSize: "10px",
                      }}
                    >
                      {chat.tag}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onMenuToggle();
                }}
                type="button"
                className="p-1 opacity-0 group-hover:opacity-60 hover:!opacity-100 transition-opacity"
              >
                <MoreVertical size={16} />
              </button>
            </div>
          </div>

          <AnimatePresence>
            {menuOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-full mt-1 bg-white py-2 z-50"
                style={{
                  borderRadius: "8px",
                  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
                  minWidth: "160px",
                }}
              >
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRename();
                  }}
                  type="button"
                  className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-100 transition-all text-left"
                >
                  <Edit3 size={14} style={{ color: "#4A90D9" }} />
                  <span className="text-sm" style={{ color: "#1C2B3A" }}>
                    Rename
                  </span>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onTogglePin();
                  }}
                  type="button"
                  className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-100 transition-all text-left"
                >
                  <Pin size={14} style={{ color: "#4A90D9" }} />
                  <span className="text-sm" style={{ color: "#1C2B3A" }}>
                    {chat.isPinned ? "Unpin" : "Pin"}
                  </span>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleArchive();
                  }}
                  type="button"
                  className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-100 transition-all text-left"
                >
                  {chat.isArchived ? (
                    <RotateCcw size={14} style={{ color: "#4A90D9" }} />
                  ) : (
                    <Archive size={14} style={{ color: "#9BAABB" }} />
                  )}
                  <span className="text-sm" style={{ color: "#1C2B3A" }}>
                    {chat.isArchived ? "Restore" : "Archive"}
                  </span>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete();
                  }}
                  type="button"
                  className="w-full flex items-center gap-3 px-4 py-2 hover:bg-red-50 transition-all text-left"
                >
                  <Trash2 size={14} style={{ color: "#E07C6B" }} />
                  <span className="text-sm" style={{ color: "#E07C6B" }}>
                    Delete
                  </span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
}
