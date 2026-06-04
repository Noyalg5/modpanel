# ModPanel AI Platform

An AI-powered platform for modern construction planning using Structural Insulated Panels (SIP). Built as part of a KTP (Knowledge Transfer Partnership) with Ultrapanel Building Technology Ltd.

## Features
- **AI Panel Layout Optimiser** — genetic algorithm that minimises material waste
- **AI Cost Quoting** — AI generates itemised construction quotes
- **Project Reports** — AI-written KTP-style progress reports
- **Project Management** — dashboard to manage construction projects

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
uvicorn main:app --reload
```
API docs available at: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App available at: http://localhost:5173

### Run Tests
```bash
cd backend
pytest tests/ -v
```

## Tech Stack
- Backend: Python, FastAPI, SQLAlchemy, SQLite
- AI: AI Provider API
- Optimisation: Custom Genetic Algorithm
- Frontend: React, Vite, Tailwind CSS
