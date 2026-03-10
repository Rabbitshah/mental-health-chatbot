import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  MoreVertical,
  Trash2,
  Edit3,
  MessageCircle,
  Calendar,
  Tag,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import Sidebar from "../components/Sidebar";
import API from "../api";

export default function History() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [chats, setChats] = useState([]);
  const [menuOpen, setMenuOpen] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const { data } = await API.get("/history/");
      setChats(data.map(chat => ({
        id: chat.id,
        title: chat.title,
        preview: chat.preview || "Started a new conversation...",
        date: new Date(chat.created_at).toLocaleDateString(),
        tag: chat.tag || "General",
        messageCount: chat.message_count
      })));
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id) => {
    if (confirm("Are you sure you want to delete this conversation?")) {
      try {
         await API.delete(`/history/${id}`);
         setChats(chats.filter((chat) => chat.id !== id));
      } catch (e) { console.error(e); }
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
        setChats(
          chats.map((chat) =>
            chat.id === id ? { ...chat, title: editTitle.trim() } : chat,
          ),
        );
      } catch (e) { console.error(e); }
    }
    setEditingId(null);
    setEditTitle("");
  };

  const cancelRename = () => {
    setEditingId(null);
    setEditTitle("");
  };

  const filteredChats = chats.filter((chat) => {
    const matchesSearch =
      chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      chat.preview.toLowerCase().includes(searchQuery.toLowerCase()) ||
      chat.tag.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getTagColor = (tag) => {
    const colors = {
      Anxiety: "#4A90D9",
      Stress: "#E07C6B",
      Reflection: "#7EC8A4",
      Health: "#2C5F8A",
      Goals: "#F5A962",
      Mindfulness: "#7EC8A4",
      Relationships: "#4A90D9",
      Career: "#2C5F8A",
      General: "#9BAABB"
    };
    return colors[tag] || "#4A90D9";
  };


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
          >
            <h1
              className="text-4xl mb-2"
              style={{ color: "var(--aura-text-primary)" }}
            >
              Chat History
            </h1>
            <p
              className="text-base"
              style={{ color: "var(--aura-text-secondary)" }}
            >
              Review and continue your previous conversations
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="bg-white p-6"
            style={{
              borderRadius: "20px",
              boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
            }}
          >
            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <Search
                  size={20}
                  className="absolute left-4 top-1/2 -translate-y-1/2"
                  style={{ color: "#9BAABB" }}
                />
                <input
                  type="text"
                  placeholder="Search conversations, topics, or keywords..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 outline-none text-base"
                  style={{
                    height: "48px",
                    background: "#F7FAFD",
                    borderRadius: "12px",
                    color: "var(--aura-text-primary)",
                    border: "1px solid #E0E7EF",
                  }}
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="absolute right-4 top-1/2 -translate-y-1/2 hover:bg-gray-200 rounded-full p-1 transition-all"
                  >
                    <X size={16} style={{ color: "#9BAABB" }} />
                  </button>
                )}
              </div>

              <div className="flex gap-2">
                {["all", "today", "week", "month"].map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setSelectedFilter(filter)}
                    className="px-4 py-2 text-sm transition-all capitalize"
                    style={{
                      background:
                        selectedFilter === filter ? "#4A90D9" : "transparent",
                      color:
                        selectedFilter === filter
                          ? "white"
                          : "var(--aura-text-secondary)",
                      borderRadius: "12px",
                      border:
                        selectedFilter === filter
                          ? "none"
                          : "1px solid #E0E7EF",
                    }}
                  >
                    {filter === "all" ? "All Time" : `This ${filter}`}
                  </button>
                ))}
              </div>
            </div>

            <div
              className="mt-4 pt-4"
              style={{ borderTop: "1px solid #E0E7EF" }}
            >
              <span
                className="text-sm"
                style={{ color: "var(--aura-text-secondary)" }}
              >
                {filteredChats.length}{" "}
                {filteredChats.length === 1 ? "conversation" : "conversations"}{" "}
                found
              </span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="space-y-4"
          >
            <AnimatePresence mode="popLayout">
              {filteredChats.map((chat, index) => (
                <motion.div
                  key={chat.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  onClick={() => navigate(`/chat/${chat.id}`)}
                  className="bg-white p-6 hover:-translate-y-0.5 transition-all relative cursor-pointer"
                  style={{
                    borderRadius: "20px",
                    boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
                  }}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                      style={{ background: `${getTagColor(chat.tag)}15` }}
                    >
                      <MessageCircle
                        size={22}
                        style={{ color: getTagColor(chat.tag) }}
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      {editingId === chat.id ? (
                        <div className="flex items-center gap-2 mb-2">
                          <input
                            type="text"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") saveRename(chat.id);
                              if (e.key === "Escape") cancelRename();
                            }}
                            className="flex-1 px-3 py-1 text-base outline-none"
                            style={{
                              border: "2px solid #4A90D9",
                              borderRadius: "8px",
                              color: "var(--aura-text-primary)",
                            }}
                            autoFocus
                          />
                          <button
                            onClick={() => saveRename(chat.id)}
                            className="px-4 py-1 text-sm text-white"
                            style={{
                              background: "#4A90D9",
                              borderRadius: "8px",
                            }}
                          >
                            Save
                          </button>
                          <button
                            onClick={cancelRename}
                            className="px-4 py-1 text-sm"
                            style={{
                              background: "#F0F4F8",
                              color: "var(--aura-text-secondary)",
                              borderRadius: "8px",
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <h3
                          className="text-lg mb-2"
                          style={{ color: "var(--aura-text-primary)" }}
                        >
                          {chat.title}
                        </h3>
                      )}
                      <p
                        className="text-sm mb-3 line-clamp-2"
                        style={{ color: "var(--aura-text-secondary)" }}
                      >
                        {chat.preview}
                      </p>
                      <div className="flex items-center gap-3 flex-wrap">
                        <span
                          className="text-xs px-3 py-1"
                          style={{
                            background: `${getTagColor(chat.tag)}15`,
                            color: getTagColor(chat.tag),
                            borderRadius: "8px",
                          }}
                        >
                          <Tag size={12} className="inline mr-1" />
                          {chat.tag}
                        </span>
                        <span className="text-xs" style={{ color: "#9BAABB" }}>
                          <Calendar size={12} className="inline mr-1" />
                          {chat.date}
                        </span>
                        <span className="text-xs" style={{ color: "#9BAABB" }}>
                          <MessageCircle size={12} className="inline mr-1" />
                          {chat.messageCount} messages
                        </span>
                      </div>
                    </div>

                    <div className="relative">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setMenuOpen(menuOpen === chat.id ? null : chat.id)
                        }}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-all"
                      >
                        <MoreVertical
                          size={20}
                          style={{ color: "var(--aura-text-secondary)" }}
                        />
                      </button>

                      <AnimatePresence>
                        {menuOpen === chat.id && (
                          <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: -10 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: -10 }}
                            transition={{ duration: 0.15 }}
                            className="absolute right-0 top-full mt-2 bg-white py-2 z-10"
                            style={{
                              borderRadius: "12px",
                              boxShadow: "0 8px 32px rgba(44, 95, 138, 0.15)",
                              minWidth: "180px",
                            }}
                          >
                            <button
                              onClick={(e) => { e.stopPropagation(); handleRename(chat.id, chat.title); }}
                              className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-50 transition-all text-left"
                            >
                              <Edit3 size={16} style={{ color: "#4A90D9" }} />
                              <span
                                className="text-sm"
                                style={{ color: "var(--aura-text-primary)" }}
                              >
                                Rename
                              </span>
                            </button>
                            <button
                              onClick={(e) => { e.stopPropagation(); handleDelete(chat.id); }}
                              className="w-full flex items-center gap-3 px-4 py-2 hover:bg-red-50 transition-all text-left"
                            >
                              <Trash2 size={16} style={{ color: "#E07C6B" }} />
                              <span
                                className="text-sm"
                                style={{ color: "#E07C6B" }}
                              >
                                Delete
                              </span>
                            </button>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {filteredChats.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-white p-12 text-center"
                style={{
                  borderRadius: "20px",
                  boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
                }}
              >
                <div
                  className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4"
                  style={{ background: "rgba(74, 144, 217, 0.1)" }}
                >
                  <Search size={32} style={{ color: "#4A90D9" }} />
                </div>
                <h3
                  className="text-xl mb-2"
                  style={{ color: "var(--aura-text-primary)" }}
                >
                  No conversations found
                </h3>
                <p
                  className="text-base"
                  style={{ color: "var(--aura-text-secondary)" }}
                >
                  Try adjusting your search or filters
                </p>
              </motion.div>
            )}
          </motion.div>
        </div>
      </main>
    </div>
  );
}
