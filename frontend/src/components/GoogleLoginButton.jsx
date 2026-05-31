import React from "react";
import { GoogleLogin } from "@react-oauth/google";
import { useNavigate } from "react-router-dom";
import API from "../api";
import { useAuth } from "../contexts/AuthContext";

const GoogleLoginButton = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSuccess = async (credentialResponse) => {
    try {
      const res = await API.post("/google-login", {
        credential: credentialResponse.credential,
      });
      // Tokens arrive as HttpOnly cookies — never stored in JS.
      login(res.data.user);
      navigate("/dashboard");
    } catch (err) {
      console.error("Google Login Error:", err);
      alert("Google login failed. Please try again.");
    }
  };

  return (
    <div className="w-full flex justify-center">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={() => {
          console.error("Google login failed");
          alert("Google login failed. Please try again.");
        }}
        width="340"
      />
    </div>
  );
};

export default GoogleLoginButton;
