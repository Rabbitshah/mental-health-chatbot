import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Chatbot from "./components/Chatbot";
import ManageProfile from "./pages/ManageProfile";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/chat" element={<Chatbot />} />
        <Route path="/profile" element={<ManageProfile />} />
        <Route path="*" element={<Login />} />
      </Routes>
    </Router>
  );
}

export default App;
