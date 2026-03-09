import { useNavigate, useLocation } from "react-router-dom";
import {
  Home,
  MessageCircle,
  Clock,
  BarChart3,
  Settings,
  LogOut,
  Bell,
  MoreVertical,
  Edit3,
  Trash2,
} from "lucide-react";
import { useState, createElement } from "react";
import { motion, AnimatePresence } from "motion/react";

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [showRecents, setShowRecents] = useState(true);
  const [recentChats, setRecentChats] = useState([
    { id: "1", title: "Morning anxiety talk", time: "2h ago" },
    { id: "2", title: "Work stress discussion", time: "Yesterday" },
    { id: "3", title: "Weekend reflection", time: "2 days ago" },
  ]);

  const getActiveNav = () => {
    const path = location.pathname;
    if (path === "/dashboard") return "home";
    if (path === "/chat") return "chat";
    if (path === "/history") return "history";
    if (path === "/insights") return "insights";
    if (path === "/profile") return "settings";
    return "chat";
  };

  const activeNav = getActiveNav();

  const handleDelete = (id) => {
    if (confirm("Are you sure you want to delete this chat?")) {
      setRecentChats(recentChats.filter((c) => c.id !== id));
      setMenuOpen(null);
    }
  };

  const handleRename = (id, currentTitle) => {
    setEditingId(id);
    setEditTitle(currentTitle);
    setMenuOpen(null);
  };

  const saveRename = (id) => {
    if (editTitle.trim()) {
      setRecentChats(
        recentChats.map((chat) =>
          chat.id === id ? { ...chat, title: editTitle.trim() } : chat,
        ),
      );
    }
    setEditingId(null);
    setEditTitle("");
  };

  const cancelRename = () => {
    setEditingId(null);
    setEditTitle("");
  };

  return (
    <aside
      className="flex flex-col h-screen"
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
                onClick={() => navigate("/chat")}
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
          JD
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm truncate">Jane Doe</div>
          <div className="text-xs opacity-50 truncate">Free plan</div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (confirm("Are you sure you want to log out?")) {
              localStorage.removeItem("token");
              localStorage.removeItem("user");
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
    </aside>
  );
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
          <button
            onClick={onClick}
            className="w-full px-3 py-2 rounded-lg hover:bg-white/5 transition-all text-left"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="text-sm truncate opacity-90">{chat.title}</div>
                <div className="text-xs opacity-50 mt-0.5">{chat.time}</div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onMenuToggle();
                }}
                className="p-1 opacity-0 group-hover:opacity-60 hover:!opacity-100 transition-opacity"
              >
                <MoreVertical size={16} />
              </button>
            </div>
          </button>

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
                    onDelete();
                  }}
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
