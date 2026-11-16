# Stage 1: AI Threat Prediction

Input: network flows (CICFlowMeter features + Source IP, Destination IP, Timestamp). Output: `contracts/stage1_output` (label, confidence, anomaly score, node risk, reasons).

| Module | Role |
|---|---|
| `stage1/tabddpm.py` | Diffusion model that creates realistic rare-attack flows (class-conditional, classifier-free guidance) |
| `stage1/classifier.py` | Label + confidence; trained on real + synthetic flows; gradient x input attributions |
| `stage1/cpc.py` | CPC Transformer: learns normal per-host sequences, scores anything unexpected (0..1) |
| `stage1/dygnn.py` | Dynamic graph network (plain PyTorch): per-host risk over time snapshots |
| `stage1/explain.py` | Turns attributions into reasons such as "unusual packet rate" |
| `stage1/predictor.py` | `ThreatPredictor.load()`, `.ingest(flows)`, `.predict(node_id)`; fuses the three models |
| `stage1/train.py` | One command trains everything and writes `artifacts/metrics.json` |

```bash
pip install -r requirements.txt
python -m pytest -q
python -m stage1.train --data synthetic      # real data: see ../docs/DATASET_AND_TRAINING.md
python -m stage1.demo
```
Fusion: `risk = 0.45*DyGNN + 0.35*P(attack) + 0.20*CPC` (change in `artifacts/config.json`). A host the classifier calls benign but CPC finds very strange is labelled `ANOMALY_UNKNOWN` (early warning for unseen attacks).
No datasets or model weights in Git.
