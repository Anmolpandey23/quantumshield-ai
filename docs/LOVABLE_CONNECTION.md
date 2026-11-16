# Connecting your Lovable website to the backend

> **The Lovable dashboard is now included in this repo as `frontend/` and is already wired to the backend.** Start with `docs/INTEGRATED_DASHBOARD.md`. This page stays useful for the raw REST/WebSocket contract and for hosting.

## 1. Make the backend reachable
Lovable pages are served over **https** from the internet, so they cannot call `http://localhost:8000`. Pick one:

**A. Tunnel (quickest, for demos).** Keep the backend running, then in another terminal:
```bash
cloudflared tunnel --url http://localhost:8000      # or:  ngrok http 8000
```
It prints a public `https://....` address. That is your `BACKEND_URL`.

**B. Deploy (stable).** Render / Railway / Fly.io: start command
`uvicorn app.main:app --host 0.0.0.0 --port $PORT` with working directory `backend_dashboard` (install `requirements-integration.txt`).

Set these environment variables before starting the backend (see `backend_dashboard/.env.example`):
```
QS_CORS_ORIGINS=https://your-project.lovable.app     # your Lovable URL; comma-separate several
QS_API_KEY=pick-a-long-random-string                 # required for anything public
```
Then in Lovable, send header `X-API-Key: <that key>` on every call. (A key in browser code is visible to visitors: fine for a demo, for real use put a login or proxy in front.)

## 2. REST endpoints (all JSON, interactive docs at `BACKEND_URL/docs`)
| Method + path | Returns |
|---|---|
| `GET /api/health` | `{status, mode:{stage1,stage3}, n_qubits}` (no key needed) |
| `GET /api/stats` | KPI numbers: `threats_flagged, key_exchanges_ok, eavesdrop_aborts, isolations, reconnections, nodes_total, nodes_isolated, nodes_monitored, pending_approvals, avg_key_gen_ms, avg_qber_clean, avg_qber_eve, threat_breakdown{label:count}, simulator{running}` |
| `GET /api/nodes` | `[{node_id, status(online/monitored/isolated), threat_label, risk_score_node, confidence, anomaly_score, explanation[], key_id, critical, last_seen}]` |
| `GET /api/events?limit=50&node_id=&decision=` | newest-first pipeline events (the `pipeline_event` contract + `id`) |
| `GET /api/keys?limit=50` | key exchanges: `{timestamp,node_id,status,qber,key_gen_time_ms,eavesdrop_detected,shared_key_id,timings_ms}` |
| `GET /api/approvals` | `[{approval_id,node_id,action,reason,created}]` |
| `POST /api/approvals/{id}/approve` / `/reject` | body `{"approver":"name"}` |
| `POST /api/simulate/attack` \| `eavesdrop` \| `clean` | one demo event (button actions) |
| `POST /api/simulator/start?interval=3` / `stop` | background traffic generator |
| `POST /api/events/stage1?eve_fraction=0` | push a Stage 1 result (body = `contracts/stage1_output`) |
| `POST /api/ingest/flows` | body `{"flows":[...CIC rows + Source IP, Destination IP, Timestamp]}` runs the real Stage 1 models |
| `POST /api/reset` | clears everything |

Event `decision` values: `no_action`, `aborted_no_command` (eavesdropper), `command_issued`, `command_rejected`, `pending_human_approval`.

## 3. Live updates (WebSocket)
`wss://BACKEND_URL_HOST/ws?api_key=KEY` sends first `{"type":"snapshot","nodes","stats","pending","events"}`, then on every change `{"type":"event","event":{...}|null,"nodes","stats","pending"}`. Replace your state with `nodes/stats/pending`, and prepend `event` to the feed.

## 4. Prompt you can paste into Lovable
> Build a dark "security control room" dashboard. Config: `BACKEND_URL` and `API_KEY` constants. On load, open a WebSocket to `${BACKEND_URL.replace('http','ws')}/ws?api_key=${API_KEY}` (auto-reconnect). Message `snapshot` and `event` carry `nodes`, `stats`, `pending`, `event`. Show: (1) KPI cards from `stats`; (2) a machines table from `nodes` (colour status: online green, monitored amber, isolated red; risk bar from `risk_score_node`; star if `critical`); (3) a live feed from `event` rows showing Stage 1 label, confidence and `explanation`, Stage 2 result with QBER (green "secure" or red "eavesdropper detected, no command sent"), and Stage 3 command with "signature verified"; (4) a key-exchange table from `GET /api/keys`; (5) an "Awaiting approval" panel from `pending` with Approve/Reject buttons calling `POST /api/approvals/{id}/approve|reject` with header `X-API-Key`; (6) buttons "Simulate attack", "Attack + eavesdropper", "Clean traffic" (`POST /api/simulate/attack|eavesdrop|clean`) and a Start/Stop live simulator toggle. Send header `X-API-Key` on all REST calls.

The built-in page at `BACKEND_URL/` shows the same thing and is a working reference for your Lovable code.
