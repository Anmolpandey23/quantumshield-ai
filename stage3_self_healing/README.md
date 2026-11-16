# Stage 3: Self-Healing Network

Input: `stage1_output` + `stage2_output`. Output: an action (isolate / monitor / reconnect), signed by Stage 2's `CommandSigner`.

| Module | Role |
|---|---|
| `stage3/env.py` | Simulator: infection spreads through a graph; the agent sees only noisy Stage 1-like signals |
| `stage3/ppo.py` | PPO from scratch (shared actor-critic over computers, action masking, GAE) |
| `stage3/guardrails.py` | Allowlist, evidence needed, max share isolated, critical nodes need a human, rate limit, kill switch |
| `stage3/policy.py` | Live policy for the orchestrator (`observe`, `decide`, `on_applied`); rule fallback if no weights |
| `stage3/node_agent.py` | Runs on each machine: verifies the ML-DSA signature (replay/forgery/wrong node rejected) before obeying |
| `stage3/baselines.py`, `evaluate.py` | never-act / random / rule policies to compare against |

```bash
pip install -r requirements.txt
python -m pytest -q
python -m stage3.train        # ~1-2 min
python -m stage3.evaluate     # PPO vs baselines table for your report
```
The agent only PROPOSES. Guardrails decide if it may run, and the most drastic actions wait for `Orchestrator.approve()` / the dashboard button.
