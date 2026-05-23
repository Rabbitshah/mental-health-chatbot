import axios from "axios";
import { showToast } from "./components/Toast";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  withCredentials: true, // Req 14.4, 14.5 – use credentials: "include" for HttpOnly cookies
});

let refreshRequest = null;

function clearAuthState() {
  localStorage.removeItem("user");
  localStorage.removeItem("isLoggedIn");
}

API.interceptors.request.use((req) => {
  // No longer manual Authorization header injection – handled by cookies
  return req;
});

API.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;

    if (
      status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/login") &&
      !originalRequest.url?.includes("/signup") &&
      !originalRequest.url?.includes("/auth/refresh")
    ) {
      originalRequest._retry = true;
      try {
        refreshRequest =
          refreshRequest ||
          API.post("/auth/refresh", {}, {
            _skipAuthRefresh: true,
          }).finally(() => {
            refreshRequest = null;
          });

        await refreshRequest;
        // The server will have set a new access_token cookie
        return API(originalRequest);
      } catch (refreshError) {
        clearAuthState();
        showToast("Your session expired. Please sign in again.");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

export const updateProfile = (data) => API.put("/profile", data);

export default API;
