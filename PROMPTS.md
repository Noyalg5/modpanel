# ModPanel AI Platform — AI Coding Prompts

## How to use this file

1. Create a folder called `modpanel` on your computer
2. Copy `PROJECT.md` and `ROADMAP.md` into it
3. Open your terminal, `cd` into `modpanel`
4. Open your AI coding tool
5. Paste **one prompt at a time** — wait for it to finish before pasting the next

---

## PROMPT 1 — Backend Foundation

Paste this first. It builds the entire Python backend skeleton.

```
Read PROJECT.md carefully before doing anything.

Then implement Phase 1 — the backend foundation:

1. Create `backend/requirements.txt` with these packages:
   fastapi, uvicorn[standard], sqlalchemy, aiosqlite, python-jose[cryptography], passlib[bcrypt], pydantic-settings, python-multipart, anthropic

2. Create `.env.example`:
   ANTHROPIC_API_KEY=your_key_here
   SECRET_KEY=your_jwt_secret_change_this
   DATABASE_URL=sqlite+aiosqlite:///./modpanel.db

3. Create `backend/core/config.py` — use pydantic-settings BaseSettings to load from .env. Fields: ANTHROPIC_API_KEY, SECRET_KEY, DATABASE_URL, ACCESS_TOKEN_EXPIRE_MINUTES=60

4. Create `backend/db/database.py` — SQLAlchemy async engine using DATABASE_URL from config. Export: engine, AsyncSession, Base, get_db dependency.

5. Create `backend/db/models.py` — SQLAlchemy ORM models:
   - User: id, email (unique), hashed_password, created_at
   - Project: id, user_id (FK→User), name, description, location, status (enum: draft/active/complete), created_at
   - PanelType: id, name, width_mm, height_mm, thickness_mm, material, cost_per_unit (float)
   - OptimisationRun: id, project_id (FK→Project), panel_type_id (FK→PanelType), wall_width_mm, wall_height_mm, status (pending/complete/failed), result_json (Text), waste_percentage (float nullable), created_at
   - Quote: id, project_id (FK→Project), ai_summary (Text), total_cost (float), breakdown_json (Text), created_at
   - Report: id, project_id (FK→Project), content_markdown (Text), created_at

6. Create `backend/api/__init__.py` (empty)

7. Create `backend/api/auth.py` — FastAPI router with:
   - POST /auth/register — accepts email+password, hashes password with passlib, saves User, returns JWT token
   - POST /auth/login — verifies credentials, returns JWT token
   - get_current_user dependency that validates JWT and returns User

8. Create `backend/api/projects.py` — FastAPI router (requires auth) with:
   - GET /projects — list current user's projects
   - POST /projects — create project
   - GET /projects/{id} — get single project (must belong to user)
   - PUT /projects/{id} — update project
   - DELETE /projects/{id} — delete project

9. Create `backend/api/panels.py` — FastAPI router with:
   - GET /panels — list all panel types
   - POST /panels — create panel type
   Also create a startup function `seed_panels()` that inserts 3 default panel types if none exist:
   - Standard SIP 100mm: 1200×2400mm, cost £85
   - Insulated SIP 150mm: 1200×2400mm, cost £110
   - Structural SIP 200mm: 1200×2700mm, cost £145

10. Create `backend/main.py`:
    - Create FastAPI app
    - Add CORS middleware (allow all origins for development)
    - Include routers: auth, projects, panels
    - On startup: create all DB tables, run seed_panels()
    - Root route GET / returns {"status": "ModPanel API running"}

Use proper Pydantic v2 schemas for all request/response bodies. Keep each function under 50 lines.
```

---

## PROMPT 2 — Genetic Algorithm Optimiser

Paste this after Prompt 1 is complete.

