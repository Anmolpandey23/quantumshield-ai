# Runbook: from zero to a live demo in VS Code

1. **Open the folder** `quantumshield-ai` in VS Code. Terminal > New Terminal.
2. **Python 3.11 or 3.12** required. Create the environment:
   * Windows: `python -m venv venv` then `.\venv\Scripts\Activate.ps1`
   * Mac/Linux: `python3 -m venv venv && source venv/bin/activate`
   * In VS Code press Ctrl+Shift+P > "Python: Select Interpreter" > choose `venv`.
3. `pip install -r requirements-integration.txt` (PyTorch is a big download, be patient).
4. **Check everything:** `bash scripts/run_all_tests.sh` (Windows: `.\scripts\run_all_tests.ps1`). All suites must pass. Stage 1 and Stage 3 tests take about a minute each.
5. **Train:** `bash scripts/train_all.sh` (Windows: `.\scripts\train_all.ps1`). For real data see `docs/DATASET_AND_TRAINING.md`.
6. **Terminal demo of the whole loop:** `python -m integration.demo --live`
7. **Start the backend:** `cd backend_dashboard` then `uvicorn app.main:app --port 8000`.
   Open http://localhost:8000 and click "Start live simulator". Open http://localhost:8000/docs to try the API.
8. **React dashboard (recommended):** `cd frontend`, `cp .env.example .env`, set `VITE_USE_MOCK_DATA=false`, `npm install`, `npm run dev`. See `docs/INTEGRATED_DASHBOARD.md`.
9. **A separate Lovable site instead:** `docs/LOVABLE_CONNECTION.md`.

## Demo script (3 minutes)
1. "Simulate attack": feed row shows DDoS 94%, reasons, secure channel, `isolate` signed, machine turns red.
2. "Attack + eavesdropper": QBER jumps to ~25%, channel rejected, **no command sent**.
3. Critical machine (star) gets attacked: it appears under "Waiting for a human". Click Approve.
4. Start the live simulator: machines get isolated, then reconnected with new keys once clean.

## Settings (environment variables)
`QS_N_QUBITS` (lower = faster handshakes), `QS_USE_REAL_MODELS=0` (force stubs), `QS_CRITICAL_NODES`, `QS_API_KEY`, `QS_CORS_ORIGINS`.

## Troubleshooting
* "No trained Stage 1 models": run step 5. The backend still works with stub data until then (header shows `Stage 1: stub`).
* Stage 3 says `rule_fallback`: run `python -m stage3.train`.
* Port busy: use `--port 8001`.
* CUDA errors: add `--device cpu` to `stage1.train`.
