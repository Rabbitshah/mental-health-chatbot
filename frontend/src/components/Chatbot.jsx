import { useState, useRef, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  MessageCircle,
  Send,
  Paperclip,
  Smile,
  Bell,
  HelpCircle,
} from "lucide-react";
import { motion } from "motion/react";
import ReactMarkdown from "react-markdown";
import API from "../api";
import Sidebar from "./Sidebar";

export default function Chatbot() {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [userName, setUserName] = useState("Jane Doe");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
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
  }, [navigate, sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

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
    setIsThinking(true);

    try {
      const payload = { message: prompt };
      if (sessionId) {
        payload.session_id = parseInt(sessionId, 10);
      }
      
      const res = await API.post("/chat", payload);
      
      if (!sessionId && res.data.session_id) {
        // Replace URL dynamically so subsequent messages use this session without reloading
        navigate(`/chat/${res.data.session_id}`, { replace: true });
      }

      const aiMessage = {
        id: (Date.now() + 1).toString(),
        text:
          res.data?.response ||
          res.data?.reply ||
          "I hear you. I am here to listen and support you.",
        sender: "ai",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
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
      };
      setMessages((prev) => [...prev, aiMessage]);
    } finally {
      setIsThinking(false);
    }
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
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-all">
              <Bell size={20} style={{ color: "var(--aura-text-secondary)" }} />
            </button>
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-all">
              <HelpCircle
                size={20}
                style={{ color: "var(--aura-text-secondary)" }}
              />
            </button>
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs cursor-pointer"
              style={{ background: "#4A90D9", color: "white" }}
            >
              {userName.charAt(0).toUpperCase()}
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-8 py-6">
          {messages.length === 0 ? (
            <EmptyState
              onSuggestionClick={handleSuggestionClick}
              suggestions={suggestions}
            />
          ) : (
            <div className="space-y-6 max-w-4xl mx-auto">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
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
              <div className="flex-1 relative">
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

                <div className="absolute right-3 bottom-3 flex gap-2">
                  <button className="p-2 hover:bg-gray-100 rounded-lg transition-all">
                    <Paperclip
                      size={18}
                      style={{ color: "var(--aura-text-secondary)" }}
                    />
                  </button>
                  <button className="p-2 hover:bg-gray-100 rounded-lg transition-all">
                    <Smile
                      size={18}
                      style={{ color: "var(--aura-text-secondary)" }}
                    />
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

function MessageBubble({ message }) {
  const isUser = message.sender === "user";

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
            <ReactMarkdown 
              className="leading-relaxed flex flex-col gap-2"
              components={{
                p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                ul: ({node, ...props}) => <ul className="list-disc ml-5 mb-2" {...props} />,
                ol: ({node, ...props}) => <ol className="list-decimal ml-5 mb-2" {...props} />,
                li: ({node, ...props}) => <li className="mb-1" {...props} />,
                h1: ({node, ...props}) => <h1 className="text-xl font-bold mb-2" {...props} />,
                h2: ({node, ...props}) => <h2 className="text-lg font-bold mb-2" {...props} />,
                h3: ({node, ...props}) => <h3 className="text-md font-bold mb-2" {...props} />,
                strong: ({node, ...props}) => <strong className="font-bold" {...props} />
              }}
            >
              {message.text}
            </ReactMarkdown>
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
