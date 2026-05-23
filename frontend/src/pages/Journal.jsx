import { useCallback, useEffect, useMemo, useState } from "react";
import { BookOpen, Plus, Save, Search, Sparkles, Trash2 } from "lucide-react";
import Sidebar from "../components/Sidebar";
import API from "../api";
import { showToast } from "../components/Toast";

const blankEntry = {
  title: "Today’s Reflection",
  mood_label: "",
  mood_score: 6,
  trigger: "",
  thought: "",
  body_feeling: "",
  reframe: "",
  next_step: "",
  tags: [],
};

export default function Journal() {
  const [entries, setEntries] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [draft, setDraft] = useState(blankEntry);
  const [query, setQuery] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const selectedEntry = useMemo(
    () => entries.find((entry) => entry.id === selectedId),
    [entries, selectedId],
  );

  const loadEntries = useCallback(async (search = "") => {
    setIsLoading(true);
    try {
      const { data } = await API.get("/wellness/journals", {
        params: search ? { q: search } : {},
      });
      setEntries(data.entries || []);
      if (!selectedId && data.entries?.[0]) {
        setSelectedId(data.entries[0].id);
        setDraft(data.entries[0]);
      }
    } catch {
      showToast("Could not load journal entries.");
    } finally {
      setIsLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    const timeout = setTimeout(() => loadEntries(query.trim()), 250);
    return () => clearTimeout(timeout);
  }, [loadEntries, query]);

  useEffect(() => {
    if (selectedEntry) {
      setDraft({
        ...selectedEntry,
        tags: selectedEntry.tags || [],
      });
    }
  }, [selectedEntry]);

  const startNewEntry = () => {
    setSelectedId(null);
    setDraft(blankEntry);
  };

  const updateDraft = (field, value) => {
    setDraft((current) => ({ ...current, [field]: value }));
  };

  const saveEntry = async () => {
    setIsSaving(true);
    try {
      const payload = {
        ...draft,
        tags: typeof draft.tags === "string"
          ? draft.tags.split(",").map((tag) => tag.trim()).filter(Boolean)
          : draft.tags,
      };
      const { data } = selectedId
        ? await API.put(`/wellness/journals/${selectedId}`, payload)
        : await API.post("/wellness/journals", payload);

      setEntries((current) => {
        const exists = current.some((entry) => entry.id === data.id);
        return exists
          ? current.map((entry) => (entry.id === data.id ? data : entry))
          : [data, ...current];
      });
      setSelectedId(data.id);
      setDraft(data);
      showToast("Journal saved.", "success");
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save journal.");
    } finally {
      setIsSaving(false);
    }
  };

  const deleteEntry = async (entryId) => {
    if (!window.confirm("Delete this journal entry?")) return;
    try {
      await API.delete(`/wellness/journals/${entryId}`);
      setEntries((current) => current.filter((entry) => entry.id !== entryId));
      if (selectedId === entryId) {
        startNewEntry();
      }
      showToast("Journal deleted.", "success");
    } catch {
      showToast("Could not delete journal entry.");
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-5 pb-24 md:p-10" style={{ background: "#F7FAFD" }}>
        <div className="max-w-[1300px] mx-auto space-y-6">
          <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 mb-3 text-sm" style={{ background: "rgba(126, 200, 164, 0.14)", color: "#2F7A57", borderRadius: "999px" }}>
                <BookOpen size={16} />
                Structured reflection
              </div>
              <h1 className="text-3xl md:text-4xl" style={{ color: "var(--aura-text-primary)" }}>
                Journal
              </h1>
              <p className="mt-2 max-w-2xl" style={{ color: "var(--aura-text-secondary)" }}>
                Capture what happened, what you felt, and one next step without turning it into a long essay.
              </p>
            </div>
            <button
              onClick={startNewEntry}
              className="inline-flex items-center justify-center gap-2 px-5 py-3 text-white"
              style={{ background: "#4A90D9", borderRadius: "12px" }}
            >
              <Plus size={18} />
              New Entry
            </button>
          </header>

          <section className="grid grid-cols-1 xl:grid-cols-[360px_1fr] gap-5">
            <aside className="bg-white p-4 h-fit" style={{ borderRadius: "16px", border: "1px solid #E4ECF4" }}>
              <div className="relative mb-4">
                <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#66768F" }} />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search reflections"
                  className="w-full pl-10 pr-3 py-3 text-sm focus:outline-none focus:ring-2"
                  style={{ border: "1px solid #D0DCE8", borderRadius: "12px", color: "var(--aura-text-primary)" }}
                />
              </div>

              <div className="space-y-2 max-h-[calc(100vh-260px)] overflow-y-auto">
                {isLoading ? (
                  <p className="p-4 text-sm" style={{ color: "var(--aura-text-secondary)" }}>Loading entries...</p>
                ) : entries.length === 0 ? (
                  <p className="p-4 text-sm" style={{ color: "var(--aura-text-secondary)" }}>No journal entries yet.</p>
                ) : (
                  entries.map((entry) => (
                    <button
                      key={entry.id}
                      type="button"
                      onClick={() => setSelectedId(entry.id)}
                      className="w-full p-4 text-left transition-all"
                      style={{
                        borderRadius: "12px",
                        background: selectedId === entry.id ? "rgba(74, 144, 217, 0.1)" : "#F7FAFD",
                        border: selectedId === entry.id ? "1px solid rgba(74, 144, 217, 0.35)" : "1px solid transparent",
                      }}
                    >
                      <div className="font-medium truncate" style={{ color: "var(--aura-text-primary)" }}>{entry.title}</div>
                      <div className="text-xs mt-1" style={{ color: "var(--aura-text-secondary)" }}>
                        {new Date(entry.created_at).toLocaleDateString()}
                      </div>
                      {entry.next_step && (
                        <p className="text-sm mt-2 line-clamp-2" style={{ color: "var(--aura-text-secondary)" }}>{entry.next_step}</p>
                      )}
                    </button>
                  ))
                )}
              </div>
            </aside>

            <article className="bg-white p-5 md:p-7" style={{ borderRadius: "16px", border: "1px solid #E4ECF4" }}>
              <div className="grid grid-cols-1 lg:grid-cols-[1fr_220px] gap-4 mb-5">
                <input
                  value={draft.title}
                  onChange={(event) => updateDraft("title", event.target.value)}
                  className="text-2xl md:text-3xl focus:outline-none"
                  style={{ color: "var(--aura-text-primary)" }}
                />
                <div className="grid grid-cols-2 gap-3">
                  <label className="text-sm">
                    <span style={{ color: "var(--aura-text-secondary)" }}>Mood</span>
                    <input
                      value={draft.mood_label || ""}
                      onChange={(event) => updateDraft("mood_label", event.target.value)}
                      placeholder="Calm"
                      className="mt-1 w-full px-3 py-2 focus:outline-none focus:ring-2"
                      style={{ border: "1px solid #D0DCE8", borderRadius: "10px", color: "var(--aura-text-primary)" }}
                    />
                  </label>
                  <label className="text-sm">
                    <span style={{ color: "var(--aura-text-secondary)" }}>Score</span>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={draft.mood_score || ""}
                      onChange={(event) => updateDraft("mood_score", Number(event.target.value))}
                      className="mt-1 w-full px-3 py-2 focus:outline-none focus:ring-2"
                      style={{ border: "1px solid #D0DCE8", borderRadius: "10px", color: "var(--aura-text-primary)" }}
                    />
                  </label>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <TextArea label="Trigger" field="trigger" value={draft.trigger} onChange={updateDraft} placeholder="What set this off?" />
                <TextArea label="Body Feeling" field="body_feeling" value={draft.body_feeling} onChange={updateDraft} placeholder="Where do you feel it physically?" />
                <TextArea label="Thought" field="thought" value={draft.thought} onChange={updateDraft} placeholder="What thought kept repeating?" tall />
                <TextArea label="Helpful Reframe" field="reframe" value={draft.reframe} onChange={updateDraft} placeholder="What is a kinder or more balanced view?" tall />
              </div>

              <div className="mt-4">
                <TextArea label="Next Step" field="next_step" value={draft.next_step} onChange={updateDraft} placeholder="One small thing you can do next." />
              </div>

              <div className="mt-5 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex items-center gap-2 text-sm" style={{ color: "var(--aura-text-secondary)" }}>
                  <Sparkles size={16} />
                  Keep it honest, short, and useful to future you.
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedId && (
                    <button
                      type="button"
                      onClick={() => deleteEntry(selectedId)}
                      className="inline-flex items-center gap-2 px-4 py-2"
                      style={{ color: "#E07C6B", border: "1px solid #F1D1CC", borderRadius: "10px" }}
                    >
                      <Trash2 size={16} />
                      Delete
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={saveEntry}
                    disabled={isSaving}
                    className="inline-flex items-center gap-2 px-5 py-2 text-white disabled:opacity-50"
                    style={{ background: "#2C5F8A", borderRadius: "10px" }}
                  >
                    <Save size={16} />
                    {isSaving ? "Saving..." : "Save Entry"}
                  </button>
                </div>
              </div>
            </article>
          </section>
        </div>
      </main>
    </div>
  );
}

function TextArea({ label, field, value, onChange, placeholder, tall = false }) {
  return (
    <label className="block text-sm">
      <span style={{ color: "var(--aura-text-secondary)" }}>{label}</span>
      <textarea
        value={value || ""}
        onChange={(event) => onChange(field, event.target.value)}
        placeholder={placeholder}
        rows={tall ? 7 : 4}
        className="mt-1 w-full px-3 py-3 resize-none focus:outline-none focus:ring-2"
        style={{
          border: "1px solid #D0DCE8",
          borderRadius: "12px",
          color: "var(--aura-text-primary)",
          lineHeight: 1.5,
        }}
      />
    </label>
  );
}
