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

