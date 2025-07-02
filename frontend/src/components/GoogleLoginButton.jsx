import React from "react";
import { GoogleLogin } from "@react-oauth/google";
import axios from "axios";

const GoogleLoginButton = () => {
  const handleSuccess = async (credentialResponse) => {
    try {
      const res = await axios.post("http://localhost:8000/google-login", {
        token: credentialResponse.credential,
      });

      localStorage.setItem("token", res.data.token);
      localStorage.setItem("user", JSON.stringify(res.data.user));
      window.location.href = "/chat";
    } catch (err) {
      console.error("Google Login Error:", err);
    }
  };

  return (
    <div>
      <GoogleLogin onSuccess={handleSuccess} onError={() => console.error("Google login failed")} />
    </div>
  );
};

export default GoogleLoginButton;
