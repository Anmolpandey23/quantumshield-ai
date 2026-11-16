# QuantumShield AI — Frontend

AI-Driven Post-Quantum Cybersecurity & Self-Healing Network dashboard.
**Frontend only.** Every number on screen is clearly labelled sample / demo data —
nothing here is a real security result.

Built with React 19, TypeScript, Tailwind CSS v4, Framer Motion, Recharts and
TanStack Start (file-based routing, Vite).

---

## 1. Run locally

Requirements: **Node.js 20+** (or [Bun](https://bun.sh) 1.1+).

```bash
# install dependencies
npm install          # or: bun install

# optional: configure the API
cp .env.example .env

# start the dev server
npm run dev          # or: bun run dev
```

Open the URL printed in the terminal (usually http://localhost:8080 or :3000).

Other scripts:

| Command           | What it does                    |
| ----------------- | ------------------------------- |
| `npm run build`   | Production build                |
| `npm run preview` | Serve the production build      |
| `npm test`        | Run unit tests (Vitest)         |
| `npm run lint`    | Lint the project                |

---

## 2. Pages

| URL             | Page                  |
| --------------- | --------------------- |
| `/`             | Overview Dashboard    |
| `/threats`      | AI Threat Prediction  |
| `/cryptography` | Quantum Cryptography  |
| `/self-healing` | Self-Healing Network  |
| `/topology`     | Network Topology      |
| `/pipeline`     | Pipeline Monitor      |
| `/simulation`   | Simulation Center     |
| `/logs`         | Execution Logs        |

The **Run End-to-End Simulation** button (top bar, Overview, Simulation Center)
walks through: Network Traffic → AI Threat Detection → Quantum-Safe Security →
Self-Healing → Final Status, using demo data.

---

## 3. Folder structure

```
src/
  routes/                 One file per page (file-based routing)
    __root.tsx            App shell: fonts, sidebar/top bar, providers
  components/
    layout/               Sidebar, top bar, page header, nav config
    hud/                  Reusable UI: GlassPanel, StatCard, StatusBadge,
                          HudRing, Meter, FlowArrow, DemoBadge
    network/              Animated SVG NetworkGraph
    charts/               Shared Recharts theme + tooltip
    simulation/           Workflow stepper + Run button
    cursor/               Custom glowing cursor (desktop only)
    ui/                   shadcn/ui primitives
  features/simulation/    Simulation state (React context) + stage order
  services/
    api/config.ts         VITE_API_BASE_URL / VITE_USE_MOCK_DATA
    api/endpoints.ts      All backend paths in one place
    api/client.ts         fetch wrapper
    quantumshield.service.ts  The single integration seam (mock ↔ FastAPI)
    queries.ts            TanStack Query definitions used by pages
  data/mock/              Demo datasets (clearly labelled)
  types/quantumshield.ts  Shared TypeScript types (= your API contract)
  styles.css              Design system (colors, glass, glow, animations)
```

---

## 4. Connecting the QuantumShield backend (already built)

This folder lives inside the QuantumShield AI repo as `frontend/`; the backend is `../backend_dashboard`
and already serves every route in `src/services/api/endpoints.ts` (see `../docs/INTEGRATED_DASHBOARD.md`).

```bash
# terminal 1 (repo root)
cd backend_dashboard && uvicorn app.main:app --port 8000
# terminal 2
cd frontend && cp .env.example .env
```
In `.env` set:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_DATA=false
VITE_API_KEY=            # only if the backend sets QS_API_KEY
```

Restart `npm run dev`. In live mode a WebSocket (`src/features/live/LiveSync.tsx`) refreshes every page when the backend reports an event,
and the "Demo data" badges disappear (except on surfaces that stay simulated). Fields the pipeline cannot measure show n/a.
If you change a response shape, change `src/types/quantumshield.ts`, `../backend_dashboard/app/adapter.py` and `../backend_dashboard/tests/frontend_contract.py` together.

---

## 5. Customising the look

All colors, gradients, glow and animations live in `src/styles.css`
(oklch tokens such as `--primary` cyan and `--accent` teal). Components only
use these tokens, so changing a value there re-themes the whole app.

### Custom cursor

`src/components/cursor/QuantumCursor.tsx` adds a glowing cyan dot, a lagging
ring that turns into a teal hover ring over buttons/links, a short light trail
and a click ripple. It only loads on mouse/trackpad devices, keeps the normal
text cursor in input fields, and respects "reduce motion". Styles are at the
bottom of `src/styles.css`. To disable it, remove `<QuantumCursor />` from
`src/routes/__root.tsx`.
