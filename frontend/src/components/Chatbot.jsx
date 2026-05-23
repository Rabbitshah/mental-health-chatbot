import { useState, useRef, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  MessageCircle,
  Send,
  RefreshCw,
  Copy,
  Share2,
  Phone,
  X,
  ShieldCheck,
  Wind,
  TimerReset,
  HeartPulse,
} from "lucide-react";
import { motion } from "motion/react";
import ReactMarkdown from "react-markdown";
import API from "../api";
import Sidebar from "./Sidebar";
import CrisisBanner from "./CrisisBanner";
import NotificationBell from "./NotificationBell";
import { showToast } from "./Toast";

export default function Chatbot() {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [userName, setUserName] = useState("Jane Doe");
  const [showCrisisBanner, setShowCrisisBanner] = useState(false);
  const [showCrisisPanel, setShowCrisisPanel] = useState(false);
  const [crisisResources, setCrisisResources] = useState([]);
  const [activeSupportTool, setActiveSupportTool] = useState("grounding");
  const [breathingActive, setBreathingActive] = useState(false);
  const messagesEndRef = useRef(null);
  const draftStorageKey = sessionId
    ? `aurachat-draft-${sessionId}`
    : "aurachat-draft-new";

  useEffect(() => {
    const isLoggedIn = localStorage.getItem("isLoggedIn") === "true";
    if (!isLoggedIn) {
      navigate("/login");
      return;
    }

    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        if (user?.name) setUserName(user.name);
      } catch {
        // Ignore malformed local user payload and keep defaults.
      }
    }

    const savedDraft = localStorage.getItem(draftStorageKey);
    if (savedDraft) {
      setInputValue(savedDraft);
    } else {
      setInputValue("");
    }
    
    // Fetch history if sessionId is in URL
    if (sessionId) {
      const fetchHistory = async () => {
        try {
          const res = await API.get(`/history/${sessionId}`);
          const formattedMessages = res.data.map(msg => ({
            id: msg.id.toString(),
            text: msg.text,
            sender: msg.sender,
            timestamp: new Date(msg.created_at)
          }));
          setMessages(formattedMessages);
        } catch (error) {
          console.error("Failed to load history", error);
        }
      };
      fetchHistory();
    } else {
      setMessages([]);
    }
  }, [draftStorageKey, navigate, sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  useEffect(() => {
    if (inputValue.trim()) {
      localStorage.setItem(draftStorageKey, inputValue);
    } else {
      localStorage.removeItem(draftStorageKey);
    }
  }, [draftStorageKey, inputValue]);

  const streamAssistantMessage = async (messageId, fullText) => {
    const chunkSize = 12;
    const delayMs = 18;

    for (let index = chunkSize; index <= fullText.length; index += chunkSize) {
      const partialText = fullText.slice(0, index);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === messageId ? { ...message, text: partialText } : message,
        ),
      );
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }

    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId ? { ...message, text: fullText } : message,
      ),
    );
  };

  const sendPrompt = async (prompt) => {
    const payload = { message: prompt };
    if (sessionId) {
      payload.session_id = parseInt(sessionId, 10);
    }

    const res = await API.post("/chat", payload);

    if (!sessionId && res.data.session_id) {
      navigate(`/chat/${res.data.session_id}`, { replace: true });
    }

    // Notify Sidebar to refresh its session list
    window.dispatchEvent(new Event("sessions-updated"));

    if (res.data?.crisis_detected) {
      setShowCrisisBanner(true);
      setShowCrisisPanel(true);
      setCrisisResources(res.data?.emergency_resources || []);
    }

    const aiText =
      res.data?.response ||
      res.data?.reply ||
      "I hear you. I am here to listen and support you.";
    const aiMessageId = (Date.now() + 1).toString();
    const aiMessage = {
      id: aiMessageId,
      text: "",
      sender: "ai",
      timestamp: new Date(),
      isError: false,
      promptText: prompt,
    };
    setMessages((prev) => [...prev, aiMessage]);
    setIsThinking(false);
    await streamAssistantMessage(aiMessageId, aiText);
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      text: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const prompt = inputValue;
    setInputValue("");
    localStorage.removeItem(draftStorageKey);
    setIsThinking(true);

    try {
      await sendPrompt(prompt);
    } catch (error) {
      let errorMsg = "I could not connect right now. Please try again in a moment.";
      if (error.response?.status === 429) {
          errorMsg = "You're sending messages too quickly. Please pause for a moment to let me catch up!";
      }

      const aiMessage = {
        id: (Date.now() + 1).toString(),
        text: errorMsg,
        sender: "ai",
        timestamp: new Date(),
        isError: true,
        promptText: prompt,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleRetryOrRegenerate = async (promptText, messageId) => {
    if (!promptText || isThinking) return;

    setMessages((prev) => prev.filter((message) => message.id !== messageId));
    setIsThinking(true);

    try {
      await sendPrompt(promptText);
    } catch (error) {
      let errorMsg = "I could not connect right now. Please try again in a moment.";
      if (error.response?.status === 429) {
        errorMsg = "You're sending messages too quickly. Please pause for a moment to let me catch up!";
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          text: errorMsg,
          sender: "ai",
          timestamp: new Date(),
          isError: true,
          promptText,
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleCopyMessage = async (text) => {
    if (!text) return;

    try {
      await navigator.clipboard.writeText(text);
      showToast("Message copied.", "success");
    } catch (error) {
      console.error("Failed to copy message", error);
      showToast("Copy is not available right now.");
    }
  };

  const handleShareMessage = async (text) => {
    if (!text) return;

    if (navigator.share) {
      try {
        await navigator.share({
          title: "AuraChat message",
          text,
        });
      } catch (error) {
        console.error("Share cancelled or unavailable", error);
      }
      return;
    }

    await handleCopyMessage(text);
    showToast("Sharing is unavailable here, so the message was copied.", "success");
  };

  const handleKeyDown = (e) => {

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion);
  };

  const handleSupportToolPrompt = (prompt) => {
    setInputValue(prompt);
  };

  const handleBreathingToggle = () => {
    setBreathingActive((current) => !current);
    setActiveSupportTool("breathing");
  };

  const suggestions = [
    "I'm feeling anxious",
    "I need to vent",
    "Help me reflect",
  ];

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <main className="flex-1 flex flex-col" style={{ background: "#F7FAFD" }}>
        <header
          className="px-8 py-4 bg-white flex items-center justify-between"
          style={{
            boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
            height: "64px",
          }}
        >
          <h2 className="text-xl" style={{ color: "var(--aura-text-primary)" }}>
            {messages.length > 0 ? "New Conversation" : "AuraChat"}
          </h2>

          <div className="flex items-center gap-4">
            <NotificationBell />
            <div
              className="flex items-center gap-2 px-3 py-1.5"
              style={{
                background: "rgba(126, 200, 164, 0.1)",
                borderRadius: "20px",
                color: "#7EC8A4",
              }}
            >
              <div
                className="w-2 h-2 rounded-full"
                style={{ background: "#7EC8A4" }}
              ></div>
              <span className="text-sm">AI is ready</span>
            </div>
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs cursor-pointer"
              style={{ background: "#4A90D9", color: "white" }}
            >
              {userName.charAt(0).toUpperCase()}
            </div>
          </div>
        </header>

      {showCrisisBanner && (
        <CrisisBanner onDismiss={() => setShowCrisisBanner(false)} />
      )}
      {showCrisisPanel && (
        <CrisisSupportPanel
          resources={crisisResources}
          onDismiss={() => setShowCrisisPanel(false)}
          onGrounding={() => {
            setShowCrisisPanel(false);
            handleSupportToolPrompt("Guide me through a short grounding exercise right now.");
          }}
        />
      )}

        <div className="flex-1 overflow-y-auto px-8 py-6">
          <div className="max-w-5xl mx-auto mb-5">
            <SupportToolPanel
              activeTool={activeSupportTool}
              setActiveTool={setActiveSupportTool}
              breathingActive={breathingActive}
              onBreathingToggle={handleBreathingToggle}
              onPrompt={handleSupportToolPrompt}
            />
          </div>
          {messages.length === 0 ? (
            <EmptyState
              onSuggestionClick={handleSuggestionClick}
              suggestions={suggestions}
            />
          ) : (
            <div className="space-y-6 max-w-4xl mx-auto">
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isLatestAiMessage={
                    message.sender === "ai" &&
                    messages
                      .filter((item) => item.sender === "ai")
                      .at(-1)?.id === message.id
                  }
                  onRetryOrRegenerate={handleRetryOrRegenerate}
                  isThinking={isThinking}
                  onCopyMessage={handleCopyMessage}
                  onShareMessage={handleShareMessage}
                />
              ))}
              {isThinking && <ThinkingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div
          className="px-8 py-6 bg-white"
          style={{ boxShadow: "0 -2px 8px rgba(0, 0, 0, 0.04)" }}
        >
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Talk to Aura..."
                  className="w-full px-5 py-4 pr-24 resize-none focus:outline-none focus:ring-2 transition-all"
                  style={{
                    borderRadius: "16px",
                    border: "1px solid #D0DCE8",
                    minHeight: "56px",
                    maxHeight: "120px",
                    color: "var(--aura-text-primary)",
                  }}
                  rows={1}
                />
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs" style={{ color: "var(--aura-text-secondary)" }}>
                  <span>Private reflection space</span>
                  <span aria-hidden="true">.</span>
                  <button
                    type="button"
                    onClick={() => handleSupportToolPrompt("Can you guide me through a quick grounding exercise?")}
                    className="hover:underline"
                    style={{ color: "#2C5F8A" }}
                  >
                    Ask for grounding
                  </button>
                </div>
              </div>

              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isThinking}
                className="text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 flex items-center justify-center shrink-0"
                style={{
                  background: "#4A90D9",
                  borderRadius: "50%",
                  width: "56px",
                  height: "56px",
                  boxShadow: "0 4px 12px rgba(74, 144, 217, 0.3)",
                }}
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function SupportToolPanel({
  activeTool,
  setActiveTool,
  breathingActive,
  onBreathingToggle,
  onPrompt,
}) {
  const tools = [
    {
      id: "grounding",
      label: "Ground",
      icon: ShieldCheck,
      color: "#2C5F8A",
      title: "5-4-3-2-1 reset",
      body: "Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, and 1 steady breath.",
      prompt: "Guide me through the 5-4-3-2-1 grounding exercise.",
    },
    {
      id: "breathing",
      label: "Breathe",
      icon: Wind,
      color: "#7EC8A4",
      title: breathingActive ? "Follow the slow rhythm" : "Box breathing",
      body: breathingActive
        ? "Inhale for 4, hold for 4, exhale for 4, hold for 4. Repeat gently."
        : "Use a simple four-count pattern when your body feels activated.",
      prompt: "Walk me through a short box breathing exercise.",
    },
    {
      id: "plan",
      label: "Plan",
      icon: TimerReset,
      color: "#F5A962",
      title: "One small next step",
      body: "Choose one safe, doable action for the next 10 minutes.",
      prompt: "Help me choose one small next step for the next 10 minutes.",
    },
  ];
  const selected = tools.find((tool) => tool.id === activeTool) || tools[0];
  const SelectedIcon = selected.icon;

  return (
    <section
      className="bg-white px-4 py-3"
      style={{
        border: "1px solid #E4ECF4",
        borderRadius: "16px",
        boxShadow: "0 4px 18px rgba(44, 95, 138, 0.06)",
      }}
      aria-label="Quick support tools"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-3 min-w-0">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: `${selected.color}18`, color: selected.color }}
          >
            <SelectedIcon size={20} />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-semibold" style={{ color: "var(--aura-text-primary)" }}>
                {selected.title}
              </h3>
              {breathingActive && selected.id === "breathing" && (
                <span
                  className="inline-flex h-2.5 w-2.5 rounded-full"
                  style={{ background: "#7EC8A4", boxShadow: "0 0 0 6px rgba(126, 200, 164, 0.16)" }}
                />
              )}
            </div>
            <p className="text-sm mt-1" style={{ color: "var(--aura-text-secondary)" }}>
              {selected.body}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          {tools.map((tool) => {
            const Icon = tool.icon;
            const active = activeTool === tool.id;
            return (
              <button
                key={tool.id}
                type="button"
                onClick={() => setActiveTool(tool.id)}
                className="w-10 h-10 inline-flex items-center justify-center transition-all"
                style={{
                  borderRadius: "10px",
                  border: active ? `1px solid ${tool.color}` : "1px solid #E4ECF4",
                  background: active ? `${tool.color}12` : "#FFFFFF",
                  color: active ? tool.color : "#66768F",
                }}
                title={tool.label}
                aria-label={tool.label}
              >
                <Icon size={18} />
              </button>
            );
          })}
          <button
            type="button"
            onClick={
              selected.id === "breathing"
                ? onBreathingToggle
                : () => onPrompt(selected.prompt)
            }
            className="inline-flex items-center gap-2 px-4 py-2 text-sm text-white transition-all hover:opacity-90"
            style={{ background: selected.color, borderRadius: "10px" }}
          >
            {selected.id === "breathing" ? <HeartPulse size={16} /> : <MessageCircle size={16} />}
            <span>{selected.id === "breathing" ? (breathingActive ? "Pause" : "Start") : "Use"}</span>
          </button>
        </div>
      </div>
    </section>
  );
}

function CrisisSupportPanel({ resources, onDismiss, onGrounding }) {
  const primaryResource = resources?.[0];
  const textResource = resources?.find((resource) => resource.number === "741741");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="w-full max-w-xl bg-white overflow-hidden"
        style={{ borderRadius: "18px", boxShadow: "0 24px 70px rgba(0, 0, 0, 0.28)" }}
      >
        <div className="p-6" style={{ background: "#FFF5F3", borderBottom: "1px solid #F1D1CC" }}>
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ background: "rgba(224, 124, 107, 0.14)", color: "#C15A4B" }}>
                <ShieldCheck size={22} />
              </div>
              <div>
                <h2 className="text-2xl" style={{ color: "#7A3A2E" }}>Immediate Support</h2>
                <p className="mt-1 text-sm" style={{ color: "#7A3A2E" }}>
                  If you might hurt yourself or someone else, contact emergency support now.
                </p>
              </div>
            </div>
            <button onClick={onDismiss} className="p-2 rounded-full hover:bg-white/70" aria-label="Close support panel">
              <X size={18} style={{ color: "#7A3A2E" }} />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <a
            href={`tel:${primaryResource?.number || "988"}`}
            className="flex items-center gap-3 p-4 text-white"
            style={{ background: "#E07C6B", borderRadius: "14px" }}
          >
            <Phone size={20} />
            <div>
              <div className="font-medium">Call or Text {primaryResource?.number || "988"}</div>
              <div className="text-sm opacity-90">{primaryResource?.hotline || "988 Suicide & Crisis Lifeline"}</div>
            </div>
          </a>

          <a
            href={`sms:${textResource?.number || "741741"}`}
            className="flex items-center gap-3 p-4"
            style={{ border: "1px solid #D0DCE8", borderRadius: "14px", color: "#2C5F8A" }}
          >
            <MessageCircle size={20} />
            <div>
              <div className="font-medium">Text Support</div>
              <div className="text-sm" style={{ color: "var(--aura-text-secondary)" }}>
                {textResource?.text || "Text HOME to 741741"}
              </div>
            </div>
          </a>

          <button
            type="button"
            onClick={onGrounding}
            className="w-full flex items-center gap-3 p-4 text-left"
            style={{ border: "1px solid #D0DCE8", borderRadius: "14px", color: "#2C5F8A" }}
          >
            <Wind size={20} />
            <div>
              <div className="font-medium">Start Grounding</div>
              <div className="text-sm" style={{ color: "var(--aura-text-secondary)" }}>
                Get a short stabilizing prompt in chat.
              </div>
            </div>
          </button>

          <p className="text-xs leading-relaxed" style={{ color: "var(--aura-text-secondary)" }}>
            AuraChat can stay with you for reflection, but urgent safety needs deserve immediate human support.
          </p>
        </div>
      </motion.div>
    </div>
  );
}

function EmptyState({ onSuggestionClick, suggestions }) {
  return (
    <div className="flex flex-col items-center justify-center h-full max-w-2xl mx-auto text-center">
      <div className="mb-8">
        <div className="relative w-32 h-32 mx-auto">
          <div
            className="absolute inset-0 rounded-full opacity-20"
            style={{ background: "#4A90D9" }}
          />
          <div
            className="absolute inset-4 rounded-full opacity-40"
            style={{ background: "#7EC8A4" }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <MessageCircle size={48} style={{ color: "#4A90D9" }} />
          </div>
        </div>
      </div>

      <h3
        className="text-2xl mb-3"
        style={{ color: "var(--aura-text-primary)" }}
      >
        Start a conversation
      </h3>
      <p className="mb-8" style={{ color: "var(--aura-text-secondary)" }}>
        Aura is listening.
      </p>

      <div className="flex flex-wrap gap-3 justify-center">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onSuggestionClick(suggestion)}
            className="px-6 py-3 hover:opacity-80 transition-all"
            style={{
              background: "white",
              borderRadius: "24px",
              color: "var(--aura-text-primary)",
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.06)",
            }}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({
  message,
  isLatestAiMessage,
  onRetryOrRegenerate,
  isThinking,
  onCopyMessage,
  onShareMessage,
}) {
  const isUser = message.sender === "user";
  const omitMarkdownNode = (props) => {
    const cleanProps = { ...props };
    delete cleanProps.node;
    return cleanProps;
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} gap-3`}>
      {!isUser && (
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white text-sm"
          style={{ background: "#7EC8A4" }}
        >
          A
        </div>
      )}

      <motion.div
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="max-w-[70%]"
      >
        <div
          className="px-6 py-4"
          style={{
            background: isUser ? "#4A90D9" : "#ffffff",
            color: isUser ? "#ffffff" : "#1A1A2E",
            borderRadius: "24px",
            boxShadow: isUser
              ? "0 4px 12px rgba(74, 144, 217, 0.2)"
              : "0 2px 8px rgba(0, 0, 0, 0.06)",
          }}
        >
          {isUser ? (
            <p className="leading-relaxed whitespace-pre-wrap flex flex-col">{message.text}</p>
          ) : (
            <div className="leading-relaxed flex flex-col gap-2">
              <ReactMarkdown
                components={{
                  p: (props) => <p className="mb-2 last:mb-0" {...omitMarkdownNode(props)} />,
                  ul: (props) => <ul className="list-disc ml-5 mb-2" {...omitMarkdownNode(props)} />,
                  ol: (props) => <ol className="list-decimal ml-5 mb-2" {...omitMarkdownNode(props)} />,
                  li: (props) => <li className="mb-1" {...omitMarkdownNode(props)} />,
                  h1: (props) => <h1 className="text-xl font-bold mb-2" {...omitMarkdownNode(props)} />,
                  h2: (props) => <h2 className="text-lg font-bold mb-2" {...omitMarkdownNode(props)} />,
                  h3: (props) => <h3 className="text-md font-bold mb-2" {...omitMarkdownNode(props)} />,
                  strong: (props) => <strong className="font-bold" {...omitMarkdownNode(props)} />
                }}
              >
                {message.text}
              </ReactMarkdown>
            </div>
          )}
        </div>
        <div
          className={`text-xs mt-2 ${isUser ? "text-right" : "text-left"}`}
          style={{ color: "var(--aura-text-secondary)" }}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
        {!isUser && message.promptText && (
          <div className="mt-2 flex flex-wrap gap-2">
            <button
              onClick={() =>
                onRetryOrRegenerate(message.promptText, message.id)
              }
              disabled={isThinking}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-full transition-all disabled:opacity-50"
              style={{
                background: "rgba(74, 144, 217, 0.08)",
                color: "#4A90D9",
              }}
            >
              <RefreshCw size={12} />
              <span>{message.isError ? "Retry" : isLatestAiMessage ? "Regenerate" : "Retry Prompt"}</span>
            </button>
            <button
              onClick={() => onCopyMessage(message.text)}
              disabled={isThinking || !message.text}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-full transition-all disabled:opacity-50"
              style={{
                background: "rgba(126, 200, 164, 0.1)",
                color: "#2C5F8A",
              }}
            >
              <Copy size={12} />
              <span>Copy</span>
            </button>
            <button
              onClick={() => onShareMessage(message.text)}
              disabled={isThinking || !message.text}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-xs rounded-full transition-all disabled:opacity-50"
              style={{
                background: "rgba(245, 169, 98, 0.12)",
                color: "#8A5A2B",
              }}
            >
              <Share2 size={12} />
              <span>Share</span>
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}

function ThinkingIndicator() {
  return (
    <div className="flex justify-start gap-3">
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white text-sm"
        style={{ background: "#7EC8A4" }}
      >
        A
      </div>

      <div
        className="px-6 py-4 flex items-center gap-2"
        style={{
          background: "#ffffff",
          borderRadius: "24px",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.06)",
        }}
      >
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 rounded-full"
            style={{ background: "#4A90D9" }}
            animate={{ y: [0, -8, 0], opacity: [0.5, 1, 0.5] }}
            transition={{
              duration: 1,
              repeat: Infinity,
              delay: i * 0.2,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </div>
  );
}
