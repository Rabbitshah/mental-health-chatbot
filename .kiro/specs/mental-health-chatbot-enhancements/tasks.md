# Implementation Plan: Mental Health Chatbot Enhancements

## Overview

This implementation plan transforms the mental health chatbot from a prototype into a production-ready application. The work is organized into logical phases covering security, core functionality, performance, frontend improvements, and observability. Each task builds incrementally, with checkpoints to ensure stability before proceeding.

## Tasks

- [x] 1. Set up infrastructure and database migrations
  - Create new database tables (refresh_tokens, crisis_events, notifications)
  - Add new columns to existing tables (chat_sessions.summary, chat_sessions.tag)
  - Create database indexes for performance optimization
  - Set up Redis connection and configuration
  - _Requirements: 3.5, 3.6, 12.1, 13.1, 13.2, 13.3, 13.4, 15.2_

- [x] 1.1 Write property test for database cascade deletion
  - **Property 7: Message Retrieval Ordering**
  - **Validates: Requirements 3.4**

- [x] 2. Implement authentication enhancements
  - [x] 2.1 Create refresh token models and database operations
    - Implement RefreshToken SQLAlchemy model
    - Add create_refresh_token() function
    - Add validate_refresh_token() function
    - Add revoke_refresh_token() function
    - _Requirements: 15.1, 15.2, 15.3, 15.5_
  
  - [x] 2.2 Write property test for refresh token validation
    - **Property 40: Refresh Token Database Storage**
    - **Property 41: Refresh Token Validation and Exchange**
    - **Validates: Requirements 15.2, 15.4**
  
  - [x] 2.3 Update login endpoint to issue refresh tokens
    - Modify POST /login to return both access and refresh tokens
    - Store refresh token in database on successful login
    - _Requirements: 15.1_
  
  - [x] 2.4 Create POST /auth/refresh endpoint
    - Implement token refresh logic
    - Validate refresh token against database
    - Issue new access token
    - _Requirements: 15.4, 15.6_
  
  - [x] 2.5 Write property test for authentication token validation
    - **Property 1: Authentication Token Validation**
    - **Property 2: Authenticated Request Processing**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
  
  - [x] 2.6 Update logout endpoint to revoke refresh tokens
    - Modify POST /logout to accept and revoke refresh token
    - _Requirements: 15.5_
  
  - [x] 2.7 Write unit tests for authentication flows
    - Test login with valid credentials
    - Test login with invalid credentials
    - Test token refresh with valid token
    - Test token refresh with expired token
    - Test logout revokes token

- [x] 3. Implement security middleware and validation
  - [x] 3.1 Configure CORS from environment variables
    - Read CORS_ORIGINS from .env
    - Validate CORS_ORIGINS is set on startup
    - Configure CORSMiddleware with environment values
    - _Requirements: 10.1, 10.2, 10.5_
  
  - [x] 3.2 Write property test for CORS origin validation
    - **Property 29: CORS Origin Validation**
    - **Validates: Requirements 10.5**
  
  - [x] 3.3 Create SecurityHeadersMiddleware
    - Implement middleware to add security headers to all responses
    - Add X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
    - Add Content-Security-Policy header
    - Add Strict-Transport-Security for production
    - _Requirements: 10.3, 10.4, 10.6_
  
  - [x] 3.4 Write property test for security headers
    - **Property 28: Security Headers on All Responses**
    - **Validates: Requirements 10.3, 10.4**
  
  - [x] 3.5 Implement input validation with Pydantic models
    - Create ChatRequest model with message length validation
    - Create MoodRequest model with range validation
    - Create UserCreate model with email validation
    - Add whitespace validation to message fields
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.6_
  
  - [x] 3.6 Write property tests for input validation
    - **Property 30: Input Validation Error Responses**
    - **Property 31: Whitespace-Only Input Rejection**
    - **Property 32: Email Format Validation**
    - **Validates: Requirements 11.2, 11.4, 11.6**

