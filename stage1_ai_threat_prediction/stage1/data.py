"""Data loading: the real CIC-IDS2017 CSVs, or a synthetic stand-in with the SAME columns.

Real data  -> `load_cicids(folder)`  (use the *TrafficLabelling* CSVs, they contain Source/Destination IP + Timestamp)
Synthetic  -> `make_synthetic(...)`  (runs anywhere, used by tests and by the dashboard demo)
"""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

from .config import BENIGN, FEATURES, META_COLS, MIN_CLASS_ROWS


class DatasetFormatError(ValueError):
    """The CSV folder is not in the expected CIC-IDS2017 *TrafficLabelling* format."""


# --------------------------------------------------------------------------- labels
def normalise_label(raw: str) -> str:
    l = str(raw).strip()
    low = l.lower()
    if low == "benign":
        return BENIGN
    if "ddos" in low:
        return "DDoS"
    if low.startswith("dos") or "heartbleed" in low:
        return "DoS"
    if "portscan" in low:
        return "PortScan"
    if "patator" in low:
        return "BruteForce"
    if low == "bot":
        return "Bot"
    if "web attack" in low:
        return "WebAttack"
    if "infiltration" in low:
        return "Infiltration"
    return l


# --------------------------------------------------------------------------- real dataset
def load_cicids(data_dir: str, max_rows: int | None = 400_000, max_per_attack: int = 60_000,
                seed: int = 0) -> pd.DataFrame:
    """Read every CSV in `data_dir`, clean it, optionally down-sample (benign first), sort by time."""
    files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if not files:
        raise DatasetFormatError(f"No .csv files found in '{data_dir}'. See docs/DATASET_AND_TRAINING.md")
    need = set(FEATURES) | set(META_COLS) | {"Label"}
    feat_set = set(FEATURES)
    # Cap rows per file so the parts list never exceeds ~2× max_rows total in RAM.
    # 8 files → each gets at most ⌈max_rows * 2 / 8⌉ rows, minimum 50 000.
    _cap = max_rows or 400_000
    per_file_cap = max(50_000, (_cap * 2) // max(len(files), 1))
    parts = []
    for f in files:
        head = pd.read_csv(f, nrows=0, encoding="latin-1")
        cols = [c for c in head.columns if c.strip() in need]
        # Read in 100 000-row chunks so the C parser never allocates the whole file at once.
        chunk_acc: list[pd.DataFrame] = []
        rows_so_far = 0
        for chunk in pd.read_csv(
            f, usecols=cols, encoding="latin-1",
            low_memory=True, chunksize=100_000
        ):
            chunk.columns = [c.strip() for c in chunk.columns]
            chunk = chunk.loc[:, ~chunk.columns.duplicated()]
            # Numeric conversion per-chunk (avoids large intermediate copies)
            for col in (feat_set & set(chunk.columns)):
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
            chunk_acc.append(chunk)
            rows_so_far += len(chunk)
            if rows_so_far >= per_file_cap:
                break          # enough rows from this file
        part = pd.concat(chunk_acc, ignore_index=True)
        del chunk_acc          # free chunk list immediately
        # Stratified sample per file: keep benign + all attacks up to cap
        if len(part) > per_file_cap and "Label" in part.columns:
            rng_local = np.random.default_rng(seed)
            part["Label"] = part["Label"].map(normalise_label)
            ben_mask = part["Label"] == BENIGN
            attacks = part[~ben_mask]
            benign  = part[ben_mask]
            n_ben   = max(per_file_cap - len(attacks), 5_000)
            if len(benign) > n_ben:
                benign = benign.iloc[
                    np.sort(rng_local.choice(len(benign), n_ben, replace=False))
                ]
            part = pd.concat([benign, attacks], ignore_index=True)
            del benign, attacks
        parts.append(part)
        print(f"  loaded {os.path.basename(f)}: {len(part):,} rows")
        del part               # name goes away; DataFrame lives only inside `parts`
    df = pd.concat(parts, ignore_index=True)
    del parts                  # free all per-file DataFrames immediately
    missing = [c for c in list(FEATURES) + META_COLS + ["Label"] if c not in df.columns]
    if missing:
        raise DatasetFormatError(
            f"Missing columns {missing}. Use the 'TrafficLabelling' CSVs of CIC-IDS2017 (they include "
            "Source IP, Destination IP and Timestamp). The 'MachineLearningCVE' CSVs do not.")
    df["Label"] = df["Label"].map(normalise_label)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], dayfirst=True, errors="coerce", format="mixed")
    # Replace inf/nan column-by-column (never creates a full-width copy)
    for col in FEATURES:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=FEATURES + ["Timestamp", "Source IP", "Destination IP"]).drop_duplicates()
    counts = df["Label"].value_counts()
    keep = counts[counts >= MIN_CLASS_ROWS].index
    if len(keep) < len(counts):
        print(f"  dropped tiny classes: {sorted(set(counts.index) - set(keep))}")
    df = df[df["Label"].isin(keep)]
    if max_rows:
        rng = np.random.default_rng(seed)
        att_parts = []
        for lab, g in df[df["Label"] != BENIGN].groupby("Label"):
            att_parts.append(g.sample(max_per_attack, random_state=seed) if len(g) > max_per_attack else g)
        att = pd.concat(att_parts) if att_parts else df.iloc[:0]
        ben = df[df["Label"] == BENIGN]
        n_ben = max(max_rows - len(att), 10_000)
        if len(ben) > n_ben:
            ben = ben.iloc[np.sort(rng.choice(len(ben), n_ben, replace=False))]
        df = pd.concat([ben, att])
    return df.sort_values("Timestamp").reset_index(drop=True)


