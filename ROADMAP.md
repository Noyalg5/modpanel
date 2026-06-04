# ModPanel AI Platform — Build Roadmap

This roadmap breaks the project into 5 phases. Each phase produces something runnable and demonstrable — important for KTP project meetings and milestone reviews.

---

## Phase 1 — Backend Foundation (Week 1–2)

**Goal:** A working REST API with auth, project management, and panel types.

### Tasks
- [ ] Set up Python virtual environment and install FastAPI, SQLAlchemy, uvicorn, python-jose, pydantic
- [ ] Create `backend/core/config.py` — load `.env` variables
- [ ] Create `backend/db/database.py` — SQLAlchemy engine + session
- [ ] Create `backend/db/models.py` — User, Project, PanelType, OptimisationRun, Quote, Report ORM models
- [ ] Create `backend/api/auth.py` — register, login, JWT token generation
- [ ] Create `backend/api/projects.py` — CRUD endpoints for projects
- [ ] Create `backend/api/panels.py` — CRUD for panel types, seed 3 default types
- [ ] Create `backend/main.py` — wire all routers, add CORS middleware
- [ ] Test all endpoints via FastAPI auto-docs at `/docs`

### Deliverable
Running API at `http://localhost:8000` with auth + project management fully functional.

---

## Phase 2 — Heuristic Optimiser (Week 3–4)

**Goal:** The core technical engine — AI panel layout optimisation using a genetic algorithm.

### Tasks
- [ ] Create `backend/core/optimiser/models.py` — Pydantic schemas for optimiser input/output
- [ ] Create `backend/core/optimiser/genetic.py`:
  - `generate_population()` — random initial layouts
  - `evaluate_fitness()` — score based on waste minimisation
  - `select_parents()` — tournament selection
  - `crossover()` — produce child layout from two parents
  - `mutate()` — randomly shift panels
  - `run_optimisation()` — main loop, returns best layout
- [ ] Create `backend/api/optimiser.py` — POST to run, GET to retrieve result
- [ ] Store results as JSON in `OptimisationRun.result_json`
- [ ] Write unit tests for the genetic algorithm in `backend/tests/test_genetic.py`

### Deliverable
POST a wall size + panel type → receive an optimised panel layout with waste % and placement grid.

---

## Phase 3 — AI Integration (Week 5–6)

**Goal:** Claude API powers intelligent cost quoting and project report generation.

### Tasks
- [ ] Create `backend/core/ai/claude_client.py`:
  - `generate_quote(project, optimisation_run)` — prompt Claude to produce itemised cost quote
  - `generate_report(project, runs, quotes)` — prompt Claude to write a project summary report
- [ ] Create `backend/api/quotes.py` — POST to generate quote, GET to list quotes
- [ ] Create `backend/api/reports.py` — POST to generate report, GET to list reports
- [ ] Store quote output and report markdown in DB
- [ ] Add `.env` key: `ANTHROPIC_API_KEY`

### Sample Claude Prompt (quoting)
```
You are a construction cost estimator. Given the following project and panel layout data, produce an itemised quote in markdown format with:
- Number of panels required
- Cost per panel type
- Labour estimate (assume £45/hr, 2 hrs per panel)
- Total project cost
- Brief recommendation

Project: {project_name}
Wall area: {area} m²
Panel type: {panel_name}, cost: £{cost_per_unit} each
Panels needed: {panel_count}
Waste: {waste_pct}%
```

### Deliverable
Full AI-generated quote and markdown project report accessible via API.

---

## Phase 4 — Frontend (Week 7–10)

**Goal:** A usable browser-based UI connecting to the backend API.

### Tasks
- [ ] Scaffold frontend: `npm create vite@latest frontend -- --template react`
- [ ] Install Tailwind CSS, axios, react-router-dom, recharts
- [ ] Create `src/api/` client functions (one file per resource: auth.js, projects.js, optimiser.js, quotes.js, reports.js)
- [ ] Build pages:
  - `Dashboard.jsx` — project count, recent optimisation runs, KPI cards
  - `Projects.jsx` — list + create projects
  - `ProjectDetail.jsx` — single project: tabs for Optimiser, Quote, Reports
  - `Optimiser.jsx` — form: wall width/height + panel type → submit → show layout grid + waste %
  - `Quote.jsx` — show AI-generated quote as formatted markdown
  - `Reports.jsx` — show and download project report
- [ ] Add login/register pages with JWT token stored in memory (not localStorage)
- [ ] Deploy frontend proxy to backend in `vite.config.js`

### Deliverable
Full browser UI. Demo-ready for KTP project meetings.

---

## Phase 5 — Polish & Scale (Week 11+)

**Goal:** Production-readiness and KTP reporting features.

### Tasks
- [ ] Switch DB from SQLite to PostgreSQL (change `DATABASE_URL` in `.env` — no other code changes needed if SQLAlchemy is used correctly)
- [ ] Add pagination to all list endpoints
- [ ] Add optimiser comparison view — run multiple algorithms, compare results
- [ ] Add CSV export for quotes and reports (for submission to company/university)
- [ ] Add basic charting: fitness score over generations (recharts line chart)
- [ ] Write API integration tests
- [ ] Add Docker Compose setup: `docker-compose.yml` with backend + postgres + frontend services
- [ ] Write `README.md` with setup instructions

### Deliverable
Production-ready, containerised platform. Suitable for KTP milestone report and academic paper appendix.

---

## Scaling Path (KTP Milestones → Advanced Features)

Once the core platform is running, these extensions map directly to KTP research outputs:

| Extension | KTP Value |
|---|---|
| Simulated annealing optimiser (compare with GA) | Research comparison — publishable |
| IFC/BIM file parser to auto-extract wall dims | API integration with industry tools |
| Multi-storey optimisation | Significant technical advancement |
| Carbon footprint estimator per layout | Sustainability research output |
| Integration with Revit via plugin | Commercial deployment at Ultrapanel |
| Training materials + video walkthroughs | KTP knowledge embedding deliverable |

---

## How to Use This Roadmap with Claude Code

Open Claude Code in your project folder and give it instructions like:

```
Read CLAUDE.md first, then implement Phase 1. Start with backend/db/database.py and backend/db/models.py.
```

After each phase:
```
Phase 1 is done. Now implement Phase 2 — the genetic algorithm optimiser in backend/core/optimiser/genetic.py. Follow the build order in CLAUDE.md.
```

Claude Code will read CLAUDE.md on every task to maintain context about the architecture.