- [x] 4. Implement rate limiting
  - [x] 4.1 Set up SlowAPI rate limiter
    - Install slowapi package
    - Create custom key function using JWT user ID
    - Configure limiter with user-based tracking
    - Add rate limit exception handler
    - _Requirements: 2.3_
  
  - [x] 4.2 Apply rate limits to endpoints
    - Add @limiter.limit("10/minute") to POST /chat
    - Add @limiter.limit("100/hour") to POST /chat
    - Add @limiter.limit("20/minute") to POST /insights/mood
    - Add @limiter.limit("30/minute") to GET /search
    - Add @limiter.limit("5/hour") to GET /export
    - _Requirements: 2.1, 2.2_
  
  - [ ]* 4.3 Write property tests for rate limiting
    - **Property 3: Per-User Rate Limiting**
    - **Property 4: Rate Limit Response Headers**
    - **Validates: Requirements 2.3, 2.4, 2.6**
  
  - [ ]* 4.4 Write unit tests for rate limit enforcement
    - Test 10 requests per minute limit
    - Test 100 requests per hour limit
    - Test Retry-After header presence
    - Test rate limit counter reset

- [x] 5. Checkpoint - Ensure security tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Redis caching layer
  - [x] 6.1 Create Redis client and connection handling
    - Set up Redis connection with environment configuration
    - Implement get_redis_client() with error handling
    - Add connection timeout and retry logic
    - _Requirements: 12.1, 12.5_
  
  - [x] 6.2 Implement cache-aside pattern for session retrieval
    - Add caching to get_user_sessions()
    - Check cache before database query
    - Store results in cache with 5-minute TTL
    - _Requirements: 12.1, 12.2_
  
  - [x] 6.3 Implement cache invalidation on updates
    - Invalidate session cache when new message added
    - Invalidate session cache when session updated
    - Invalidate user sessions list cache on changes
    - _Requirements: 12.3_
  
  - [x] 6.4 Add caching for user profiles and mood analytics
    - Cache user profile data with 10-minute TTL
    - Cache mood analytics with 15-minute TTL
    - _Requirements: 12.4, 12.6_
  
  - [ ]* 6.5 Write property tests for caching behavior
    - **Property 33: Cache-First Data Retrieval**
    - **Property 34: Cache Population with TTL**
    - **Property 35: Cache Invalidation on Updates**
    - **Property 36: Graceful Cache Degradation**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**
  
  - [ ]* 6.6 Write unit tests for cache operations
    - Test cache hit scenario
    - Test cache miss scenario
    - Test cache invalidation
    - Test fallback when Redis unavailable

- [x] 7. Implement persistent chat session storage
  - [x] 7.1 Update POST /chat to create sessions
    - Check if session_id provided in request
    - Create new ChatSession if no session_id
    - Generate session title from first message
    - Store user message in database
    - _Requirements: 3.1, 3.2, 18.1_
  
  - [x] 7.2 Implement session title generation
    - Create generate_session_title() function
    - Truncate to 50 characters with "..." if needed
    - _Requirements: 18.1, 18.2_
  
  - [ ]* 7.3 Write property tests for session creation
    - **Property 5: Session Creation on First Message**
    - **Property 6: Message Persistence with Linkage**
    - **Property 43: Session Title Generation from First Message**
    - **Validates: Requirements 3.1, 3.2, 18.1, 18.2**
  
  - [x] 7.3 Store AI responses in database
    - Save AI message after receiving response
    - Link message to session with correct sender field
    - _Requirements: 3.3_
  
  - [x] 7.4 Implement GET /history endpoint
    - Return list of user's chat sessions
    - Order by updated_at descending
    - Include session metadata (title, tag, message count)
    - Add pagination support (page size 20)
    - _Requirements: 3.4, 13.5_
  
  - [x] 7.5 Implement GET /history/{session_id} endpoint
    - Retrieve all messages for session
    - Order messages by created_at ascending
    - Verify session belongs to authenticated user
    - _Requirements: 3.4_
  
  - [ ]* 7.6 Write property test for message retrieval ordering
    - **Property 7: Message Retrieval Ordering**
    - **Validates: Requirements 3.4**
  
  - [ ]* 7.7 Write unit tests for session storage
    - Test session creation on first message
    - Test message storage with correct linkage
    - Test cascade deletion of sessions and messages
    - Test session retrieval with pagination

