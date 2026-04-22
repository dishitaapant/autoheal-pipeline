# 🔁 AutoHeal CI/CD Pipeline System

A production-style **self-healing CI/CD pipeline** that monitors GitHub Actions failures, automatically detects root causes, applies targeted fixes, retries pipelines, and displays everything on a live dashboard.

---

## 🏗 Architecture

```
GitHub Actions → Webhook → FastAPI Backend → Self-Healing Engine
                                ↓                     ↓
                           MongoDB            GitHub API (re-run)
                                ↓
                        React Dashboard (live polling)
```

---

## 📁 Folder Structure

```
autoheal-pipeline/
├── backend/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── routes/
│   │   ├── webhook.py           # Receives GitHub events
│   │   ├── pipelines.py         # Pipeline CRUD APIs
│   │   ├── analytics.py         # Analytics endpoint
│   │   └── health.py            # Health check
│   ├── services/
│   │   ├── log_analyzer.py      # Rule-based log parsing
│   │   ├── healing_engine.py    # Self-healing orchestrator
│   │   ├── pipeline_service.py  # DB operations
│   │   └── ml_predictor.py      # sklearn failure classifier
│   ├── models/
│   │   └── pipeline.py          # Pydantic data models
│   ├── utils/
│   │   └── database.py          # MongoDB + fallback in-memory DB
│   ├── tests/
│   │   └── test_main.py         # pytest test suite
│   ├── seed.py                  # Demo data seeder
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Router root
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx    # Main overview page
│   │   │   ├── Pipelines.jsx    # Pipeline list + filter
│   │   │   ├── PipelineDetail.jsx # Run detail + healing timeline
│   │   │   └── Analytics.jsx   # Charts & metrics
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── StatCards.jsx
│   │   │   ├── Charts.jsx       # Recharts components
│   │   │   ├── PipelineTable.jsx
│   │   │   ├── LogViewer.jsx
│   │   │   ├── HealingTimeline.jsx
│   │   │   └── UI.jsx           # Shared badges, spinner, etc.
│   │   ├── hooks/
│   │   │   └── useData.js       # Polling data hooks
│   │   └── utils/
│   │       └── api.js           # Axios API client
│   ├── public/index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── Dockerfile
├── .github/
│   └── workflows/
│       └── pipeline.yml         # GitHub Actions CI + webhook notify
├── docker-compose.yml
├── autoheal.code-workspace      # VS Code workspace
└── README.md
```

---

## ⚙️ Setup: Run in VS Code (Local Dev)

### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB 7 running locally **or** Docker Desktop

### Step 1 — Clone & open workspace

```bash
git clone <your-repo-url> autoheal-pipeline
cd autoheal-pipeline
code autoheal.code-workspace
```

### Step 2 — Start MongoDB

**Option A — Docker (recommended):**
```bash
docker run -d --name autoheal-mongo -p 27017:27017 mongo:7.0
```

**Option B — Local MongoDB:**  
Install from https://www.mongodb.com/try/download/community and start the service.

### Step 3 — Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env — add your GITHUB_TOKEN if you want real GitHub integration

# Optional: seed demo data
python seed.py

# Start the API server
uvicorn main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**  
API docs: **http://localhost:8000/docs**

### Step 4 — Frontend setup

```bash
cd frontend
npm install
npm start
```

Dashboard runs at: **http://localhost:3000**

### Step 5 — Trigger a demo failure

Click **"⚡ Trigger Demo Failure"** on the dashboard, or:

```bash
curl -X POST http://localhost:8000/api/webhook/test-failure
```

Watch the healing happen live on the dashboard.

---

## 🐳 Run with Docker Compose

```bash
# Copy and configure env file
cp backend/.env.example .env

# Build and start everything
docker-compose up --build

# Services:
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# MongoDB:   localhost:27017
```

## 🤖 Self-Healing Logic

| Failure Type | Actions Taken |
|---|---|
| `dependency_error` | Install dependencies → Clear cache → Retry pipeline |
| `build_error` | Clear build cache → Retry pipeline |
| `test_failure` | Re-run failed jobs → Full retry if needed |
| `timeout` | Clear cache → Retry with fresh state |
| `network_error` | Retry pipeline (transient error) |
| `configuration_error` | Fix configuration → Retry |
| `unknown` | Clear cache → Generic retry |

All actions use **exponential backoff** (default: 3 retries, 2s base delay doubling each attempt).

---

## 🧪 Run Tests

```bash
cd backend
pip install pytest httpx
pytest tests/ -v
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service info |
| `GET` | `/api/health/` | Health + DB status |
| `POST` | `/api/webhook/github` | Native GitHub webhook |
| `POST` | `/api/webhook/pipeline-failure` | Generic failure webhook |
| `POST` | `/api/webhook/test-failure` | Trigger demo failure |
| `GET` | `/api/pipelines/` | List all pipeline runs |
| `GET` | `/api/pipelines/{run_id}` | Get specific run |
| `GET` | `/api/pipelines/{run_id}/logs` | Get run logs |
| `GET` | `/api/pipelines/{run_id}/healing` | Get healing actions |
| `GET` | `/api/analytics/summary` | Analytics & charts data |

Interactive docs: **http://localhost:8000/docs**

---

## 🔑 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MONGO_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | `autoheal` | Database name |
| `GITHUB_TOKEN` | — | GitHub PAT with `repo` + `actions` scopes |
| `WEBHOOK_SECRET` | — | GitHub webhook secret for signature verification |
| `MAX_RETRIES` | `3` | Max healing retry attempts |
| `RETRY_BASE_DELAY` | `2.0` | Base delay (seconds) for exponential backoff |
| `MODEL_PATH` | `/tmp/autoheal_model.pkl` | Path to persist ML model |

---

## 🤖 ML Failure Predictor

The system includes a **TF-IDF + Logistic Regression** classifier (`backend/services/ml_predictor.py`) trained on labeled log snippets. It runs alongside the rule-based analyzer — whichever has higher confidence wins.

The model is trained on startup, saved to disk, and reloaded on subsequent starts. Add more training examples to `TRAINING_DATA` in `ml_predictor.py` to improve accuracy.

---

## 🛠 VS Code Tasks

Open the Command Palette (`Ctrl+Shift+P`) → **Tasks: Run Task**:

- `Install Backend Deps` — pip install
- `Install Frontend Deps` — npm install  
- `Start MongoDB (Docker)` — start local mongo container
- `Docker Compose Up` — full stack via Docker
- `Trigger Demo Failure` — fires a test webhook via curl

Or use the **Launch Configurations** (`F5`):
- `Backend: FastAPI` — starts uvicorn with reload
- `Frontend: React Dev` — starts CRA dev server
- `Full Stack` — starts both simultaneously
