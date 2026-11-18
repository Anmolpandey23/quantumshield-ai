"""Data loading: real CIC-IDS2017 CSVs or synthetic generator matching the 52 + 11 feature schemas."""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

from .config import (
    BENIGN,
    CLASS_NAMES,
    LIGHTGBM_FEATURES,
    META_COLS,
    MIN_CLASS_ROWS,
    TABDDPM_FEATURES,
)


class DatasetFormatError(ValueError):
    """The CSV folder is not in expected CIC-IDS2017 TrafficLabelling format."""


# --------------------------------------------------------------------------- labels
def normalise_label(raw: str) -> str:
    l = str(raw).strip()
    low = l.lower()
    if low in ("benign", "normal traffic", "normal"):
        return "Normal Traffic"
    if "ddos" in low:
        return "DDoS"
    if low.startswith("dos") or "heartbleed" in low:
        return "DoS"
    if "portscan" in low or "port scanning" in low:
        return "Port Scanning"
    if "patator" in low or "brute force" in low or "bruteforce" in low:
        return "Brute Force"
    if "bot" in low:
        return "Bots"
    if "web attack" in low or "webattack" in low:
        return "Web Attacks"
    if "infiltration" in low:
        return "Web Attacks"
    return l


# --------------------------------------------------------------------------- real dataset
def load_cicids(
    data_dir: str,
    max_rows: int | None = 400_000,
    max_per_attack: int = 60_000,
    seed: int = 0,
) -> pd.DataFrame:
    """Read every CSV in data_dir, clean it, optionally down-sample, sort by time."""
    files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if not files:
        raise DatasetFormatError(f"No .csv files found in '{data_dir}'.")
    need = set(LIGHTGBM_FEATURES) | set(META_COLS) | {"Label"}
    feat_set = set(LIGHTGBM_FEATURES)
    _cap = max_rows or 400_000
    per_file_cap = max(50_000, (_cap * 2) // max(len(files), 1))
    parts = []
    for f in files:
        head = pd.read_csv(f, nrows=0, encoding="latin-1")
        cols = [c for c in head.columns if c.strip() in need]
        chunk_acc: list[pd.DataFrame] = []
        rows_so_far = 0
        for chunk in pd.read_csv(
            f, usecols=cols, encoding="latin-1",
            low_memory=True, chunksize=100_000
        ):
            chunk.columns = [c.strip() for c in chunk.columns]
            chunk = chunk.loc[:, ~chunk.columns.duplicated()]
            for col in (feat_set & set(chunk.columns)):
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
            chunk_acc.append(chunk)
            rows_so_far += len(chunk)
            if rows_so_far >= per_file_cap:
                break
        part = pd.concat(chunk_acc, ignore_index=True)
        del chunk_acc
        if len(part) > per_file_cap and "Label" in part.columns:
            rng_local = np.random.default_rng(seed)
            part["Label"] = part["Label"].map(normalise_label)
            ben_mask = part["Label"] == "Normal Traffic"
            attacks = part[~ben_mask]
            benign = part[ben_mask]
            n_ben = max(per_file_cap - len(attacks), 5_000)
            if len(benign) > n_ben:
                benign = benign.iloc[
                    np.sort(rng_local.choice(len(benign), n_ben, replace=False))
                ]
            part = pd.concat([benign, attacks], ignore_index=True)
            del benign, attacks
        parts.append(part)
        print(f"  loaded {os.path.basename(f)}: {len(part):,} rows")
        del part
    df = pd.concat(parts, ignore_index=True)
    del parts

    for c in LIGHTGBM_FEATURES:
        if c not in df.columns:
            df[c] = np.nan
    df["Label"] = df["Label"].map(normalise_label)
    counts = df["Label"].value_counts()
    keep_classes = counts[counts >= MIN_CLASS_ROWS].index
    df = df[df["Label"].isin(keep_classes)].copy()
    return df.sort_values("Timestamp").reset_index(drop=True)


# --------------------------------------------------------------------------- synthetic dataset
_RS = np.random.RandomState(1234)
_MU = _RS.uniform(1.5, 8.0, len(LIGHTGBM_FEATURES))
_SD = _RS.uniform(0.5, 1.1, len(LIGHTGBM_FEATURES))
_IDX = {f: i for i, f in enumerate(LIGHTGBM_FEATURES)}

# Class shifts across features
_SHIFT = {
    "Normal Traffic": {},
    "DDoS": {"Flow Packets/s": 3.2, "Flow Bytes/s": 2.5, "Flow IAT Mean": -3.0, "Total Fwd Packets": 2.2, "Destination Port": 1.5},
    "DoS": {"Flow Duration": 3.0, "Flow IAT Mean": 2.5, "Fwd IAT Mean": 2.5, "Idle Mean": 2.5, "Flow Packets/s": -1.5},
    "Port Scanning": {"Total Fwd Packets": -2.5, "Total Length of Fwd Packets": -3.0, "Flow Duration": -2.5, "Destination Port": 3.5},
    "Brute Force": {"PSH Flag Count": 2.8, "Flow Duration": 1.5, "Total Length of Fwd Packets": 1.8},
    "Bots": {"Packet Length Std": -2.8, "Active Mean": 2.4, "Flow IAT Std": -2.6, "Fwd Packet Length Mean": 1.8},
    "Web Attacks": {"Total Length of Fwd Packets": 2.4, "Max Packet Length": 2.4, "ACK Flag Count": 1.8},
}


def _flows(label: str, n: int, rng: np.random.Generator) -> np.ndarray:
    mu = _MU.copy()
    shift_dict = _SHIFT.get(label, {})
    for f, s in shift_dict.items():
        if f in _IDX:
            mu[_IDX[f]] += s * _SD[_IDX[f]]
    z = mu + _SD * rng.normal(0.0, 0.85, size=(n, len(LIGHTGBM_FEATURES)))
    return np.expm1(np.clip(z, 0.0, None)).astype(np.float32)


def make_synthetic(
    n_hosts: int = 30,
    n_minutes: int = 180,
    flows_per_min: float = 3.0,
    n_episodes: int = 14,
    seed: int = 0,
    start: str = "2026-01-01 08:00:00",
) -> pd.DataFrame:
    """A small synthetic network traffic trace: normal traffic + attack episodes."""
    rng = np.random.default_rng(seed)
    hosts = [f"10.0.0.{10 + i}" for i in range(n_hosts)]
    servers = ["10.0.0.2", "10.0.0.3"]
    t0 = pd.Timestamp(start)
    attack_rate = {
        "DDoS": 25,
        "DoS": 10,
        "Port Scanning": 30,
        "Brute Force": 12,
        "Bots": 5,
        "Web Attacks": 8,
    }
    episodes = []
    for _ in range(n_episodes):
        lab = rng.choice(list(attack_rate))
        episodes.append((
            rng.choice(hosts),
            int(rng.integers(5, max(6, n_minutes - 15))),
            int(rng.integers(4, 12)),
            str(lab),
        ))
    rows = []
    for m in range(n_minutes):
        for h in hosts:
            lab = next((e[3] for e in episodes if e[0] == h and e[1] <= m < e[1] + e[2]), "Normal Traffic")
            n = rng.poisson(attack_rate[lab] if lab != "Normal Traffic" else flows_per_min)
            if n == 0:
                continue
            X = _flows(lab, n, rng)
            if lab in ("DDoS", "DoS", "Brute Force", "Web Attacks", "Bots"):
                dst = rng.choice(servers, n)
            else:
                dst = rng.choice(hosts + servers, n)
            ts = t0 + pd.to_timedelta(m * 60 + rng.uniform(0, 59, n), unit="s")
            part = pd.DataFrame(X, columns=LIGHTGBM_FEATURES)
            part["Source IP"], part["Destination IP"], part["Timestamp"], part["Label"] = h, dst, ts, lab

            # Add synthesized TabDDPM telemetry columns
            is_anom = (lab != "Normal Traffic")
            part["e2c_total_bytes"] = part["Total Length of Fwd Packets"].fillna(500.0) * (2.5 if is_anom else 1.0)
            part["e4_entropy_h"] = np.clip(part["Packet Length Std"] / 50.0 + (0.8 if is_anom else 0.1), 0.0, 1.0)
            part["e5_entropy_c"] = np.clip(part["e4_entropy_h"] * 0.9, 0.0, 1.0)
            part["e6_time_char"] = np.log1p(np.maximum(0.0, part["Flow IAT Mean"])) * (0.3 if is_anom else 1.0)
            part["e6b_flow_duration_ms"] = part["Flow Duration"] / 1000.0
            part["e2_client_size"] = part["Fwd Packet Length Mean"] * (3.0 if is_anom else 1.0)
            part["e2_client_record_len"] = part["Fwd Header Length"]
            part["e2_server_record_len"] = part["Bwd Header Length"]
            part["e1_alg_suite_mlkem1024"] = 0.0
            part["e1_alg_suite_mlkem768"] = 1.0
            part["e1_alg_suite_x25519"] = 0.0

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


def stratified_split(labels: np.ndarray, seed: int = 0, val: float = 0.15, test: float = 0.15):
    """Flow-level stratified split -> boolean masks (train, val, test)."""
    rng = np.random.default_rng(seed)
    r = rng.random(len(labels))
    tr = np.zeros(len(labels), bool)
    va = tr.copy()
    te = tr.copy()
    for c in np.unique(labels):
        idx = np.where(labels == c)[0]
        order = idx[np.argsort(r[idx])]
        n_te = max(1, int(len(idx) * test))
        n_va = max(1, int(len(idx) * val))
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
    te = np.isin(blk, list(te_b))
    va = np.isin(blk, list(va_b))
    return ~(te | va), va, te