- [x] 8. Implement contextual AI conversations
  - [x] 8.1 Retrieve conversation history for AI context
    - Load last 50 messages from session
    - Order messages chronologically (oldest first)
    - _Requirements: 4.1, 4.4_
  
  - [x] 8.2 Format conversation history for Gemini API
    - Convert messages to Gemini format (role: user/model)
    - Structure as list of {role, parts: [{text}]} objects
    - _Requirements: 4.2, 4.3_
  
  - [x] 8.3 Update AI service call to include history
    - Pass formatted history to model.start_chat()
    - Handle new sessions with empty history
    - _Requirements: 4.2, 4.5_
  
  - [ ]* 8.4 Write property tests for conversation context
    - **Property 8: Conversation History Retrieval**
    - **Property 9: AI Context Formatting**
    - **Validates: Requirements 4.1, 4.2, 4.3**
  
  - [ ]* 8.5 Write unit tests for AI context handling
    - Test history retrieval limited to 50 messages
    - Test correct message formatting for AI
    - Test new session with no history
    - Test history ordering (oldest first)

- [x] 9. Implement session tagging and categorization
  - [x] 9.1 Add tag field to ChatSession model
    - Update model with default tag "General"
    - Define allowed tag values
    - _Requirements: 5.1, 5.3_
  
  - [x] 9.2 Create PUT /history/{session_id} endpoint
    - Accept title and tag updates
    - Validate tag against allowed values
    - Validate title length (max 100 characters)
    - Update updated_at timestamp
    - _Requirements: 5.2, 5.6, 18.3, 18.4, 18.5_
  
  - [x] 9.3 Add tag filtering to GET /history
    - Accept optional tag query parameter
    - Filter sessions by tag if provided
    - _Requirements: 5.4_
  
  - [ ]* 9.4 Write property tests for session tagging
    - **Property 10: Default Session Tag Assignment**
    - **Property 11: Session Tag Validation**
    - **Property 12: Tag-Based Session Filtering**
    - **Property 13: Session Tag Update Persistence**
    - **Validates: Requirements 5.1, 5.2, 5.4, 5.6**
  
  - [ ] 9.5 Write unit tests for tagging functionality
    - Test default tag assignment
    - Test tag validation rejects invalid tags
    - Test tag filtering returns correct sessions
    - Test tag update persists correctly

- [ ] 10. Checkpoint - Ensure core functionality tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement mood tracking and analytics
  - [x] 11.1 Create POST /insights/mood endpoint
    - Accept mood_score, energy_level, stress_level
    - Validate values are between 1 and 10
    - Store MoodEntry with timestamp
    - _Requirements: 6.1, 6.4_
  
  - [x] 11.2 Create GET /insights/mood endpoint
    - Accept optional days parameter (default 7, max 365)
    - Return mood entries for specified period
    - Order by date ascending
    - _Requirements: 6.3, 6.5_
  
  - [x] 11.3 Create GET /insights/analytics endpoint
    - Accept optional start_date and end_date parameters
    - Calculate average, min, max for each metric
    - Calculate weekly and monthly averages
    - Determine trend (improving/declining/stable)
    - _Requirements: 6.2, 6.6_
  
  - [x] 11.4 Create GET /insights/stats endpoint
    - Return total_sessions count
    - Calculate mood_score_percent
    - Return journals count
    - Calculate day_streak for consecutive mood entries
    - _Requirements: 6.2_
  
  - [ ]* 11.5 Write property tests for mood tracking
    - **Property 15: Mood Entry Validation and Storage**
    - **Property 16: Mood Analytics Calculation**
    - **Property 17: Mood Trend Data Retrieval**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.6**
  
  - [ ]* 11.6 Write unit tests for mood analytics
    - Test mood entry validation rejects out-of-range values
    - Test default 30-day period when no range specified
    - Test analytics calculation accuracy
    - Test streak calculation

- [x] 12. Implement chat history search and filtering
  - [x] 12.1 Create GET /search endpoint
    - Accept query, tag, start_date, end_date parameters
    - Perform case-insensitive text search on messages
    - Filter by tag if provided
    - Filter by date range if provided
    - Return sessions with matching messages
    - Include message snippets with context
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [x] 12.2 Implement full-text search query
    - Use PostgreSQL full-text search or ILIKE
    - Search across message text field
    - Return sessions containing matches
    - _Requirements: 7.1, 7.2_
  
  - [ ]* 12.3 Write property tests for search functionality
    - **Property 18: Case-Insensitive Message Search**
    - **Property 19: Date Range Session Filtering**
    - **Property 20: Combined Search Filters**
    - **Property 21: Search Result Snippets**
    - **Validates: Requirements 7.1, 7.2, 7.4, 7.5, 7.6**
  
  - [ ]* 12.4 Write unit tests for search
    - Test case-insensitive search
    - Test tag filtering
    - Test date range filtering
    - Test combined filters
    - Test snippet generation with context

