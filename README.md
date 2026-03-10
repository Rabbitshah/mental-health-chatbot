# Mental Health Chatbot

A mental health chatbot application with React frontend and FastAPI backend.

## Getting Started

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

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
