/**
 * ApiClient – wraps fetch with:
 *  - HttpOnly Cookie authentication (via credentials: "include")
 *  - 401 detection → token refresh → retry (Req 14.5, 15.3)
 *  - Exponential backoff retry for network/5xx errors (Req 14.4)
 *  - Toast notifications on failure / success (Req 14.3)
 *  - Console error logging with context (Req 14.6)
 */

import { showToast } from "./components/Toast";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// ── Retry helpers ────────────────────────────────────────────────────────────

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 500;

function shouldRetry(error, attempt) {
  if (attempt >= MAX_RETRIES) return false;
  // Retry on network errors (no response) or 5xx server errors
  if (!error.status) return true; // network / fetch failure
  return error.status >= 500 && error.status < 600;
}

function exponentialDelay(attempt) {
  const delay = BASE_DELAY_MS * Math.pow(2, attempt);
  const jitter = Math.random() * 200;
  return delay + jitter;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ── Core request ─────────────────────────────────────────────────────────────

export class ApiClient {
  constructor() {
    this._refreshing = null; // deduplicate concurrent refresh calls
  }

  /**
   * Make an authenticated request with retry + token refresh.
   *
   * @param {string} endpoint  – path relative to BASE_URL (e.g. "/chat")
   * @param {RequestInit} options – fetch options
   * @param {{ showSuccessToast?: string, showErrorToast?: boolean, attempt?: number, _refreshed?: boolean }} meta
   * @returns {Promise<Response>}
   */
  async request(endpoint, options = {}, meta = {}) {
    const {
      showSuccessToast = null,
      showErrorToast = true,
      attempt = 0,
      _refreshed = false,
    } = meta;

    const url = endpoint.startsWith("http") ? endpoint : `${BASE_URL}${endpoint}`;

    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    let response;
    try {
      // Req 14.4, 14.5 – use credentials: "include" for HttpOnly cookies
      response = await fetch(url, { 
        ...options, 
        headers,
        credentials: "include" 
      });
    } catch (networkError) {
      // Req 14.6 – log to console
      console.error("[ApiClient] Network error", {
        endpoint,
        attempt,
        error: networkError,
        stack: networkError?.stack,
      });

      if (shouldRetry({ status: null }, attempt)) {
        await sleep(exponentialDelay(attempt));
        return this.request(endpoint, options, { ...meta, attempt: attempt + 1 });
      }

      if (showErrorToast) {
        showToast("Network error – please check your connection.");
      }
      throw networkError;
    }

    // ── 401 handling: try token refresh once ────────────────────────────────
    if (response.status === 401 && !_refreshed) {
      try {
        await this._refreshToken();
        return this.request(endpoint, options, {
          ...meta,
          _refreshed: true,
          attempt: 0,
        });
      } catch (refreshError) {
        // Req 14.5 – redirect to login
        console.error("[ApiClient] Token refresh failed, redirecting to login", {
          endpoint,
          error: refreshError,
          stack: refreshError?.stack,
        });
        
        if (showErrorToast) {
          showToast("Your session has expired. Please log in again.");
        }
        
        // Only redirect if not already on login/signup pages to avoid loops
        if (!window.location.pathname.includes("/login") && !window.location.pathname.includes("/signup")) {
            window.location.href = "/login";
        }
        throw refreshError;
      }
    }

    // ── 5xx retry with exponential backoff ──────────────────────────────────
    if (response.status >= 500 && shouldRetry({ status: response.status }, attempt)) {
      console.warn("[ApiClient] Server error, retrying", {
        endpoint,
        status: response.status,
        attempt,
      });
      await sleep(exponentialDelay(attempt));
      return this.request(endpoint, options, { ...meta, attempt: attempt + 1 });
    }

    // ── Error responses ──────────────────────────────────────────────────────
    if (!response.ok) {
      let errorMessage = `Request failed (${response.status})`;
      try {
        const body = await response.clone().json();
        errorMessage = body?.detail || body?.message || errorMessage;
      } catch {
        // body not JSON – keep default message
      }

      const err = Object.assign(new Error(errorMessage), {
        status: response.status,
        response,
      });

      // Req 14.6 – log to console
      console.error("[ApiClient] Request error", {
        endpoint,
        status: response.status,
        message: errorMessage,
        stack: err.stack,
      });

      if (showErrorToast) {
        showToast(errorMessage);
      }

      throw err;
    }

    // ── Success ──────────────────────────────────────────────────────────────
    if (showSuccessToast) {
      showToast(showSuccessToast, "success");
    }

    return response;
  }

  // ── Token refresh ──────────────────────────────────────────────────────────

  async _refreshToken() {
    // Deduplicate: if a refresh is already in-flight, wait for it
    if (this._refreshing) return this._refreshing;

    this._refreshing = (async () => {
      const response = await fetch(`${BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include" // will send refresh_token cookie
      });

      if (!response.ok) {
        throw new Error(`Refresh failed with status ${response.status}`);
      }
      
      // The server will set the new access_token cookie in the response headers
      return await response.json();
    })();

    try {
      await this._refreshing;
    } finally {
      this._refreshing = null;
    }
  }

  // ── Convenience methods ───────────────────────────────────────────────────

  async get(endpoint, meta = {}) {
    return this.request(endpoint, { method: "GET" }, meta);
  }

  async post(endpoint, body, meta = {}) {
    return this.request(
      endpoint,
      { method: "POST", body: body ? JSON.stringify(body) : undefined },
      meta
    );
  }

  async put(endpoint, body, meta = {}) {
    return this.request(
      endpoint,
      { method: "PUT", body: body ? JSON.stringify(body) : undefined },
      meta
    );
  }

  async delete(endpoint, meta = {}) {
    return this.request(endpoint, { method: "DELETE" }, meta);
  }
}

export const apiClient = new ApiClient();
export default apiClient;
