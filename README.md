# QuantumShield AI

AI-driven post-quantum cybersecurity and self-healing network. **One repo: four backend stages plus the React dashboard.**

| Folder | Stage | What it does |
|---|---|---|
| `stage1_ai_threat_prediction/` | 1 | TabDDPM (synthetic attacks), CPC Transformer (normal behaviour), DyGNN (host risk on a changing graph), XAI reasons |
| `stage2_quantum_cryptography/` | 2 | QRNG, BB84 (eavesdropper detection), ML-KEM, ML-DSA, AES-256 hybrid key |
| `stage3_self_healing/` | 3 | PPO agent: isolate / monitor / reconnect, guardrails, human approval, node-side signature check |
| `backend_dashboard/` | 4 | FastAPI + WebSocket backend, SQLite log, built-in simple dashboard, **API for the React dashboard** (`app/adapter.py`) |
| `frontend/` | 4 | **React dashboard** (TanStack Start + Tailwind, built in Lovable): 8 pages, live over WebSocket |
| `contracts/` | | JSON Schemas = the agreed interface between stages |
| `integration/` | | The orchestrator that runs one attack start to finish |

## Run the backend (about 10 minutes)
```bash
python -m venv venv && source venv/bin/activate           # Windows: python -m venv venv ; .\venv\Scripts\Activate.ps1
pip install -r requirements-integration.txt
bash scripts/run_all_tests.sh                              # Windows: .\scripts\run_all_tests.ps1
bash scripts/train_all.sh                                  # trains Stage 1 + Stage 3 on synthetic data (~5 min CPU)
cd backend_dashboard && uvicorn app.main:app --port 8000   # http://localhost:8000 (simple page) and /docs (API)
```

## Run the React dashboard on top of it
```bash
cd frontend
cp .env.example .env            # Windows: copy .env.example .env
# edit .env:  VITE_USE_MOCK_DATA=false   (live)   or leave true (demo data, no backend needed)
npm install                     # or: bun install      (Node 20+)
npm run dev                     # open the URL it prints
```
In **live mode** every page reads the real pipeline, and a WebSocket refreshes them as events happen.
Press **Run End-to-End Simulation** (top bar) to inject an attack and watch it go through QRNG, BB84, ML-KEM, ML-DSA and self-healing.
Details: **`docs/INTEGRATED_DASHBOARD.md`**. Other guides: `docs/RUNBOOK.md`, `docs/DATASET_AND_TRAINING.md`, `docs/LOVABLE_CONNECTION.md`.

## The flow
`flows -> Stage 1 (label, confidence, risk, reason) -> Stage 2 secure channel (abort if eavesdropper) -> Stage 3 decision (guardrails, maybe human) -> ML-DSA signed command -> node verifies and obeys -> dashboard`
