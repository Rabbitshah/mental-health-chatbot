# Codebase Overview: AuraChat Mental Health Assistant

AuraChat is a modern, AI-powered mental health support application built with a **React-based frontend** and a **FastAPI-powered Python backend**. It leverages Google's **Gemini 2.5 Flash** model to provide empathetic, supportive conversations in a safe, private environment.

## 🚀 Core Functionalities

1.  **Empathetic AI Chat**: A core interaction point where users can talk about their feelings, anxiety, or stress. The AI is specifically prompted to be supportive and non-diagnostic.
2.  **Integrated Authentication**:
    *   **Email/Password**: Standard signup and login with secure bcrypt password hashing.
    *   **Google OAuth**: One-tap login/signup using Google accounts.
3.  **User Profile Management**: Allow users to update their personal information, change passwords, and manage preferences like dark mode and notifications.
4.  **Wellness Dashboard (Mocked)**: A central hub for tracking mood trends, streaks, and session frequency.
5.  **History & Insights (Mocked)**: Visual representations of past conversations and emotional patterns over time.

---

## 📄 Page-by-Page Breakdown

### 1. Splash Screen (`/`)
*   **Purpose**: The entry point and "front door" of the application.
*   **Contents**: High-level branding, mission statement ("Your safe space to think, feel, and heal"), and navigation to Signup or Login.
*   **How it works**: Uses `framer-motion` for elegant entry animations and a calming gradient background to set the tone.

### 2. Signup & Login (`/signup`, `/login`)
*   **Purpose**: User onboarding and authentication.
*   **Contents**: Forms for email, username, password, and a "Continue with Google" button.
*   **How it works**: Interacts with backend `/signup`, `/login`, and `/google-login` endpoints. Stores a JWT token and user metadata in `localStorage` upon success.

### 3. Dashboard (`/dashboard`)
*   **Purpose**: The user's personalized wellness hub.
*   **Contents**: Greeting, daily streak counter, session stats, a mood trend graph, recent conversation snippets, and recommended mental health exercises.
*   **How it works**: Displays the user's status at a glance. *Note: Currently uses mocked data for the visualizations.*

### 4. Chatbot (`/chat`)
*   **Purpose**: The primary interface for interacting with the AI.
*   *Contents**: A classic chat window with message bubbles, a "thinking" indicator, suggested quick-starts (e.g., "I'm feeling anxious"), and a warm sidebar navigation.
*   **How it works**: Sends user messages to the backend `/chat` endpoint, which prompts **Gemini 2.5 Flash** with a detailed "Mental Health System Prompt" to ensure safe and supportive responses.

### 5. Wellness Insights (`/insights`)
*   **Purpose**: Data-driven overview of the user's emotional journey.
*   **Contents**: Detailed mood trends, energy levels, stress tracking, and earned achievements (e.g., "7-Day Streak").
*   **How it works**: Visualizes patterns over weekly, monthly, or yearly periods. *Note: Currently uses mocked data for visualization.*

### 6. Chat History (`/history`)
*   **Purpose**: Reviewing past interactions.
*   **Contents**: A searchable and filterable list of previous conversations with tags (e.g., "Anxiety", "Stress"). Users can rename or delete past chats.
*   **How it works**: Organizes past sessions for easy retrieval. *Note: Currently uses mocked data.*

### 7. Settings / Manage Profile (`/profile`)
*   **Purpose**: Personalization and account control.
*   **Contents**: Profile info (name, email), account security (password change), Google connection status, theme preferences (Dark Mode), and data management (Export/Delete Account).
*   **How it works**: Directly updates user data in the database via the `/profile` endpoint and updates local application state.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | React, Vite, Lucide Icons, Framer Motion, Tailwind (via Vanilla CSS utilities) |
| **Backend** | FastAPI (Python), SQLAlchemy ORM |
| **AI Model** | Google Gemini 2.5 Flash |
| **Authentication** | JWT (JSON Web Tokens), Google OAuth 2.0 |
| **Database** | PostgreSQL / SQLite (managed via SQLAlchemy) |
| **Communication** | Axios with interceptors for Auth headers |