- [x] 13. Implement data export functionality
  - [x] 13.1 Create GET /export endpoint
    - Accept format parameter (json, csv, pdf)
    - Validate format value
    - _Requirements: 8.1, 8.2_
  
  - [x] 13.2 Implement JSON export
    - Gather all user sessions, messages, mood entries
    - Include export metadata (timestamp, user email)
    - Exclude sensitive data (password hashes)
    - Return JSON response
    - _Requirements: 8.1, 8.3, 8.4_
  
  - [x] 13.3 Implement CSV export
    - Generate separate CSV files for sessions, messages, moods
    - Include export metadata
    - Compress into ZIP archive
    - _Requirements: 8.2, 8.3, 8.5_
  
  - [ ]* 13.4 Write property tests for data export
    - **Property 22: Export Metadata Inclusion**
    - **Property 23: Export Data Sanitization**
    - **Validates: Requirements 8.3, 8.4**
  
  - [ ]* 13.5 Write unit tests for export
    - Test JSON export format
    - Test CSV export format
    - Test metadata inclusion
    - Test sensitive data exclusion
    - Test export completion within 30 seconds

- [x] 14. Implement crisis detection and resource recommendations
  - [x] 14.1 Create crisis detection service
    - Define CRISIS_KEYWORDS list in configuration
    - Implement detect_crisis() function
    - Scan message text for crisis keywords
    - Return detection result with matched keywords
    - _Requirements: 9.1, 9.5_
  
  - [x] 14.2 Create CrisisEvent model and logging
    - Implement CrisisEvent SQLAlchemy model
    - Create log_crisis_event() function
    - Store user_id, message_id, keywords, timestamp
    - _Requirements: 9.3_
  
  - [x] 14.3 Integrate crisis detection into chat endpoint
    - Call detect_crisis() on user messages
    - Log crisis events when detected
    - Augment AI response with emergency resources
    - Return crisis_detected flag in response
    - Do not censor or block user messages
    - _Requirements: 9.1, 9.2, 9.6_
  
  - [x] 14.4 Define emergency resources configuration
    - Create EMERGENCY_RESOURCES dictionary
    - Include hotline numbers and text services
    - Make configurable without code changes
    - _Requirements: 9.2, 9.5_
  
  - [ ]* 14.5 Write property tests for crisis detection
    - **Property 24: Crisis Keyword Detection**
    - **Property 25: Crisis Response Resource Inclusion**
    - **Property 26: Crisis Event Logging**
    - **Property 27: Message Preservation During Crisis Detection**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.6**
  
  - [ ]* 14.6 Write unit tests for crisis detection
    - Test detection of each crisis keyword
    - Test case-insensitive detection
    - Test crisis event logging
    - Test emergency resources in response
    - Test message not censored

- [x] 15. Implement conversation summarization
  - [x] 15.1 Add summary field to ChatSession model
    - Update model to include summary text field
    - _Requirements: 19.2_
  
  - [x] 15.2 Create generate_summary() function
    - Check if session has more than 10 messages
    - Call Gemini API to generate summary
    - Limit summary to 200 characters
    - Use first message as fallback on error
    - _Requirements: 19.1, 19.5, 19.6_
  
  - [x] 15.3 Integrate summary generation into chat flow
    - Generate summary after 10 messages
    - Regenerate after 20 new messages since last summary
    - Store summary in session record
    - _Requirements: 19.1, 19.4_
  
  - [x] 15.4 Include summary in session retrieval
    - Add summary to GET /history response
    - Display summary in session list
    - _Requirements: 19.2, 19.3_
  
  - [ ]* 15.5 Write property tests for summarization
    - **Property 46: Summary Storage and Retrieval**
    - **Property 47: Summary Length Constraint**
    - **Validates: Requirements 19.2, 19.3, 19.5**
  
  - [ ]* 15.6 Write unit tests for summarization
    - Test summary generation after 10 messages
    - Test summary regeneration after 20 new messages
    - Test summary length limit
    - Test fallback to first message on error

