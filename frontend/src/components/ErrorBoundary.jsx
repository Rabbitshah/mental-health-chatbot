import React from "react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  handleReload() {
    window.location.reload();
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "100vh",
            padding: "2rem",
            textAlign: "center",
            fontFamily: "inherit",
          }}
        >
          <h2 style={{ marginBottom: "0.5rem" }}>Something went wrong</h2>
          <p style={{ color: "#666", marginBottom: "1.5rem" }}>
            An unexpected error occurred. Please try reloading the page.
          </p>
          <button
            onClick={this.handleReload}
            style={{
              padding: "0.6rem 1.4rem",
              backgroundColor: "#6c63ff",
              color: "#fff",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "1rem",
            }}
          >
            Reload page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
