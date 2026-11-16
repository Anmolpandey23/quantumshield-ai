"""All settings come from environment variables (see .env.example). Nothing secret lives in code."""
import os
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("QS_DB_PATH", str(BASE / "data" / "quantumshield.db"))
N_QUBITS = int(os.getenv("QS_N_QUBITS", "1024"))                 # BB84 qubits per handshake (lower = faster demo)
USE_REAL_MODELS = os.getenv("QS_USE_REAL_MODELS", "1") == "1"     # 0 forces stubs even if models exist
API_KEY = os.getenv("QS_API_KEY", "")                            # empty = no auth (local dev only!)
CORS_ORIGINS = [o.strip() for o in os.getenv("QS_CORS_ORIGINS", "*").split(",") if o.strip()]
CRITICAL_NODES = {c for c in os.getenv("QS_CRITICAL_NODES", "10.0.0.2,10.0.0.3").split(",") if c}
SIM_NODES = int(os.getenv("QS_SIM_NODES", "12"))
