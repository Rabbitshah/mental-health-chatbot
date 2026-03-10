# Mental Health Chatbot Analysis Report

This brief covers the architecture, functionality, and identified issues (including missing features and security concerns) of the React frontend and FastAPI backend.

---

## 1. Backend Architecture & Functionality

The backend is built with FastAPI and PostgreSQL (using SQLAlchemy) and connects to the Google Gemini AI.

### **Core Structure**
- [main.py]: The entry point. It sets up CORS (hardcoded to `http://localhost:5173`) and includes routes for traditional auth, google auth, and the chat API.
- [database.py]: Establishes the Postgres connection and provides a dependency for DB sessions.
- [models.py]: Defines the [User](#4-14) schema (id, email, name, username, password, google_id, picture).
- [jwt_handler.py]: Handles creation and decoding of JWT access tokens.
- [utils.py]: Contains bcrypt password hashing functions.

### **Routes**
- **`/auth/signup` & `/auth/login`**: Standard email/password authentication returning a JWT token.
- **`/auth/profile`**: PUT route to update user profile details, protected by JWT.
- **`/google-login`**: Handles Google OAuth ID token verification and user creation/login.
- **`/chat`**: The core AI route. It takes a user message, prepends a detailed mental health system prompt, and calls `gemini-2.5-flash` to generate a response. 

### **Backend Missing Functionality & Issues**
1. **Missing Chat History Database Models**: The [models.py](#4-14) only contains a [User](#4-14) table. There are no tables for `ChatSession`, `ChatMessage`, or `InsightData`. Because of this, conversations cannot be saved or retrieved.
2. **Stateless AI Chat**: The `/chat` endpoint only sends the *current* user message and the system prompt to Gemini. It does not send previous messages in the conversation, so the AI has no memory of the ongoing conversation context.
3. **No Endpoints for Dashboard/Insights/History**: The frontend has pages for Dashboard, History, and Insights, but the backend lacks the corresponding API routes to provide this data.

### **Backend Security Concerns**
1. **Hardcoded CORS Origin**: [main.py] hardcodes the allowed origin to `http://localhost:5173`. In production, this needs to be configurable via environment variables to prevent unauthorized cross-origin requests.
2. **Missing Rate Limiting**: The `/chat` endpoint directly calls the Gemini API without rate-limiting specific users. A malicious actor could easily exhaust the application's Gemini API quota.
3. **Lack of User Authorization on Chat Endpoint**: The `/chat` endpoint ([routes/chat.py]) does *not* require a JWT token token dependency (e.g., `Depends(get_current_user)`). Anyone can hit the `/chat` endpoint without being logged in, bypassing the authentication system entirely.
4. **JWT Expiry Fixed**: The `ACCESS_TOKEN_EXPIRE_MINUTES` is functionally hardcoded to 60 minutes in [jwt_handler.py]. 

---

## 2. Frontend Architecture & Functionality

The frontend is a React application built with Vite, Tailwind CSS, and `lucide-react` for icons. It uses React Router for navigation.

### **Core Structure & Routing ([App.jsx])**
- `/` -> [SplashScreen.tsx]
- `/signup` -> [Signup.jsx]
- `/login` -> [Login.jsx]
- `/dashboard` -> [Dashboard.jsx]
- `/insights` -> [Insights.jsx]
- `/history` -> [History.jsx]
- `/chat` -> [Chatbot.jsx]
- `/profile` -> [ManageProfile.jsx]

### **Key Components Functionality**
- **[Sidebar.jsx]**: Provides the main navigation menu structure used across all authenticated pages. It handles local state for "recent chats" but does not fetch them from an API.
- **[Chatbot.jsx]**: 
  - Checks for a token in `localStorage` on mount to protect the route on the client side.
  - Maintains `messages` in local React state.
  - Calls `API.post("/chat")` to communicate with the backend.
  - **Issue**: Since state is local, refreshing the page clears the entire chat conversation.
- **[Dashboard.jsx]**: Displays user greeting, recent conversations, mood trends, and health statistics.
  - **Issue**: All data (conversations, mood data, stats) is entirely **hardcoded mock data**. It does not fetch anything from the backend.
- **[History.jsx]**: Displays a searchable, filterable list of past conversations. Allows renaming and deleting.
  - **Issue**: Uses hardcoded state. Deleting/renaming only changes local React state and is lost on refresh.
- **[Insights.jsx]**: Displays detailed graphs for mood, energy, stress, and sleep.
  - **Issue**: Entirely hardcoded mock data.
- **[ManageProfile.jsx]**: Allows UI toggles for Dark Mode, Notifications, Data Export, and Account Deletion.
  - **Issue**: None of these actions (besides the basic profile text fields which aren't wired properly to the backend `PUT` route) actually trigger backend API calls. The "Password Change" and "Delete Account" buttons just trigger JavaScript `alert()` popups.

### **Frontend Missing Functionality & Issues**
1. **Mock Data Everywhere**: History, Dashboard, and Insights pages are purely visual shells right now. They need to be wired up to actual backend endpoints.
2. **No Global State Management**: The app relies heavily on `localStorage` for the user context but lacks a context provider (e.g., React Context or Redux) to manage global user state, theme preferences, or notification settings.
3. **Logout Flow**: The logout button in the [Sidebar] clears `localStorage` and navigates to `/`, but it doesn't invalidate the token on the backend (standard for stateless JWT, but worth noting).

### **Frontend Security Concerns**
1. **Client-Side Only Route Protection**: The [Chatbot.jsx] component checks `localStorage.getItem("token")` to decide if a user is logged in. A user could manually add a fake token to `localStorage` to access the chat page. *Note: Because the backend `/chat` endpoint lacks authorization, a user doing this could actually use the AI chat for free.*
2. **XSS Potential in Chat**: The chat messages are rendered directly into the DOM (`<p>{message.text}</p>`). While React escapes strings by default, if markdown rendering is added later without proper sanitization (like DOMPurify), it could lead to Cross-Site Scripting (XSS).

---

## 3. Executive Summary of Next Steps

To make this application a fully functional and secure product, the following needs to be implemented:

1. **Secure the `/chat` Endpoint**: Add JWT authorization dependency to the backend chat route immediately to prevent unauthorized API cost accumulation.
2. **Implement Rate Limiting**: Add `slowapi` or similar rate limiting to the FastAPI server.
3. **Database Expansion**: Create SQLAlchemy models for `ChatSession` and `Message`.
4. **Contextual AI**: Update the `/chat` endpoint to fetch previous messages from the database and send the full conversation array to Gemini.
5. **Develop Missing API Routes**: Create GET endpoints for user history, mood trends, and dashboard stats.
6. **Connect Frontend to Backend**: Replace the hardcoded mock arrays in [Dashboard], [History], and [Insights] with `useEffect` Axios calls to the new API endpoints.
