import React from "react";
import { GoogleLogin } from "@react-oauth/google";
import API from "../api";

const GoogleLoginButton = () => {
  const handleSuccess = async (credentialResponse) => {
    try {
      const res = await API.post("/google-login", {
        credential: credentialResponse.credential,
      });
  
      localStorage.setItem("token", res.data.access_token || res.data.token);
      if (res.data.refresh_token) {
        localStorage.setItem("refresh_token", res.data.refresh_token);
      }
      localStorage.setItem("user", JSON.stringify(res.data.user));
      window.location.href = "/dashboard";
    } catch (err) {
      console.error("Google Login Error:", err);
    }
  };
  
  return (
    <div className="w-full flex justify-center">
      <GoogleLogin 
        onSuccess={handleSuccess} 
        onError={() => console.error("Google login failed")}
        width="340"
      />
    </div>
  );
};

export default GoogleLoginButton;