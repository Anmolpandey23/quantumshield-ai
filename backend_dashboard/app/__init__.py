"""Stage 4: FastAPI backend + live dashboard."""
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]          # repo root, so `import integration` works from anywhere
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
import integration  # noqa: E402,F401  (adds every stage folder to sys.path)
