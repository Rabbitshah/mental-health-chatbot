/* eslint-disable react-refresh/only-export-components */
import { useState, useEffect, useCallback, createContext, useContext, useRef } from "react";

const ToastContext = createContext(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
}

let _addToast = null;

/** Call this outside React components (e.g. from ApiClient). */
export function showToast(message, type = "error") {
  if (_addToast) _addToast(message, type);
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const addToast = useCallback((message, type = "error") => {
    const id = ++idRef.current;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  useEffect(() => {
    _addToast = addToast;
    return () => {
      _addToast = null;
    };
  }, [addToast]);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div
        style={{
          position: "fixed",
          bottom: "1.5rem",
          right: "1.5rem",
          zIndex: 9999,
          display: "flex",
          flexDirection: "column",
          gap: "0.5rem",
          maxWidth: "360px",
        }}
        aria-live="polite"
        aria-atomic="false"
      >
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastItem({ toast, onDismiss }) {
  const isError = toast.type === "error";
  const isSuccess = toast.type === "success";

  const bg = isError ? "#EF4444" : isSuccess ? "#22C55E" : "#4A90D9";

  return (
    <div
      role="alert"
      style={{
        background: bg,
        color: "#fff",
        padding: "0.75rem 1rem",
        borderRadius: "10px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "0.75rem",
        fontSize: "0.875rem",
        lineHeight: "1.4",
        animation: "slideIn 0.2s ease-out",
      }}
    >
      <span>{toast.message}</span>
      <button
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
        style={{
          background: "transparent",
          border: "none",
          color: "#fff",
          cursor: "pointer",
          fontSize: "1rem",
          lineHeight: 1,
          padding: 0,
          flexShrink: 0,
        }}
      >
        ✕
      </button>
    </div>
  );
}
