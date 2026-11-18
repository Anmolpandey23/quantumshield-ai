# Stage 1: AI Threat Prediction

Input: network flows (CIC-IDS2017 features + Source IP, Destination IP, Timestamp).
Output: adheres to `contracts/inference_schema.json` and `contracts/stage1_output.schema.json`.

| Module | Role |
|---|---|
| `stage1/tabddpm.py` | Denoising Diffusion Probabilistic Model (PyTorch) for benign-distribution anomaly detection across 11 telemetry features (threshold `0.56279456615448`) |
| `stage1/classifier.py` | QuantumShield CICIDS LightGBM multiclass flow classifier across 52 features (7 attack classes: Normal Traffic, DoS, DDoS, Port Scanning, Brute Force, Web Attacks, Bots) |
| `stage1/explain.py` | Explainable AI via `shap.TreeExplainer` feature contributions and human-readable operational phrases |
| `stage1/predictor.py` | `ThreatPredictor.load()`, `.ingest(flows)`, `.predict(node_id)`, `.predict_all()`; fuses TabDDPM + LightGBM inference contracts |
| `stage1/train.py` | End-to-end training pipeline for TabDDPM and LightGBM models, saving artifacts to `models/` and manifests |

```bash
pip install -r requirements.txt
python -m pytest -q
python -m stage1.train --data synthetic
python -m stage1.demo
```

### Response Contract & Model Registry
- **Registry**: `models/quantumshield_model_registry.json`
- **TabDDPM Manifest**: `models/tabddpm/improved/tabddpm_manifest.json`
- **LightGBM Manifest**: `models/cicids_classifier/lightgbm_manifest.json`
- **Inference Schema**: `contracts/inference_schema.json`

### Key Policy Principles
- TabDDPM anomaly score is not a probability.
- LightGBM class probability is not an operational risk score.
- SHAP values explain model output and are not causal effects.
- Unknown anomalies (`ANOMALY_UNKNOWN`) are flagged when flows deviate from the benign distribution even if unclassified by known attack signatures.