- [x] 16. Implement notification system
  - [x] 16.1 Create Notification model
    - Implement Notification SQLAlchemy model
    - Include type, message, read status, timestamp
    - _Requirements: 20.3_
  
  - [x] 16.2 Create notification preference storage
    - Add notification preferences to User model or settings table
    - Store frequency (daily, weekly, custom)
    - Store enabled status
    - _Requirements: 20.1, 20.2_
  
  - [x] 16.3 Create GET /notifications endpoint
    - Return pending notifications for user
    - Include unread count
    - _Requirements: 20.4, 20.5_
  
  - [x] 16.4 Create PUT /notifications/{id}/read endpoint
    - Mark notification as read
    - Update read status in database
    - _Requirements: 20.6_
  
  - [ ]* 16.5 Write property tests for notifications
    - **Property 48: Notification Preference Storage**
    - **Property 49: Notification Retrieval on Login**
    - **Property 50: Notification Dismissal and Read Status**
    - **Validates: Requirements 20.1, 20.2, 20.4, 20.5, 20.6**
  
  - [ ]* 16.6 Write unit tests for notifications
    - Test notification creation
    - Test notification retrieval
    - Test unread count calculation
    - Test marking notification as read

- [x] 17. Checkpoint - Ensure all backend features complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Implement comprehensive logging and monitoring
  - [x] 18.1 Set up structured logging
    - Configure Python logging with JSON formatter
    - Set log level from environment variable
    - Define log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - _Requirements: 16.4, 16.5_
  
  - [x] 18.2 Add request logging middleware
    - Log all API requests with timestamp, endpoint, user ID, status
    - Log response time
    - _Requirements: 16.1_
  
  - [x] 18.3 Add error logging
    - Log all exceptions with stack traces and request context
    - Include user ID and endpoint in error logs
    - _Requirements: 16.2_
  
  - [x] 18.4 Add AI service call logging
    - Log Gemini API calls with token usage and response time
    - Log AI service errors
    - _Requirements: 16.3_
  
  - [x] 18.5 Add rate limit violation logging
    - Log rate limit violations with user ID and endpoint
    - _Requirements: 16.6_
  
  - [ ]* 18.6 Write property test for structured logging
    - **Property 42: Structured Request Logging**
    - **Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.6**
  
  - [ ]* 18.7 Write unit tests for logging
    - Test request logging format
    - Test error logging includes stack trace
    - Test AI service logging includes metrics
    - Test rate limit logging

- [x] 19. Implement frontend error boundaries
  - [x] 19.1 Create ErrorBoundary component
    - Implement React error boundary class
    - Add getDerivedStateFromError method
    - Add componentDidCatch method
    - Create error fallback UI
    - _Requirements: 14.1, 14.2_
  
  - [x] 19.2 Wrap route components with ErrorBoundary
    - Wrap Dashboard, Chatbot, Insights, History routes
    - _Requirements: 14.1_
  
  - [ ]* 19.3 Write unit tests for error boundary
    - Test error boundary catches component errors
    - Test fallback UI displays
    - Test error logging to console

- [x] 20. Implement frontend API error handling
  - [x] 20.1 Create ApiClient class with retry logic
    - Implement request method with error handling
    - Add exponential backoff for retries
    - Determine which errors are retryable
    - _Requirements: 14.4_
  
  - [x] 20.2 Implement automatic token refresh
    - Detect 401 errors
    - Call /auth/refresh endpoint
    - Retry original request with new token
    - Redirect to login if refresh fails
    - _Requirements: 14.5, 15.3_
  
  - [x] 20.3 Add toast notifications for API errors
    - Display error toast on API failures
    - Show success toast on successful operations
    - _Requirements: 14.3_
  
  - [x] 20.4 Add console error logging
    - Log all errors to browser console
    - Include error context and stack trace
    - _Requirements: 14.6_
  
  - [ ]* 20.5 Write property tests for error handling
    - **Property 37: API Error Toast Notifications**
    - **Property 38: API Request Retry with Backoff**
    - **Property 39: Error Logging to Console**
    - **Validates: Requirements 14.3, 14.4, 14.6**
  
  - [ ]* 20.6 Write unit tests for API client
    - Test retry logic with exponential backoff
    - Test token refresh on 401
    - Test redirect to login on refresh failure
    - Test toast notifications on errors

