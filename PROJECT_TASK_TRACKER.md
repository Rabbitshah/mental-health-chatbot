# Project Task Tracker

This file is the working tracker for the mental health chatbot project.

How this will be used:
- After each approved task, this file will be updated.
- Each item will be marked so we can track what is done and what is still pending.
- I will inform you when a task is completed, then wait for your approval before continuing to the next one.

Status key:
- `[ ]` Not started
- `[-]` In progress
- `[x]` Completed
- `[!]` Blocked / needs decision

## Missing Or Not Yet Fully Implemented

- `[x]` Fix frontend and backend email/password auth request mismatch.
  Details: frontend sends `identifier`, backend expects `email`.

- `[x]` Fix settings/profile API route mismatch.
  Details: frontend calls `/auth/profile` and `/auth/export`, backend exposes `/profile` and `/export`.

- `[x]` Implement real delete-all conversation history flow from settings.
  Details: current button only shows an alert.

- `[x]` Replace hardcoded sidebar recents with real session data from backend.

- `[x]` Connect sidebar rename/delete actions to backend history APIs.

- `[x]` Implement actual history date filters for `today`, `week`, and `month`.

- `[x]` Replace dashboard placeholder "Resume" behavior with real recent-session resume logic.

- `[x]` Replace static recommended content with data-backed or curated backend-driven recommendations.

- `[x]` Replace static insights summary cards with real analytics derived from stored data.

- `[x]` Implement real top discussion topics generation from chat/session data.

- `[x]` Implement achievement logic based on actual user activity.

- `[x]` Add a real data source for sleep-related insights or remove the unsupported sleep metric.

- `[x]` Implement behavior for chat attachment, emoji, help, and notification actions or remove them until supported.

- `[x]` Implement behavior for the sidebar "Get Help" action.

- `[x]` Generate or manage session tags/categories instead of leaving sessions mostly `General`.

- `[x]` Add account-management support for Google-auth users without local passwords.
  Details: current password-verified profile/delete flows do not fit passwordless accounts.

- `[x]` Move frontend API base URL to environment configuration instead of hardcoding localhost.

- `[x]` Add automated tests for auth, chat, history, and insights flows.

## Best Enhancements To Add Next

- `[x]` Add protected-route handling in the frontend for authenticated pages.

- `[x]` Add stronger crisis/safety handling beyond prompt-only LLM behavior.

- `[x]` Add streaming chat responses for better UX.

- `[x]` Add retry/regenerate response actions in chat.

- `[x]` Add message copy/share actions.

- `[x]` Add draft persistence for unfinished chat input.

- `[x]` Add better loading, error, and empty states across dashboard, history, insights, and settings.

- `[x]` Add full-text backend search for conversations.

- `[x]` Add bulk history actions such as delete/archive/select multiple.

- `[x]` Add session favorites/pinning/archive support.

- `[x]` Add better title generation for chat sessions.

- `[x]` Persist user preferences such as dark mode, language, and notification settings.

- `[x]` Add analytics improvements for mood trends, streaks, and correlations over time.

- `[x]` Add export/history/privacy controls with more complete user data management.

- `[x]` Add deployment-ready configuration cleanup for secrets, URLs, and environments.

## Update Log