# --------------------------------------------------------------------------- synthetic dataset
_RS = np.random.RandomState(1234)
_MU = _RS.uniform(1.5, 8.0, len(FEATURES))          # fixed "normal" behaviour, in log1p space
_SD = _RS.uniform(0.5, 1.1, len(FEATURES))
_IDX = {f: i for i, f in enumerate(FEATURES)}

# class -> {feature: shift in standard deviations}. Distinct but overlapping, so the task is not trivial.
_SHIFT = {
    BENIGN: {},
    "DDoS": {"Flow Packets/s": 3.2, "Flow Bytes/s": 2.5, "SYN Flag Count": 3.0, "Flow IAT Mean": -3.0, "Total Fwd Packets": 2.2},
    "DoS": {"Flow Duration": 3.0, "Flow IAT Mean": 2.5, "Fwd IAT Mean": 2.5, "Idle Mean": 2.5, "Flow Packets/s": -1.5},
    "PortScan": {"Total Fwd Packets": -2.5, "Total Length of Fwd Packets": -3.0, "Flow Duration": -2.5,
                 "RST Flag Count": 3.0, "Destination Port": 2.5},
    "BruteForce": {"Total Backward Packets": 2.0, "PSH Flag Count": 2.8, "Fwd PSH Flags": 2.5, "Flow Duration": 1.5},
    "Bot": {"Packet Length Std": -2.8, "Active Mean": 2.4, "Flow IAT Std": -2.6, "Fwd Packet Length Mean": 1.8},
    "WebAttack": {"Total Length of Fwd Packets": 2.4, "Max Packet Length": 2.4, "ACK Flag Count": 1.8, "Down/Up Ratio": -1.8},
}


def _flows(label: str, n: int, rng: np.random.Generator) -> np.ndarray:
    mu = _MU.copy()
    for f, s in _SHIFT[label].items():
        mu[_IDX[f]] += s * _SD[_IDX[f]]
    z = mu + _SD * rng.normal(0.0, 0.85, size=(n, len(FEATURES)))
    return np.expm1(np.clip(z, 0.0, None)).astype(np.float32)