```
Read PROJECT.md. Phase 1 is done. Now implement Phase 2 — the heuristic optimiser.

1. Create `backend/core/__init__.py` (empty)
2. Create `backend/core/optimiser/__init__.py` (empty)

3. Create `backend/core/optimiser/models.py` — Pydantic schemas:
   - OptimiserInput: wall_width_mm (int), wall_height_mm (int), panel_width_mm (int), panel_height_mm (int), population_size=50, generations=100
   - PanelPlacement: x (int), y (int), panel_number (int)
   - OptimiserResult: placements (list[PanelPlacement]), total_panels (int), waste_percentage (float), fitness_history (list[float]), best_generation (int)

4. Create `backend/core/optimiser/genetic.py` with these functions:

   a) `calculate_coverage(placements, wall_w, wall_h, panel_w, panel_h) -> float`
      — given a list of (x,y) positions, calculate what % of wall area is covered without overlap

   b) `evaluate_fitness(placements, wall_w, wall_h, panel_w, panel_h) -> float`
      — fitness = coverage_percentage - (overlap_penalty * 10)
      — penalise any panels placed outside wall bounds

   c) `generate_individual(wall_w, wall_h, panel_w, panel_h) -> list[tuple]`
      — generate a random list of (x, y) panel positions that fit within wall bounds
      — calculate how many panels can fit: n_cols = wall_w // panel_w, n_rows = wall_h // panel_h
      — return grid positions for all fitting panels with small random offsets

   d) `generate_population(size, wall_w, wall_h, panel_w, panel_h) -> list`
      — return list of `size` individuals

   e) `select_parents(population, fitnesses) -> tuple`
      — tournament selection: pick 3 random, return the best 2

   f) `crossover(parent1, parent2) -> list`
      — single-point crossover on the panel position lists

   g) `mutate(individual, wall_w, wall_h, panel_w, panel_h, rate=0.1) -> list`
      — with probability `rate`, randomly shift a panel by ±50mm

   h) `run_optimisation(input: OptimiserInput) -> OptimiserResult`
      — main loop: generate population, evaluate, select, crossover, mutate for N generations
      — track best fitness per generation
      — return OptimiserResult with best layout

5. Create `backend/api/optimiser.py` — FastAPI router (requires auth):
   - POST /optimiser/run — accepts project_id, panel_type_id, wall_width_mm, wall_height_mm
     → loads panel type from DB, runs run_optimisation(), saves OptimisationRun to DB, returns result
   - GET /optimiser/{run_id} — returns saved OptimisationRun
   - GET /projects/{project_id}/optimisations — list all runs for a project

6. Add the optimiser router to `backend/main.py`

Write a brief docstring on each function explaining what it does.
```

---

## PROMPT 3 — AI Integration

Paste this after Prompt 2 is complete.

```
Read PROJECT.md. Phases 1 and 2 are done. Now implement Phase 3 — AI integration using the AI model API.

1. Create `backend/core/ai/__init__.py` (empty)

2. Create `backend/core/ai/claude_client.py` with two async functions:

   a) `generate_quote(project_name: str, wall_area_m2: float, panel_name: str, cost_per_unit: float, panel_count: int, waste_pct: float) -> dict`
   
   Build this prompt and send to the AI model (claude-haiku-4-5):
   
   "You are a construction cost estimator. Produce an itemised quote in markdown for:
   Project: {project_name}
   Wall area: {wall_area_m2:.1f} m²
   Panel type: {panel_name} at £{cost_per_unit:.2f} each
   Panels needed: {panel_count}
   Waste: {waste_pct:.1f}%
   
   Include: panel material cost, labour (£45/hr, 1.5 hrs per panel), delivery estimate (£250 flat), subtotal, VAT (20%), total.
   End with a one-sentence recommendation."
   
   Return: {"ai_summary": <full markdown response>, "total_cost": <extracted float>, "breakdown_json": <json string of line items>}

   b) `generate_report(project_name: str, location: str, runs_summary: str, quotes_summary: str) -> str`
   
   Build this prompt:
   
   "Write a professional project progress report in markdown for a KTP (Knowledge Transfer Partnership) construction project.
   Project: {project_name}, Location: {location}
   Optimisation runs completed: {runs_summary}
   Quotes generated: {quotes_summary}
   
   Include sections: Executive Summary, Technical Progress, Optimisation Results, Cost Analysis, Next Steps.
   Keep it concise and suitable for a university-industry review meeting."
   
   Return the markdown string.

3. Create `backend/api/quotes.py` — FastAPI router (requires auth):
   - POST /quotes/generate — accepts project_id and optimisation_run_id
     → loads project + run + panel type from DB
     → calls generate_quote()
     → saves Quote to DB
     → returns Quote
   - GET /projects/{project_id}/quotes — list all quotes for project

4. Create `backend/api/reports.py` — FastAPI router (requires auth):
   - POST /reports/generate — accepts project_id
     → loads project, all its optimisation runs, all its quotes
     → calls generate_report()
     → saves Report to DB
     → returns Report
   - GET /projects/{project_id}/reports — list all reports

5. Add quotes and reports routers to `backend/main.py`

Use the `anthropic` Python SDK. Load ANTHROPIC_API_KEY from config. Handle API errors gracefully with HTTPException 502.
```