- `2026-03-19`: Initial tracker created with missing functionality and enhancement backlog.
- `2026-03-19`: Fixed frontend email/password auth payload mismatch so login requests now send `email` instead of `identifier`.
- `2026-03-19`: Fixed settings/profile frontend API paths to match backend routes for profile update, password change, export, and account deletion.
- `2026-03-22`: Added a backend delete-all history route and connected the settings page "Delete Conversation History" action to it.
- `2026-03-22`: Replaced hardcoded sidebar recents with real backend session data and synced sidebar user display with local account data.
- `2026-03-23`: Connected sidebar rename and delete actions to backend history APIs and kept sidebar state in sync.
- `2026-03-23`: Implemented working history filters for today, week, and month using each session's creation date.
- `2026-03-23`: Replaced the dashboard resume placeholder with real latest-session resume behavior and dynamic session naming.
- `2026-03-23`: Moved dashboard recommendations to a backend-driven curated recommendations endpoint and connected the UI to it.
- `2026-03-23`: Replaced static insights summary cards with backend-generated analytics based on stored mood history.
- `2026-03-23`: Implemented backend-generated top discussion topics based on chat titles and message content, and connected the insights page to it.
- `2026-03-23`: Replaced static achievements with backend-generated achievement progress based on streaks, mood check-ins, morning check-ins, and session counts.
- `2026-03-23`: Removed the unsupported sleep metric from insights and replaced it with a real check-in rate metric derived from stored mood data.
- `2026-03-23`: Removed unsupported chat attachment, emoji, notification, and help controls from the chat screen and clarified that text chat is the currently supported mode.
- `2026-03-23`: Implemented the sidebar "Get Help" action as a support modal with emergency guidance, 988 contact action, and a clear safety disclaimer.
- `2026-03-23`: Added backend session tag inference in the chat flow so new and ongoing conversations are categorized beyond the default General tag when topic keywords are detected.
- `2026-03-23`: Added Google-account management support by treating passwordless users as a first-class case in profile update/delete flows and adapting the settings UI for Google sign-in accounts.
- `2026-03-23`: Moved the frontend API base URL to Vite environment configuration with a localhost fallback for development.
- `2026-03-23`: Added a first-pass backend test suite for auth, chat, history, and insights using a SQLite test database and a stubbed Gemini model.
- `2026-03-23`: Test execution could not be verified locally because the available Python launchers and checked virtualenv interpreters point to a blocked Windows Store Python shim.
- `2026-03-23`: Added a reusable frontend protected-route guard and applied it to dashboard, insights, history, chat, and profile routes.
- `2026-03-24`: Added deterministic backend crisis keyword detection and a direct emergency-support response so urgent harm-related messages no longer rely only on the LLM prompt.
- `2026-03-29`: Added progressive assistant response rendering in the chat UI so replies appear in a streaming-style flow instead of all at once.
- `2026-03-29`: Added retry/regenerate controls in chat so failed assistant replies can be retried and the latest prompt can be resent for a fresh response.
- `2026-03-29`: Added copy and native-share actions for assistant messages, with clipboard fallback when native sharing is unavailable.
- `2026-03-29`: Added per-session draft persistence for unfinished chat input so drafts survive refreshes and route changes until sent or cleared.
- `2026-03-29`: Added explicit loading, error, and empty states across dashboard, history, insights, and settings so data fetches fail more gracefully and empty screens are clearer.
- `2026-03-29`: Added backend conversation search across session titles, tags, and message text, and wired the history page to use that search API as the user types.
- `2026-03-29`: Added bulk history selection and deletion, including a backend bulk-delete endpoint, a multi-select toolbar in history, and backend test coverage for the bulk action flow.
- `2026-03-29`: Added session pin and archive support with backend status fields and endpoints, archived-view support in history, pinned recents in the sidebar, sync events between history and sidebar, and compatibility migration logic for existing databases.
- `2026-03-31`: Replaced first-message truncation with deterministic, topic-aware session title generation and added backend tests for both tagged and general conversation titles.
- `2026-04-03`: Persisted user preferences for dark mode, language, and notifications in the backend user model, surfaced them through profile payloads, and connected the settings page to load, save, and reset those preferences.
- `2026-04-03`: Added deeper analytics with a new insights patterns endpoint covering current streak, longest streak, best check-in day, and simple mood correlations, then rendered those patterns in the insights UI.
- `2026-04-03`: Expanded privacy and export controls with richer export payloads, a privacy summary endpoint, settings-page privacy metrics, and test coverage for preference/export data handling.
- `2026-04-03`: Added deployment-ready environment templates for backend and frontend plus README setup and production configuration guidance.
