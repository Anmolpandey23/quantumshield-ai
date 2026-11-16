# Integrated dashboard: how `frontend/` talks to `backend_dashboard/`

The dashboard has two modes, chosen by `frontend/.env`:

| `VITE_USE_MOCK_DATA` | Behaviour |
|---|---|
| `true` (default) | Bundled, clearly labelled demo data. No backend needed. Good for design work. |
| `false` | **Live.** Every page calls the FastAPI backend; a WebSocket (`/ws`) triggers a refresh whenever the pipeline produces an event. |

## Start everything (two terminals)
```bash
# terminal 1: backend
cd backend_dashboard && uvicorn app.main:app --port 8000
# terminal 2: dashboard
cd frontend && cp .env.example .env     # set VITE_USE_MOCK_DATA=false, VITE_API_BASE_URL=http://localhost:8000
npm install && npm run dev
```
Then either press **Run End-to-End Simulation** in the dashboard, or start the traffic generator:
`curl -X POST "http://localhost:8000/api/simulator/start?interval=3"` (or use the button on the backend's own page at `http://localhost:8000/`).

If the backend has `QS_API_KEY` set, put the same value in `frontend/.env` as `VITE_API_KEY`. It ships to the browser, so that is for demos only.
Cross-origin calls are allowed by `QS_CORS_ORIGINS` (default `*`; set it to the dashboard's real URL when you deploy).

## Where each page's data comes from
All routes are in `backend_dashboard/app/main.py`; the shaping logic is in `backend_dashboard/app/adapter.py`.

| Page | Endpoint | Built from |
|---|---|---|
| Overview | `GET /api/overview` | node table + event log. Posture = 100 minus the mean node risk. Health = share of nodes not isolated. PQC coverage = share of nodes holding a live key. MTTR = measured time from an `isolate` command to the next `reconnect`. The activity chart counts events per minute. |
| Threat Prediction | `GET /api/threats` | non-benign Stage 1 events (severity from risk score), per-minute max risk vs max anomaly score, per-label max risk. Accuracy/precision/recall show **n/a**: the pipeline does not measure them. Macro-F1 appears when `artifacts/metrics.json` exists. |
| Quantum Cryptography | `GET /api/crypto` | Stage 2 results: ML-KEM-768 and ML-DSA-65 status, live sessions (nodes holding their current key), average measured step timings (QRNG, BB84, ML-KEM, HKDF+AES, ML-DSA), key-rotation list. No classical timings exist, so that bar is hidden. |
| Self-Healing | `GET /api/healing` | isolate / reconnect / aborted / pending / rejected events as incidents; policies = the real Stage 3 guardrail settings; auto-remediation = share of commands not approved by a human. |
| Topology | `GET /api/topology` | one node per machine seen, plus a "controller" hub. Colour = status (healthy / warning = monitored / isolated). Isolated machines get a red broken link. Positions are a ring layout. |
| Pipeline Monitor | `GET /api/pipeline` | four stages with real events/sec. Stage 2 latency = average key-generation time. Other latencies, queue depth and uptime are not measured and show n/a / 0. |
| Simulation Center | `POST /api/simulation/{traffic,detection,crypto,healing,final}` | `traffic` injects the chosen scenario into the chosen number of simulated nodes and runs it through the **real** Stage 2 to 4 pipeline; the other stages report on that run. `hndl` (harvest-now-decrypt-later) puts an eavesdropper on every channel: BB84 must catch it and **no command is sent**. |
| Execution Logs | `GET /api/logs` | readable lines generated from the stored events (Stage 1 flag, Stage 2 channel, Stage 3 decision, Stage 4 signed command). |

## Honesty rules (kept on purpose)
* A number is either computed from real pipeline events or it is `null` / "n/a" / "—". Nothing is estimated.
* The "Demo data" badge appears only in demo mode. Surfaces that are always simulated (the Simulation Center, the Key Exchange Visualiser) keep their badge in live mode.
* In demo mode nothing is read from the backend, so demo values must never be quoted as results.

## Changing things
* New field on a page: add it to `frontend/src/types/quantumshield.ts`, to `adapter.py`, and to `backend_dashboard/tests/frontend_contract.py` (the test that keeps the two sides in step).
* Backend tests: `cd backend_dashboard && python -m pytest -q`. Frontend tests: `cd frontend && npm test`.
* The older prompt-based Lovable instructions in `docs/LOVABLE_CONNECTION.md` still work for a separate Lovable site; the REST endpoints and WebSocket are unchanged.

## Known limits
* A Simulation Center run at high intensity and many nodes does many real BB84 + ML-KEM + ML-DSA handshakes (about 30% of the nodes are attacked). On a slow machine lower `QS_N_QUBITS` (for example 256) before starting the backend.
* The frontend's server-side rendering fetches data from `VITE_API_BASE_URL` too. If the backend is down the page shows the "This page didn't load" screen; start the backend and press Try again.
* Topology positions are a ring, not your real network map. Feed real topology by extending `adapter.topology`.
* Public hosting of the dashboard needs the backend on a public https URL (see `docs/LOVABLE_CONNECTION.md`).
