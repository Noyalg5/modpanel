# ModPanel AI Platform — CLAUDE.md

This is the primary reference file for building the **ModPanel AI Platform**, a full-stack web application that uses AI and heuristic optimisation to support modern construction planning. This project is designed to align with the KTP (Knowledge Transfer Partnership) role: *Software Developer with AI in Modern Construction*.

---

## Project Overview

ModPanel AI Platform helps construction companies (like those using Structural Insulated Panels / modern methods of construction) to:

1. **Optimise panel layouts** for buildings using heuristic algorithms (minimise waste, maximise efficiency)
2. **Generate AI-assisted cost quotes** for modular building projects
3. **Manage projects** through a dashboard with milestones and reports
4. **Expose a REST API** for external system integration (e.g., CAD tools, BIM software)

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Clean REST APIs, auto-docs at `/docs`, beginner-friendly |
| Frontend | React 18 + Vite + Tailwind CSS | Fast to build, widely used |
| Database | SQLite (dev) → PostgreSQL (prod) | SQLite requires zero setup |
| AI | Anthropic Claude API (claude-haiku-3-5) | Natural language quoting & summaries |
| Optimisation | Custom Python — Genetic Algorithm | Core KTP technical deliverable |
| Auth | JWT (python-jose) | Simple token-based auth |

---

## Project Structure

```
modpanel/
├── CLAUDE.md                  ← this file (always read first)
├── README.md
├── .env.example               ← environment variable template
├── backend/
│   ├── main.py                ← FastAPI app entry point
│   ├── requirements.txt
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py            ← login, register, JWT
│   │   ├── projects.py        ← CRUD for construction projects
│   │   ├── panels.py          ← panel type definitions
│   │   ├── optimiser.py       ← trigger & retrieve optimisation runs
│   │   ├── quotes.py          ← cost quoting endpoints
│   │   └── reports.py         ← project report generation
│   ├── core/
│   │   ├── __init__.py
│   │   ├── optimiser/
│   │   │   ├── __init__.py
│   │   │   ├── genetic.py     ← genetic algorithm for panel layout
│   │   │   └── models.py      ← optimiser input/output schemas
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   └── claude_client.py  ← Anthropic API wrapper
│   │   └── config.py          ← settings loaded from .env
│   └── db/
│       ├── __init__.py
│       ├── database.py        ← SQLAlchemy setup
│       └── models.py          ← ORM models
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api/               ← axios API client functions
        ├── components/        ← reusable UI components
        └── pages/
            ├── Dashboard.jsx
            ├── Projects.jsx
            ├── Optimiser.jsx
            ├── Quote.jsx
            └── Reports.jsx
```

---

## Database Models

### User
- id, email, hashed_password, created_at

### Project
- id, user_id, name, description, location, status (draft/active/complete), created_at

### PanelType
- id, name, width_mm, height_mm, thickness_mm, material, cost_per_unit

### OptimisationRun
- id, project_id, wall_width_mm, wall_height_mm, panel_type_id, status, result_json, waste_percentage, created_at

### Quote
- id, project_id, ai_summary, total_cost, breakdown_json, created_at

### Report
- id, project_id, content_markdown, created_at

---

## Core Algorithms

### Genetic Algorithm (backend/core/optimiser/genetic.py)

Given:
- Wall dimensions (width × height)
- Panel dimensions (width × height)
- Constraints (no partial panels on edges, minimise cut waste)

Output:
- Best panel arrangement (grid positions)
- Waste percentage
- Number of full panels used
- Fitness score over generations

Implementation steps:
1. Represent a layout as a chromosome (list of panel placements)
2. Initialize a random population of N=50 layouts
3. Evaluate fitness = minimize waste + maximize coverage
4. Selection → crossover → mutation for 100 generations
5. Return best solution

---

## API Endpoints (FastAPI)

### Auth
- `POST /auth/register` — create account
- `POST /auth/login` — returns JWT token

### Projects
- `GET /projects` — list user's projects
- `POST /projects` — create project
- `GET /projects/{id}` — get single project
- `PUT /projects/{id}` — update
- `DELETE /projects/{id}` — delete

### Panels
- `GET /panels` — list available panel types
- `POST /panels` — add panel type (admin)

### Optimiser
- `POST /optimiser/run` — submit a new optimisation job
- `GET /optimiser/{run_id}` — get result of a run
- `GET /projects/{id}/optimisations` — all runs for a project

### Quotes
- `POST /quotes/generate` — generate AI-assisted quote for a project
- `GET /projects/{id}/quotes` — list quotes

### Reports
- `POST /reports/generate` — generate project summary report (AI)
- `GET /projects/{id}/reports` — list reports

---

## Frontend Pages

| Page | Route | Purpose |
|---|---|---|
| Dashboard | `/` | Summary: projects count, recent runs, KPIs |
| Projects | `/projects` | List, create, manage projects |
| Optimiser | `/projects/:id/optimise` | Input wall dims, run algorithm, view layout |
| Quote | `/projects/:id/quote` | View AI-generated cost quote |
| Reports | `/projects/:id/reports` | View and download project reports |

---

## Environment Variables (.env)

```
ANTHROPIC_API_KEY=your_key_here
SECRET_KEY=your_jwt_secret_here
DATABASE_URL=sqlite:///./modpanel.db
```

---

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API docs at http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# App at http://localhost:5173
```

---

## Build Order (for Claude Code)

Build strictly in this order — each phase depends on the previous:

1. **Backend foundation**: `db/database.py`, `db/models.py`, `core/config.py`
2. **Auth**: `api/auth.py` + JWT middleware
3. **Projects & Panels API**: CRUD endpoints
4. **Optimiser core**: `core/optimiser/genetic.py` + `api/optimiser.py`
5. **AI integration**: `core/ai/claude_client.py` + `api/quotes.py` + `api/reports.py`
6. **Frontend scaffold**: Vite + React + Tailwind + axios client
7. **Frontend pages**: Dashboard → Projects → Optimiser → Quote → Reports

---

## KTP Alignment

| KTP Requirement | Platform Feature |
|---|---|
| Heuristic optimisation algorithms | Genetic algorithm for panel layout |
| AI integration | Claude API for quoting and reports |
| Data engineering & API integration | REST API + structured DB schema |
| Modern Construction Methods | Panel-first design, DfMA principles |
| Research outputs / reports | Auto-generated project reports |
| Agile / iterative development | Phased milestone build order |

---

## Key Constraints

- Keep all functions under 50 lines — split into helpers if longer
- Every API endpoint must have a Pydantic request/response schema
- No hardcoded secrets — always use `.env`
- SQLite for development; all DB code must be compatible with PostgreSQL too (use SQLAlchemy, not raw SQL)
- Frontend API calls go through `src/api/` functions only — never fetch directly in components
