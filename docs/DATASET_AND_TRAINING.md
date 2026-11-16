# Which dataset to use (and how to train)

## Short answer
| Use | Dataset | Why |
|---|---|---|
| **Main dataset (recommended)** | **CIC-IDS2017**, the **"TrafficLabelling"** CSVs (`GeneratedLabelledFlows.zip`) | Has labelled attacks (DDoS, DoS, PortScan, brute force, bot, web attacks) AND `Source IP`, `Destination IP`, `Timestamp`. DyGNN (graph over time) and CPC (per-host sequences) need those three columns. |
| First test, no download | `--data synthetic` (built in) | Same columns, same attack families. Proves your setup works in minutes. |
| Optional second dataset | CSE-CIC-IDS2018 (same format, newer) | Good for a "tested on a second dataset" slide. |

**Do NOT use the "MachineLearningCSV" version of CIC-IDS2017.** It has no IP addresses or timestamps, so Stage 1's graph and sequence models cannot work (the loader tells you this).

Download page: search "CIC-IDS2017 University of New Brunswick" (https://www.unb.ca/cic/datasets/ids-2017.html). Many Kaggle mirrors exist too. Unzip so you have a folder of 8 CSV files (Monday ... Friday). Keep it OUTSIDE the repo (datasets never go to Git).

## Train
```bash
cd stage1_ai_threat_prediction
python -m stage1.train --data synthetic                                   # 3-4 min, CPU
python -m stage1.train --data cicids --data-dir "D:/datasets/CIC-IDS2017" # real data
```
Useful flags: `--max-rows 400000` (default, keeps RAM and time sane), `--epochs-ddpm 40`, `--epochs-clf 20`, `--epochs-cpc 15`, `--epochs-gnn 8`, `--device cuda` (auto if a GPU exists), `--quick` (smoke test).
On real data expect 20-60 minutes on CPU; much less on a GPU.

Output goes to `stage1_ai_threat_prediction/artifacts/` (git-ignored): `metrics.json` is your results table:
* classifier macro-F1 **with vs without TabDDPM data** (the proof TabDDPM helps rare attacks),
* CPC attack-vs-benign AUROC and mean scores,
* DyGNN AUROC / average precision on held-out time blocks.

Then Stage 3: `cd stage3_self_healing && python -m stage3.train && python -m stage3.evaluate` (about 1-2 min). `evaluate` prints PPO vs "never act" vs random vs a hand-written rule.

## Honest notes (put these in your report)
* TabDDPM here is the Gaussian-diffusion part on numeric flow features (all CIC features are numeric), conditioned on the class label with classifier-free guidance.
* Classifier and TabDDPM use a stratified flow split; CPC and DyGNN use a time-block split so sequences are not cut in half. Each model is scored on its own held-out set.
* Synthetic data was used to verify all code. The real CIC-IDS2017 loader follows the published column names but was not run on the real files while this was written. If your first run fails with a column or timestamp error, send the message and the first 3 lines of one CSV.
* Stage 3 is trained on a simulator of an infection spreading through a network, not on real incidents. That is normal for self-healing research, and it is why guardrails and human approval exist.
* Stage 2 uses pure-Python ML-KEM/ML-DSA libraries (learning use, not constant-time). Production would use liboqs or OpenSSL 3.5+.
* Smaller PyTorch install (CPU only): `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