def make_synthetic(n_hosts: int = 30, n_minutes: int = 180, flows_per_min: float = 3.0, n_episodes: int = 14,
                   seed: int = 0, start: str = "2026-01-01 08:00:00") -> pd.DataFrame:
    """A small fake network: benign chatter plus attack episodes launched by some hosts."""
    rng = np.random.default_rng(seed)
    hosts = [f"10.0.0.{10 + i}" for i in range(n_hosts)]
    servers = ["10.0.0.2", "10.0.0.3"]
    t0 = pd.Timestamp(start)
    attack_rate = {"DDoS": 25, "DoS": 10, "PortScan": 30, "BruteForce": 12, "Bot": 5, "WebAttack": 8}
    episodes = []
    for _ in range(n_episodes):
        lab = rng.choice(list(attack_rate))
        episodes.append((rng.choice(hosts), int(rng.integers(5, max(6, n_minutes - 15))), int(rng.integers(4, 12)), str(lab)))
    rows = []
    for m in range(n_minutes):
        for h in hosts:
            lab = next((e[3] for e in episodes if e[0] == h and e[1] <= m < e[1] + e[2]), BENIGN)
            n = rng.poisson(attack_rate[lab] if lab != BENIGN else flows_per_min)
            if n == 0:
                continue
            X = _flows(lab, n, rng)
            if lab in ("DDoS", "DoS", "BruteForce", "WebAttack", "Bot"):
                dst = rng.choice(servers, n)
            else:                                    # benign chatter and port scans touch many machines
                dst = rng.choice(hosts + servers, n)
            ts = t0 + pd.to_timedelta(m * 60 + rng.uniform(0, 59, n), unit="s")
            part = pd.DataFrame(X, columns=FEATURES)
            part["Source IP"], part["Destination IP"], part["Timestamp"], part["Label"] = h, dst, ts, lab
            rows.append(part)
    df = pd.concat(rows, ignore_index=True)
    return df.sort_values("Timestamp").reset_index(drop=True)


def load(source: str, data_dir: str | None = None, **kw) -> pd.DataFrame:
    if source == "synthetic":
        return make_synthetic(seed=kw.get("seed", 0), n_minutes=kw.get("n_minutes", 180))
    if source == "cicids":
        if not data_dir:
            raise DatasetFormatError("--data-dir is required for --data cicids")
        return load_cicids(data_dir, max_rows=kw.get("max_rows", 400_000), seed=kw.get("seed", 0))
    raise ValueError(f"unknown data source '{source}'")


# --------------------------------------------------------------------------- splits
def stratified_split(labels: np.ndarray, seed: int = 0, val: float = 0.15, test: float = 0.15):
    """Flow-level stratified split -> boolean masks (train, val, test)."""
    rng = np.random.default_rng(seed)
    r = rng.random(len(labels))
    tr = np.zeros(len(labels), bool); va = tr.copy(); te = tr.copy()
    for c in np.unique(labels):
        idx = np.where(labels == c)[0]
        order = idx[np.argsort(r[idx])]
        n_te, n_va = max(1, int(len(idx) * test)), max(1, int(len(idx) * val))
        te[order[:n_te]] = True
        va[order[n_te:n_te + n_va]] = True
        tr[order[n_te + n_va:]] = True
    return tr, va, te


def block_split(timestamps: pd.Series, block_minutes: int = 10, seed: int = 0, val: float = 0.15, test: float = 0.15):
    """Time-block split (sequences stay intact). Returns masks (train, val, test)."""
    blk = ((timestamps - timestamps.min()).dt.total_seconds() // (block_minutes * 60)).astype(int).to_numpy()
    ub = np.unique(blk)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(ub)
    n_te, n_va = max(1, int(len(ub) * test)), max(1, int(len(ub) * val))
    te_b, va_b = set(perm[:n_te].tolist()), set(perm[n_te:n_te + n_va].tolist())
    te = np.isin(blk, list(te_b)); va = np.isin(blk, list(va_b))
    return ~(te | va), va, te
