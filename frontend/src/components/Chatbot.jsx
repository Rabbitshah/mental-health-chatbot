
import { useState, useEffect, useRef } from "react";
import API from "../api";
import { useNavigate } from "react-router-dom";

export default function Chatbot() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [userName, setUserName] = useState("User");
  const [menuOpen, setMenuOpen] = useState(false);
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
  }, [messages]);

  const sendMessage = async () => {
    const userMsg = input.trim();
    if (!userMsg) return;

    setMessages((prev) => [...prev, { type: "user", text: userMsg }]);
    setInput("");

    try {
      const res = await API.post("/chat", { message: userMsg });
      const botReply = res.data.response || res.data.reply;
      setMessages((prev) => [...prev, { type: "bot", text: botReply }]);
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: "Something went wrong!" },
      ]);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-gray-900 flex font-sans text-gray-200">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col p-6 min-h-screen">
        <div className="flex items-center mb-8">
          <span className="font-extrabold text-2xl tracking-widest text-indigo-500">
            AuraChat
          </span>
        </div>
        <button className="bg-indigo-600 text-white rounded-full px-4 py-2 mb-6 font-medium hover:bg-indigo-700 transition">
          + New chat
        </button>
        <div className="flex-1 overflow-y-auto pr-1">
          <div className="mb-4">
            <span className="text-xs text-gray-400 uppercase">
              Your conversations
            </span>
          </div>
          <div className="mb-4">
            <span className="text-xs text-gray-400 uppercase">Last 7 Days</span>
          </div>
        </div>
        <div className="mt-6 relative">
          <div
            className="flex items-center gap-2 mt-2 cursor-pointer select-none"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span className="inline-block w-8 h-8 bg-gray-700 rounded-full" />
            <span className="text-sm font-semibold text-gray-200">{userName}</span>
            <svg
              className="w-5 h-5 ml-1 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 8h16M4 16h16"
              />
            </svg>
            {menuOpen && (
              <div className="absolute right-0 bottom-full mb-2 w-40 bg-gray-800 border border-gray-700 rounded-lg shadow-md z-50">
                <button
                  className="w-full text-left px-4 py-2 hover:bg-gray-700 text-sm text-gray-200"
                  onClick={() => {
                    setMenuOpen(false);
                    navigate("/profile");
                  }}
                >
                  Settings
                </button>
                <button
                  className="w-full text-left px-4 py-2 hover:bg-gray-700 text-sm text-red-400"
                  onClick={handleLogout}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center px-6 py-10">
        <div className="w-full max-w-4xl">
          <div className="flex flex-col items-center mb-8">
            <span className="bg-gray-800 px-6 py-2 rounded-full border border-gray-700 text-lg font-semibold tracking-widest text-indigo-500 mb-2">
              AuraChat
            </span>
            <h1 className="text-3xl font-bold mb-1 text-center text-white">
              Good day! How may I assist you today?
            </h1>
          </div>

          {/* Chat Box */}
          <div className="bg-gray-800 rounded-xl shadow p-6 mb-6 h-[420px] overflow-y-auto space-y-4 border border-gray-700">
            {messages.length === 0 ? (
              <div className="text-center text-gray-400">
                Start the conversation...
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${
                    msg.type === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm whitespace-pre-wrap ${
                      msg.type === "user"
                        ? "bg-indigo-600 text-white"
                        : "bg-gray-700 text-gray-200"
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div className="flex items-center bg-gray-800 rounded-full shadow px-4 py-2 border border-gray-700">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 border-none outline-none bg-transparent px-2 py-2 text-base text-gray-200 placeholder-gray-400"
              placeholder="What's on your mind?..."
              onKeyDown={(e) => {
                if (e.key === "Enter") sendMessage();
              }}
            />
            <button
              onClick={sendMessage}
              className="ml-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full p-2 transition"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M2.25 12l15.75-7.5-7.5 15.75-2.25-6.75-6.75-2.25z"
                />
              </svg>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
