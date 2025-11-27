import { useState } from "react";
import API from "../api";
import { useNavigate, Link } from "react-router-dom";
import GoogleLoginButton from "../components/GoogleLoginButton";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const navigate = useNavigate();

  const handleSignup = async () => {
    try {
      await API.post("/signup", { email, password, name, username });
      // Automatically log in the user after signup
      const res = await API.post("/login", { email, password });
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("user", JSON.stringify(res.data.user));
      navigate("/chat");
    } catch (err) {
      alert(err.response?.data?.detail || "Signup failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-tr from-[#232946] via-[#393e46] to-[#18181b]">
      <div className="flex w-full max-w-5xl bg-[#232946]/80 rounded-lg shadow-lg overflow-hidden">
        {/* Left: Branding and Info */}
        <div className="hidden md:flex flex-col w-1/2 p-10 text-white bg-gradient-to-br from-[#18181b] via-[#232946] to-[#393e46]">
          <h1 className="text-3xl font-bold mb-6 tracking-wide">AuraChat</h1>
        </div>
        {/* Right: Signup Form */}
        <div className="w-full md:w-1/2 bg-[#232946] p-10 flex flex-col justify-center">
          <h2 className="text-2xl font-bold mb-2 text-gray-100">Sign up</h2>
          <p className="mb-6 text-gray-300 text-sm">
            Create your account to get started
          </p>
          <label className="block mb-2 text-sm font-medium text-gray-200">
            Name*
          </label>
          <input
            className="w-full mb-4 p-2 border rounded bg-[#232946] text-white focus:outline-none focus:ring-2 focus:ring-[#e4acfc]"
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <label className="block mb-2 text-sm font-medium text-gray-200">
            Username*
          </label>
          <input
            className="w-full mb-4 p-2 border rounded bg-[#232946] text-white focus:outline-none focus:ring-2 focus:ring-[#e4acfc]"
            placeholder="Choose a username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <label className="block mb-2 text-sm font-medium text-gray-200">
            Email Address*
          </label>
          <input
            className="w-full mb-4 p-2 border rounded bg-[#232946] text-white focus:outline-none focus:ring-2 focus:ring-[#e4acfc]"
            placeholder="ex. email@domain.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <label className="block mb-2 text-sm font-medium text-gray-200">
            Password*
          </label>
          <input
            type="password"
            className="w-full mb-6 p-2 border rounded bg-[#232946] text-white focus:outline-none focus:ring-2 focus:ring-[#e4acfc]"
            placeholder="Enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            className="w-full bg-gradient-to-r from-[#6a8dff] to-[#a259ff] hover:from-[#5a7be0] hover:to-[#8e47d6] text-white py-2 rounded mb-4 font-semibold transition-all duration-200 cursor-pointer transform hover:scale-105 hover:shadow-lg"
            onClick={handleSignup}
          >
            Sign up
          </button>
          <div className="flex items-center my-4">
            <div className="flex-grow h-px bg-gray-300" />
            <span className="mx-2 text-gray-400 text-xs">or</span>
            <div className="flex-grow h-px bg-gray-300" />
          </div>
          <div className="mb-4">
            <GoogleLoginButton />
          </div>
          <div className="text-center text-xs text-gray-500 mb-2">
            Already have an account?{" "}
            <Link to="/login" className="text-[#e4acfc] hover:underline">
              Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
