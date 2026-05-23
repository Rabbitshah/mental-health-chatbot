import ReactDOM from "react-dom/client";
import App from "./App";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { ToastProvider } from "./components/Toast";
import "./index.css";

const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

if (!clientId) {
  console.error(
    "[AuraChat] VITE_GOOGLE_CLIENT_ID is not set. " +
    "Add it to frontend/.env and restart the dev server."
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <GoogleOAuthProvider clientId={clientId ?? ""}>
    <ToastProvider>
      <App />
    </ToastProvider>
  </GoogleOAuthProvider>
);
