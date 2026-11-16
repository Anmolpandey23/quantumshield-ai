# Stage 4: Backend and Dashboard

FastAPI app wrapping the orchestrator. SQLite event log, WebSocket live feed, optional API key, CORS for your Lovable site, built-in dashboard at `/`.

```bash
pip install -r requirements.txt          # or the repo-wide requirements-integration.txt
python -m pytest -q
uvicorn app.main:app --port 8000         # http://localhost:8000  and  /docs
```
Files: `app/main.py` (routes), `app/engine.py` (pipeline + broadcast + simulator control), `app/store.py` (SQLite), `app/simulator.py` (traffic generators), `static/index.html` (dashboard).
API reference and Lovable steps: `../docs/LOVABLE_CONNECTION.md`.