---

## PROMPT 4 — Frontend

Paste this after Prompt 3 is complete.

```
Read PROJECT.md. The backend (Phases 1-3) is complete. Now build the React frontend (Phase 4).

1. In the `frontend/` folder, create `package.json` with these dependencies:
   - react, react-dom, react-router-dom
   - axios
   - recharts (for charts)
   - tailwindcss, @tailwindcss/vite
   - vite, @vitejs/plugin-react

2. Create `frontend/vite.config.js`:
   - Use @vitejs/plugin-react and @tailwindcss/vite plugins
   - Add server proxy: /api → http://localhost:8000 (strip /api prefix)

3. Create `frontend/index.html` — standard Vite HTML entry

4. Create `frontend/src/main.jsx` — render <App /> into #root

5. Create `frontend/src/api/` folder with these files (all use axios with base URL /api):
   - `auth.js` — login(email, password), register(email, password)
   - `projects.js` — getProjects(), getProject(id), createProject(data), updateProject(id, data), deleteProject(id)
   - `panels.js` — getPanels()
   - `optimiser.js` — runOptimisation(data), getOptimisationRun(id), getProjectOptimisations(projectId)
   - `quotes.js` — generateQuote(projectId, runId), getProjectQuotes(projectId)
   - `reports.js` — generateReport(projectId), getProjectReports(projectId)
   
   Store JWT token in a module-level variable (not localStorage). Add it to axios Authorization header automatically.

6. Create these pages in `frontend/src/pages/`:

   a) `Login.jsx` — email/password form, calls auth.login(), stores token, redirects to /

   b) `Register.jsx` — email/password form, calls auth.register(), redirects to /login

   c) `Dashboard.jsx` — shows:
      - Total projects count
      - Total optimisation runs count
      - A welcome message
      - Button: "New Project"

   d) `Projects.jsx` — list of user projects as cards. Each card shows name, location, status badge, and a "View" button. "New Project" button opens a simple inline form.

   e) `ProjectDetail.jsx` — three tabs: Optimiser | Quotes | Reports
      - Optimiser tab: form for wall_width_mm, wall_height_mm, panel_type dropdown. Submit runs optimisation. Shows result: waste %, panel count, and a simple grid visualisation (CSS grid of coloured boxes representing panels).
      - Quotes tab: button "Generate Quote from latest run". Shows quote as rendered markdown.
      - Reports tab: button "Generate Report". Shows report as rendered markdown.

7. Create `frontend/src/App.jsx`:
   - Use react-router-dom with routes: /, /login, /register, /projects, /projects/:id
   - Redirect unauthenticated users to /login
   - Include a simple top navbar with project name and logout button

Use Tailwind utility classes for all styling. Keep components simple and clean.
```

---

## PROMPT 5 — Final Polish & Testing

Paste this after Prompt 4 is complete.

```
Read PROJECT.md. All four phases are complete. Now do the final polish:

1. Create `backend/tests/__init__.py` (empty)

2. Create `backend/tests/test_genetic.py` — pytest tests for the genetic algorithm:
   - test that generate_individual() returns positions within wall bounds
   - test that evaluate_fitness() returns a value between 0 and 100
   - test that run_optimisation() returns an OptimiserResult with waste_percentage >= 0
   - test that more generations produces equal or better fitness than fewer

3. Create `README.md` in the project root with:
   - Project overview (2 sentences)
   - Setup instructions for backend (create venv, pip install -r requirements.txt, copy .env.example to .env, uvicorn main:app --reload)
   - Setup instructions for frontend (npm install, npm run dev)
   - Link to API docs: http://localhost:8000/docs
   - Brief description of each feature

4. Add input validation to the optimiser API endpoint:
   - wall_width_mm and wall_height_mm must be between 500 and 50000
   - Return HTTP 422 with a clear message if invalid

5. In `backend/main.py`, add a GET /health endpoint that returns:
   {"status": "ok", "version": "1.0.0", "db": "connected"}

6. Make sure all files have proper Python type hints throughout.

After completing all of this, give me a summary of every file created and the command to start both the backend and frontend.
```

---

## After All Prompts Are Done

Start the app:

```bash
# Terminal 1 — backend
cd modpanel/backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env    # then edit .env and add your ANTHROPIC_API_KEY
uvicorn main:app --reload

# Terminal 2 — frontend
cd modpanel/frontend
npm install
npm run dev
```

Then open:
- App: http://localhost:5173
- API docs: http://localhost:8000/docs
