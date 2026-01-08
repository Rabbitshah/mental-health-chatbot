import { useState, useEffect, useRef } from "react";
import API from "../api";
import { useNavigate } from "react-router-dom";

export default function Chatbot() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [userName, setUserName] = useState("User");
  const [isTyping, setIsTyping] = useState(false);
  const navigate = useNavigate();
  const chatEndRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) navigate("/login");

    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const userObj = JSON.parse(userStr);
        if (userObj.name) setUserName(userObj.name);
      } catch {}
    }
  }, [navigate]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const formatTime = (date = new Date()) => {
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const sendMessage = async (messageText = null) => {
    const userMsg = messageText || input.trim();
    if (!userMsg) return;

    const timestamp = formatTime();
    setMessages((prev) => [
      ...prev,
      { type: "user", text: userMsg, timestamp },
    ]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await API.post("/chat", { message: userMsg });
      const botReply = res.data.response || res.data.reply;
      const botTimestamp = formatTime();
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: botReply, timestamp: botTimestamp },
      ]);
    } catch (err) {
      console.error("Chat error:", err);
      setIsTyping(false);
      const errorTimestamp = formatTime();
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: "Something went wrong!", timestamp: errorTimestamp },
      ]);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
  };

  const handleSuggestion = (suggestion) => {
    sendMessage(suggestion);
  };

  const getTodayDate = () => {
    const today = new Date();
    return today.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="min-h-screen bg-gray-900 flex font-sans text-gray-200">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col min-h-screen">
        {/* MindfulBot Branding */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-blue-400 border-2 border-white flex items-center justify-center">
              <span className="text-white font-bold text-lg">M</span>
            </div>
            <div>
              <span className="font-bold text-xl text-white">MindfulBot</span>
              <p className="text-sm text-gray-400">Always here to listen</p>
            </div>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={handleNewChat}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-3 font-medium transition flex items-center justify-center gap-2"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            New Chat
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-4">
          {/* RECENTS Section */}
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-gray-400 uppercase mb-3 tracking-wider">
              RECENTS
            </h3>
            <div className="space-y-2">
              <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center gap-2 text-gray-300">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span className="text-sm">Anxiety about work</span>
              </button>
              <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center gap-2 text-gray-300">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span className="text-sm">Sleep issues</span>
              </button>
            </div>
          </div>

          {/* TOOLS Section */}
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-gray-400 uppercase mb-3 tracking-wider">
              TOOLS
            </h3>
            <div className="space-y-2">
              <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center gap-2 text-gray-300">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                  />
                </svg>
                <span className="text-sm">Journal</span>
              </button>
              <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center gap-2 text-gray-300">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
                <span className="text-sm">Breathing Exercises</span>
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="p-4 border-t border-gray-700 space-y-2">
          <button
            onClick={() => navigate("/profile")}
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center gap-2 text-gray-300"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <span className="text-sm">Settings</span>
          </button>
          <button className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center gap-2 text-red-400">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <span className="text-sm">Crisis Support</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-h-screen">
        {/* Top Header */}
        <header className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Daily Check-in</h2>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-400">Online & Listening</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition">
              Emergency Help
            </button>
            <button className="text-gray-400 hover:text-gray-300">
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                />
              </svg>
            </button>
          </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="max-w-4xl mx-auto">
            {/* Date Header */}
            {messages.length > 0 && (
              <div className="text-center text-gray-500 text-sm mb-6">
                Today, {formatTime()}
              </div>
            )}

            {/* Messages */}
            <div className="space-y-6">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-12">
                  <div className="w-16 h-16 rounded-full bg-blue-400 border-2 border-white flex items-center justify-center mx-auto mb-4">
                    <span className="text-white font-bold text-2xl">M</span>
                  </div>
                  <p className="text-lg text-gray-300 mb-2">Hello, I'm here to listen without judgment.</p>
                  <p className="text-gray-400">How are you feeling right now?</p>
                </div>
              ) : (
                <>
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 ${
                        msg.type === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      {msg.type === "bot" && (
                        <div className="w-10 h-10 rounded-full bg-blue-400 border-2 border-white flex items-center justify-center flex-shrink-0">
                          <span className="text-white font-bold">M</span>
                        </div>
                      )}
                      <div className={`flex flex-col ${msg.type === "user" ? "items-end" : "items-start"} max-w-[70%]`}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-medium text-gray-400">
                            {msg.type === "bot" ? "MindfulBot" : "You"}
                          </span>
                          <span className="text-xs text-gray-500">{msg.timestamp}</span>
                        </div>
                        <div
                          className={`px-4 py-3 rounded-2xl ${
                            msg.type === "user"
                              ? "bg-blue-600 text-white"
                              : "bg-gray-700 text-gray-200"
                          }`}
                        >
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                        </div>
                        {/* Suggested Actions for Bot Messages */}
                        {msg.type === "bot" && idx === messages.length - 1 && !isTyping && (
                          <div className="flex flex-wrap gap-2 mt-3">
                            <button
                              onClick={() => handleSuggestion("Explore strategies")}
                              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-lg text-sm transition"
                            >
                              Explore strategies
                            </button>
                            <button
                              onClick={() => handleSuggestion("Keep venting")}
                              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-lg text-sm transition"
                            >
                              Keep venting
                            </button>
                            <button
                              onClick={() => handleSuggestion("Try a breathing exercise")}
                              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-lg text-sm transition"
                            >
                              Try a breathing exercise
                            </button>
                          </div>
                        )}
                      </div>
                      {msg.type === "user" && (
                        <div className="w-10 h-10 rounded-full bg-orange-400 border-2 border-white flex items-center justify-center flex-shrink-0">
                          <span className="text-white font-bold text-sm">
                            {userName.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                  {/* Typing Indicator */}
                  {isTyping && (
                    <div className="flex gap-3 justify-start">
                      <div className="w-10 h-10 rounded-full bg-blue-400 border-2 border-white flex items-center justify-center flex-shrink-0">
                        <span className="text-white font-bold">M</span>
                      </div>
                      <div className="flex flex-col items-start">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-medium text-gray-400">MindfulBot</span>
                          <span className="text-xs text-gray-500">{formatTime()}</span>
                        </div>
                        <div className="px-4 py-3 rounded-2xl bg-gray-700">
                          <div className="flex items-center gap-1.5">
                            <span className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></span>
                            <span className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></span>
                            <span className="w-2 h-2 bg-gray-400 rounded-full typing-dot"></span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
              <div ref={chatEndRef} />
            </div>
          </div>
        </div>

        {/* Input Bar */}
        <div className="border-t border-gray-700 px-6 py-4 bg-gray-800">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-3 bg-gray-700 rounded-lg px-4 py-3">
              <button className="text-gray-400 hover:text-gray-300 transition">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
              </button>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="flex-1 border-none outline-none bg-transparent text-gray-200 placeholder-gray-400"
                placeholder="Type your thoughts here..."
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
              />
              <button className="text-gray-400 hover:text-gray-300 transition">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                  />
                </svg>
              </button>
              <button
                onClick={() => sendMessage()}
                className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg p-2 transition"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            </div>
            <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
              <span>Your conversation is private and secure.</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
