import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Chatbot from "./components/Chatbot";
import ManageProfile from "./pages/ManageProfile";
import Dashboard from "./pages/Dashboard";
import SplashScreen from "./pages/SplashScreen";
import Insights from "./pages/Insights";
import History from "./pages/History";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SplashScreen />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/insights" element={<Insights />} />
        <Route path="/history" element={<History />} />
        <Route path="/chat" element={<Chatbot />} />
        <Route path="/profile" element={<ManageProfile />} />
        <Route path="*" element={<SplashScreen />} />
      </Routes>
    </Router>
  );
}

export default App;