- [x] 21. Implement frontend code splitting and lazy loading
  - [x] 21.1 Configure Vite for code splitting
    - Update vite.config.js with manual chunks
    - Separate vendor, charts, and UI libraries
    - _Requirements: 17.6_
  
  - [x] 21.2 Implement lazy loading for route components
    - Use React.lazy() for Dashboard, Chatbot, Insights, History
    - Wrap with Suspense and LoadingSpinner fallback
    - _Requirements: 17.1, 17.2, 17.3, 17.4_
  
  - [x] 21.3 Add route preloading
    - Preload critical routes (Dashboard, Chat) after initial load
    - Delay preload by 2 seconds to avoid blocking
    - _Requirements: 17.5_
  
  - [ ]* 21.4 Write unit tests for lazy loading
    - Test loading indicator displays during load
    - Test component renders after load
    - Test preloading triggers after delay

- [x] 22. Update frontend to display new features
  - [x] 22.1 Update Sidebar to show session tags
    - Display tag badge next to session title
    - _Requirements: 5.5, 18.6_
  
  - [x] 22.2 Add session tag editor to History page
    - Add dropdown to select tag
    - Call PUT /history/{id} on tag change
    - _Requirements: 5.6_
  
  - [x] 22.3 Add crisis banner component
    - Display prominent banner when crisis detected
    - Show emergency resources and hotline numbers
    - _Requirements: 9.4_
  
  - [x] 22.4 Add search interface to History page
    - Add search input and filter controls
    - Call GET /search endpoint
    - Display search results with snippets
    - _Requirements: 7.1, 7.6_
  
  - [x] 22.5 Add data export button
    - Add export button to profile or settings page
    - Allow format selection (JSON, CSV)
    - Trigger download on response
    - _Requirements: 8.1, 8.2_
  
  - [x] 22.6 Add notification bell icon
    - Display notification count badge
    - Show notification list on click
    - Mark notifications as read on dismiss
    - _Requirements: 20.4, 20.5, 20.6_
  
  - [x] 22.7 Display conversation summaries
    - Show summary below session title in history
    - _Requirements: 19.3_

- [x] 23. Update environment configuration
  - [x] 23.1 Add required environment variables to .env.example
    - Add CORS_ORIGINS
    - Add REDIS_HOST, REDIS_PORT
    - Add LOG_LEVEL
    - Add ENVIRONMENT (development/production)
    - _Requirements: 10.1, 10.2, 12.1, 16.5_
  
  - [x] 23.2 Update backend to validate required environment variables
    - Check CORS_ORIGINS is set on startup
    - Provide clear error messages for missing variables
    - _Requirements: 10.2_

- [x] 24. Final checkpoint - Run full test suite
  - Ensure all tests pass, ask the user if questions arise.

- [x] 25. Integration and final wiring
  - [x] 25.1 Verify all endpoints are protected with authentication
    - Ensure JWT dependency on all protected routes
    - _Requirements: 1.1_
  
  - [x] 25.2 Verify all endpoints have appropriate rate limits
    - Check rate limit decorators on all endpoints
    - _Requirements: 2.1, 2.2_
  
  - [x] 25.3 Test end-to-end user flows
    - Test signup → login → chat → mood tracking → export
    - Test session creation → tagging → search
    - Test crisis detection flow
    - Test token refresh flow
  
  - [x] 25.4 Verify database indexes are created
    - Run migration to create all indexes
    - Verify index creation with database inspection
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  
  - [x] 25.5 Test cache fallback behavior
    - Stop Redis and verify application continues working
    - _Requirements: 12.5_
  
  - [x] 25.6 Verify security headers on all responses
    - Test sample requests and inspect response headers
    - _Requirements: 10.3, 10.4, 10.6_

- [x] 26. Final checkpoint - Production readiness verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and integration points
- Checkpoints ensure incremental validation and provide opportunities for user feedback
- The implementation uses Python/FastAPI for backend and JavaScript/React for frontend
- Redis caching includes graceful degradation when cache is unavailable
- All authentication endpoints use JWT with refresh token mechanism
- Crisis detection augments responses but never censors user messages
