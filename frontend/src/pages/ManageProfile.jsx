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
    <div className="min-h-screen flex items-center justify-center bg-[#f7f7fa]">
      <form
        className="bg-white p-8 rounded-lg shadow-md w-full max-w-md"
        onSubmit={handleSubmit}
      >
        <h2 className="text-2xl font-bold mb-6 text-center">Manage Profile</h2>
        <label className="block mb-2 text-sm font-medium text-gray-700">
          Username
        </label>
        <input
          className="w-full mb-4 p-2 border rounded bg-gray-100 cursor-not-allowed"
          value={username}
          disabled
        />
        <label className="block mb-2 text-sm font-medium text-gray-700">
          Name
        </label>
        <input
          className="w-full mb-4 p-2 border rounded"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <label className="block mb-2 text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          className="w-full mb-4 p-2 border rounded"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <label className="block mb-2 text-sm font-medium text-gray-700">
          New Password
        </label>
        <input
          type="password"
          className="w-full mb-4 p-2 border rounded"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Leave blank to keep current password"
        />
        <label className="block mb-2 text-sm font-medium text-gray-700">
          Current Password*
        </label>
        <input
          type="password"
          className="w-full mb-4 p-2 border rounded"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
        />
        <button
          type="submit"
          className="w-full bg-[#6a8dff] text-white py-2 rounded font-semibold mb-2 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Saving..." : "Save Changes"}
        </button>
        {msg && (
          <div className="text-center text-sm mt-2 text-red-500">{msg}</div>
        )}
        <button
          type="button"
          className="w-full mt-4 text-blue-600 hover:underline text-sm"
          onClick={() => navigate("/chat")}
        >
          Back to Chat
        </button>
      </form>
    </div>
  );
}
