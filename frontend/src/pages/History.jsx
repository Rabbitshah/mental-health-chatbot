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
  Pin,
  Archive,
  RotateCcw,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import Sidebar from "../components/Sidebar";
import API from "../api";

export default function History() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [showArchived, setShowArchived] = useState(false);
  const [chats, setChats] = useState([]);
  const [selectedChatIds, setSelectedChatIds] = useState([]);
  const [selectionMode, setSelectionMode] = useState(false);
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [menuOpen, setMenuOpen] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchHistory(searchQuery);
    }, 250);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, showArchived]);

  const fetchHistory = async (query = "") => {
    setIsLoading(true);
    setLoadError("");
    try {
      const trimmedQuery = query.trim();
      const { data } = await API.get("/history/", {
        params: {
          ...(trimmedQuery ? { q: trimmedQuery } : {}),
          include_archived: showArchived,
        },
      });
      setChats(data.map(chat => ({
        id: chat.id,
        title: chat.title,
        preview: chat.preview || "Started a new conversation...",
        date: new Date(chat.created_at).toLocaleDateString(),
        createdAt: chat.created_at,
        tag: chat.tag || "General",
        messageCount: chat.message_count,
        isPinned: chat.is_pinned,
        isArchived: chat.is_archived,
      })));
    } catch (e) {
      console.error(e);
      setLoadError("We couldn't load your saved conversations right now.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (confirm("Are you sure you want to delete this conversation?")) {
      try {
         await API.delete(`/history/${id}`);
         setChats(chats.filter((chat) => chat.id !== id));
         setSelectedChatIds((current) => current.filter((chatId) => chatId !== id));
         window.dispatchEvent(new Event("sessions-updated"));
      } catch (e) { console.error(e); }
      setMenuOpen(null);
    }
  };

  const toggleSelectionMode = () => {
    setSelectionMode((current) => !current);
    setSelectedChatIds([]);
    setMenuOpen(null);
  };

  const toggleChatSelection = (id) => {
    setSelectedChatIds((current) =>
      current.includes(id)
        ? current.filter((chatId) => chatId !== id)
        : [...current, id],
    );
  };

  const selectAllVisible = () => {
    setSelectedChatIds(filteredChats.map((chat) => chat.id));
  };

  const clearSelection = () => {
    setSelectedChatIds([]);
  };

  const handleBulkDelete = async () => {
    if (selectedChatIds.length === 0) {
      return;
    }

    if (!confirm(`Delete ${selectedChatIds.length} selected conversation${selectedChatIds.length === 1 ? "" : "s"}? This cannot be undone.`)) {
      return;
    }

    setIsBulkDeleting(true);
    try {
      await API.delete("/history/bulk", {
        data: { session_ids: selectedChatIds },
      });
      setChats((current) => current.filter((chat) => !selectedChatIds.includes(chat.id)));
      setSelectedChatIds([]);
      setSelectionMode(false);
      window.dispatchEvent(new Event("sessions-updated"));
    } catch (e) {
      console.error(e);
      setLoadError("We couldn't delete the selected conversations right now.");
    } finally {
      setIsBulkDeleting(false);
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
        window.dispatchEvent(new Event("sessions-updated"));
      } catch (e) { console.error(e); }
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
      setChats((current) =>
        current
          .map((chat) =>
            chat.id === id
              ? {
                  ...chat,
                  isPinned: data.is_pinned,
                  isArchived: data.is_archived,
                }
              : chat,
          )
          .filter((chat) => showArchived || !chat.isArchived)
          .sort((a, b) => {
            if (a.isPinned !== b.isPinned) {
              return Number(b.isPinned) - Number(a.isPinned);
            }
            return new Date(b.createdAt) - new Date(a.createdAt);
          }),
      );
      setMenuOpen(null);
      window.dispatchEvent(new Event("sessions-updated"));
    } catch (e) {
      console.error(e);
      setLoadError("We couldn't update that conversation right now.");
    }
  };

  const filteredChats = chats.filter((chat) => {
    const chatDate = new Date(chat.createdAt);
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const startOfTomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
    const sevenDaysAgo = new Date(now);
    sevenDaysAgo.setDate(now.getDate() - 7);
    const thirtyDaysAgo = new Date(now);
    thirtyDaysAgo.setDate(now.getDate() - 30);

    let matchesFilter = true;

    if (selectedFilter === "today") {
      matchesFilter = chatDate >= startOfToday && chatDate < startOfTomorrow;
    } else if (selectedFilter === "week") {
      matchesFilter = chatDate >= sevenDaysAgo;
    } else if (selectedFilter === "month") {
      matchesFilter = chatDate >= thirtyDaysAgo;
    }

    return matchesFilter;
  });

  const allVisibleSelected =
    filteredChats.length > 0 &&
    filteredChats.every((chat) => selectedChatIds.includes(chat.id));

  useEffect(() => {
    setSelectedChatIds((current) =>
      current.filter((id) => chats.some((chat) => chat.id === id)),
    );
  }, [chats]);

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
                <button
                  onClick={toggleSelectionMode}
                  className="px-4 py-2 text-sm transition-all"
                  style={{
                    background: selectionMode ? "#2C5F8A" : "transparent",
                    color: selectionMode ? "white" : "var(--aura-text-secondary)",
                    borderRadius: "12px",
                    border: selectionMode ? "none" : "1px solid #E0E7EF",
                  }}
                >
                  {selectionMode ? "Cancel Select" : "Select Multiple"}
                </button>
                <button
                  onClick={() => setShowArchived((current) => !current)}
                  className="px-4 py-2 text-sm transition-all"
                  style={{
                    background: showArchived ? "#4A90D9" : "transparent",
                    color: showArchived ? "white" : "var(--aura-text-secondary)",
                    borderRadius: "12px",
                    border: showArchived ? "none" : "1px solid #E0E7EF",
                  }}
                >
                  {showArchived ? "Viewing Archived" : "Show Archived"}
                </button>
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

            {selectionMode && !isLoading && !loadError && (
              <div
                className="mt-4 pt-4 flex items-center justify-between gap-4 flex-wrap"
                style={{ borderTop: "1px solid #E0E7EF" }}
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    onClick={allVisibleSelected ? clearSelection : selectAllVisible}
                    className="px-4 py-2 text-sm transition-all"
                    style={{
                      background: "rgba(74, 144, 217, 0.08)",
                      color: "#4A90D9",
                      borderRadius: "12px",
                    }}
                  >
                    {allVisibleSelected ? "Clear Visible" : "Select Visible"}
                  </button>
                  <span
                    className="text-sm"
                    style={{ color: "var(--aura-text-secondary)" }}
                  >
                    {selectedChatIds.length} selected
                  </span>
                </div>

                <button
                  onClick={handleBulkDelete}
                  disabled={selectedChatIds.length === 0 || isBulkDeleting}
                  className="px-4 py-2 text-sm text-white transition-all disabled:opacity-50"
                  style={{
                    background: "#E07C6B",
                    borderRadius: "12px",
                  }}
                >
                  {isBulkDeleting ? "Deleting..." : `Delete Selected${selectedChatIds.length ? ` (${selectedChatIds.length})` : ""}`}
                </button>
              </div>
            )}

            <div
              className="mt-4 pt-4"
              style={{ borderTop: "1px solid #E0E7EF" }}
            >
              <span
                className="text-sm"
                style={{ color: "var(--aura-text-secondary)" }}
              >
                {isLoading
                  ? "Loading conversations..."
                  : loadError
                  ? "History unavailable"
                  : `${filteredChats.length} ${filteredChats.length === 1 ? "conversation" : "conversations"} found${searchQuery.trim() ? ` for "${searchQuery.trim()}"` : ""}${showArchived ? " in archived chats" : ""}`}
              </span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="space-y-4"
          >
            {isLoading ? (
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
                  Loading your conversations
                </h3>
                <p
                  className="text-base"
                  style={{ color: "var(--aura-text-secondary)" }}
                >
                  Pulling your saved sessions and filters into view.
                </p>
              </motion.div>
            ) : loadError ? (
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
                  style={{ background: "rgba(224, 124, 107, 0.12)" }}
                >
                  <X size={32} style={{ color: "#E07C6B" }} />
                </div>
                <h3
                  className="text-xl mb-2"
                  style={{ color: "var(--aura-text-primary)" }}
                >
                  History is temporarily unavailable
                </h3>
                <p
                  className="text-base mb-5"
                  style={{ color: "var(--aura-text-secondary)" }}
                >
                  {loadError}
                </p>
                <button
                  onClick={() => fetchHistory(searchQuery)}
                  className="px-5 py-2.5 text-white hover:opacity-90 transition-all"
                  style={{ background: "#4A90D9", borderRadius: "12px" }}
                >
                  Try Again
                </button>
              </motion.div>
            ) : (
              <>
                <AnimatePresence mode="popLayout">
                  {filteredChats.map((chat, index) => (
                    <motion.div
                      key={chat.id}
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -100 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                      onClick={() => {
                        if (selectionMode) {
                          toggleChatSelection(chat.id);
                          return;
                        }
                        navigate(`/chat/${chat.id}`);
                      }}
                      className="bg-white p-6 hover:-translate-y-0.5 transition-all relative cursor-pointer"
                      style={{
                        borderRadius: "20px",
                        boxShadow: "0 4px 24px rgba(44, 95, 138, 0.08)",
                      }}
                    >
                      <div className="flex items-start gap-4">
                        {selectionMode && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleChatSelection(chat.id);
                            }}
                            className="w-6 h-6 mt-1 shrink-0 rounded-md border flex items-center justify-center transition-all"
                            style={{
                              borderColor: selectedChatIds.includes(chat.id) ? "#4A90D9" : "#D0DCE8",
                              background: selectedChatIds.includes(chat.id) ? "#4A90D9" : "white",
                              color: "white",
                            }}
                          >
                            {selectedChatIds.includes(chat.id) ? "X" : ""}
                          </button>
                        )}
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
                              className="text-lg mb-2 flex items-center gap-2"
                              style={{ color: "var(--aura-text-primary)" }}
                            >
                              <span>{chat.title}</span>
                              {chat.isPinned && (
                                <Pin size={14} style={{ color: "#4A90D9" }} />
                              )}
                              {chat.isArchived && (
                                <Archive size={14} style={{ color: "#9BAABB" }} />
                              )}
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
                          {!selectionMode && (
                            <>
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
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleStatusUpdate(chat.id, { is_pinned: !chat.isPinned });
                                      }}
                                      className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-50 transition-all text-left"
                                    >
                                      <Pin size={16} style={{ color: "#4A90D9" }} />
                                      <span
                                        className="text-sm"
                                        style={{ color: "var(--aura-text-primary)" }}
                                      >
                                        {chat.isPinned ? "Unpin" : "Pin"}
                                      </span>
                                    </button>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleStatusUpdate(chat.id, { is_archived: !chat.isArchived });
                                      }}
                                      className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-50 transition-all text-left"
                                    >
                                      {chat.isArchived ? (
                                        <RotateCcw size={16} style={{ color: "#4A90D9" }} />
                                      ) : (
                                        <Archive size={16} style={{ color: "#9BAABB" }} />
                                      )}
                                      <span
                                        className="text-sm"
                                        style={{ color: "var(--aura-text-primary)" }}
                                      >
                                        {chat.isArchived ? "Restore" : "Archive"}
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
                            </>
                          )}
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
                      {chats.length === 0
                        ? searchQuery.trim()
                          ? "No matching conversations were found. Try a different keyword."
                          : showArchived
                          ? "Archived conversations will appear here."
                          : "Start a new chat and it will appear here."
                        : "Try adjusting your search or filters."}
                    </p>
                  </motion.div>
                )}
              </>
            )}
          </motion.div>
        </div>
      </main>
    </div>
  );
}
