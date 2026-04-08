# Mental Health Chatbot

A mental health chatbot application with React frontend and FastAPI backend.

## Getting Started

Copy the environment templates before running locally:

```bash
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Required backend environment variables:

- `DATABASE_URL`
- `SECRET_KEY`
- `GEMINI_API_KEY`
- `GOOGLE_CLIENT_ID`
- `CORS_ORIGINS`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Required frontend environment variables:

- `VITE_API_BASE_URL`

## Tech Stack

### Frontend

- React + Vite
- Tailwind CSS
- React Router
- Google OAuth

### Backend

- FastAPI
- PostgreSQL (SQLAlchemy)
- JWT Authentication
- Google Generative AI

## Available Scripts

### Frontend

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Backend

- `python -m uvicorn main:app --reload` - Start development server

## Deployment Notes

- Use separate production values for `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, and `GOOGLE_CLIENT_ID`.
- Set `CORS_ORIGINS` to your deployed frontend URL or a comma-separated list of allowed origins.
- Set `VITE_API_BASE_URL` in the frontend build environment so the app points to the deployed backend instead of localhost.
- Do not commit populated `.env` files with real secrets.
