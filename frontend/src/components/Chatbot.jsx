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
  }, []);

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
    <div className="min-h-screen bg-[#18181b] flex font-sans text-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-[#232946] border-r border-[#393e46] flex flex-col p-6 min-h-screen">
        <div className="flex items-center mb-8">
          <span className="font-extrabold text-xl tracking-widest">
            AuraChat
          </span>
        </div>
        <button className="bg-[#6a8dff] text-white rounded-full px-4 py-2 mb-6 font-medium hover:shadow-md transition">
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
            <span className="text-sm font-semibold">{userName}</span>
            <svg
              className="w-5 h-5 ml-1"
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
              <div className="absolute right-0 bottom-full mb-2 w-40 bg-[#232946] border border-[#393e46] rounded-lg shadow-md z-50">
                <button
                  className="w-full text-left px-4 py-2 hover:bg-[#393e46] text-sm"
                  onClick={() => {
                    setMenuOpen(false);
                    navigate("/profile");
                  }}
                >
                  Settings
                </button>
                <button
                  className="w-full text-left px-4 py-2 hover:bg-[#393e46] text-sm text-red-400"
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
            <span className="bg-[#232946] px-6 py-2 rounded-full border border-[#393e46] text-lg font-semibold tracking-widest mb-2">
              AuraChat
            </span>
            <h1 className="text-3xl font-bold mb-1 text-center">
              Good day! How may I assist you today?
            </h1>
          </div>

          {/* Chat Box */}
          <div className="bg-[#232946] rounded-xl shadow p-6 mb-6 max-h-[420px] overflow-y-auto space-y-4 border border-[#393e46]">
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
                        ? "bg-[#6a8dff] text-gray-100 text-right"
                        : "bg-[#393e46] border border-[#232946] text-left"
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
          <div className="flex items-center bg-[#232946] rounded-full shadow px-4 py-2 border border-[#393e46]">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 border-none outline-none bg-transparent px-2 py-2 text-base text-gray-100 placeholder-gray-400"
              placeholder="What's on your mind?..."
              onKeyDown={(e) => {
                if (e.key === "Enter") sendMessage();
              }}
            />
            <button
              onClick={sendMessage}
              className="ml-2 bg-[#6a8dff] hover:bg-[#4e6edb] text-white rounded-full p-2 transition"
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
