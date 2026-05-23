import { lazy, Suspense, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import SplashScreen from "./pages/SplashScreen";
import ProtectedRoute from "./components/ProtectedRoute";
import ErrorBoundary from "./components/ErrorBoundary";
import LoadingSpinner from "./components/LoadingSpinner";

// Lazy-loaded route components (requirement 17.1, 17.2, 17.3)
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Chatbot = lazy(() => import("./components/Chatbot"));
const Insights = lazy(() => import("./pages/Insights"));
const History = lazy(() => import("./pages/History"));
const ManageProfile = lazy(() => import("./pages/ManageProfile"));
const SafetyPlan = lazy(() => import("./pages/SafetyPlan"));
const Journal = lazy(() => import("./pages/Journal"));

// Preload critical routes after initial load (requirement 17.5)
function preloadCriticalRoutes() {
  import("./pages/Dashboard");
  import("./components/Chatbot");
}

function App() {
  useEffect(() => {
    // Delay preload by 2 seconds to avoid blocking initial render
    const timer = setTimeout(preloadCriticalRoutes, 2000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<SplashScreen />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <ErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <Dashboard />
                </Suspense>
              </ErrorBoundary>
            </ProtectedRoute>
          }
        />
        <Route
          path="/insights"
          element={
            <ProtectedRoute>
              <ErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <Insights />
                </Suspense>
              </ErrorBoundary>
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <ErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <History />
                </Suspense>
              </ErrorBoundary>
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <Chatbot />
                </Suspense>
              </ErrorBoundary>
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat/:sessionId"
          element={
            <ProtectedRoute>
              <ErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <Chatbot />
                </Suspense>
              </ErrorBoundary>
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Suspense fallback={<LoadingSpinner />}>
                <ManageProfile />
              </Suspense>
            </ProtectedRoute>
          }
        />
        <Route
          path="/safety-plan"
          element={
            <ProtectedRoute>
              <ErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <SafetyPlan />
                </Suspense>
              </ErrorBoundary>
            </ProtectedRoute>
          }
        />
        <Route
          path="/journal"
          element={
            <ProtectedRoute>
              <ErrorBoundary>
                <Suspense fallback={<LoadingSpinner />}>
                  <Journal />
                </Suspense>
              </ErrorBoundary>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<SplashScreen />} />
      </Routes>
    </Router>
  );
}

export default App;
