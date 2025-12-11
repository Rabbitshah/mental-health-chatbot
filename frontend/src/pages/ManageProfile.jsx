import { useState, useEffect } from "react";
import { updateProfile } from "../api";
import { useNavigate } from "react-router-dom";

export default function ManageProfile() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        setName(user.name || "");
        setEmail(user.email || "");
        setUsername(user.username || "");
      } catch {}
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    try {
      const res = await updateProfile({
        name,
        email,
        password: password || undefined,
        current_password: currentPassword,
      });
      setMsg("Profile updated!");
      localStorage.setItem("user", JSON.stringify(res.data.user));
      setPassword("");
      setCurrentPassword("");
    } catch (err) {
      setMsg(err.response?.data?.detail || "Update failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 text-gray-200">
      <form
        className="bg-gray-800 p-8 rounded-2xl shadow-lg w-full max-w-md"
        onSubmit={handleSubmit}
      >
        <h2 className="text-3xl font-bold mb-6 text-center text-white">Manage Profile</h2>
        <div className="mb-4">
          <label className="block mb-2 text-sm font-medium text-gray-300">
            Username
          </label>
          <input
            className="w-full px-4 py-2 border rounded-lg bg-gray-700 text-gray-400 cursor-not-allowed border-gray-600"
            value={username}
            disabled
          />
        </div>
        <div className="mb-4">
          <label className="block mb-2 text-sm font-medium text-gray-300">
            Name
          </label>
          <input
            className="w-full px-4 py-2 border rounded-lg bg-gray-700 text-white border-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="mb-4">
          <label className="block mb-2 text-sm font-medium text-gray-300">
            Email
          </label>
          <input
            className="w-full px-4 py-2 border rounded-lg bg-gray-700 text-white border-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="mb-4">
          <label className="block mb-2 text-sm font-medium text-gray-300">
            New Password
          </label>
          <input
            type="password"
            className="w-full px-4 py-2 border rounded-lg bg-gray-700 text-white border-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Leave blank to keep current password"
          />
        </div>
        <div className="mb-6">
          <label className="block mb-2 text-sm font-medium text-gray-300">
            Current Password*
          </label>
          <input
            type="password"
            className="w-full px-4 py-2 border rounded-lg bg-gray-700 text-white border-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
        </div>
        <button
          type="submit"
          className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold mb-2 disabled:opacity-50 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          disabled={loading}
        >
          {loading ? "Saving..." : "Save Changes"}
        </button>
        {msg && (
          <div className={`text-center text-sm mt-2 ${msg.includes("updated") ? "text-green-400" : "text-red-400"}`}>
            {msg}
          </div>
        )}
        <button
          type="button"
          className="w-full mt-4 text-indigo-500 hover:underline text-sm"
          onClick={() => navigate("/chat")}
        >
          Back to Chat
        </button>
      </form>
    </div>
  );
}
