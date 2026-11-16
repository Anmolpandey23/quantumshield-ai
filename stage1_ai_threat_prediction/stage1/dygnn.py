"""DyGNN: the network as a graph that changes over time; scores how risky each computer is.

Every `snapshot_seconds` we build a graph: nodes = hosts, edges = "A talked to B" (weighted by flow count).
Each node gets features = average of its outgoing flows' features + degree statistics.
A 2-layer graph network mixes information from neighbours; a GRU keeps a memory per host across snapshots,
so a host that slowly turns bad (or sits next to bad hosts) is noticed. Output: risk in [0, 1] per host.
Written in plain PyTorch (no torch-geometric needed).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import average_precision_score, roc_auc_score

N_STRUCT = 4        # log out-flows, log in-flows, log unique dsts, log unique srcs


@dataclass
class Snapshot:
    nodes: torch.Tensor         # (n,) global host ids active in this snapshot
    x: torch.Tensor             # (n, F + N_STRUCT)
    edge_src: torch.Tensor      # local indices
    edge_dst: torch.Tensor
    edge_w: torch.Tensor
    y: torch.Tensor             # (n,) 1 if host sent an attack flow in this snapshot


class DyGNN(nn.Module):
    def __init__(self, in_dim: int, hidden: int = 64):
        super().__init__()
        self.cfg = {"in_dim": in_dim, "hidden": hidden}
        self.hidden = hidden
        self.inp = nn.Linear(in_dim, hidden)
        self.msg1, self.msg2 = nn.Linear(hidden * 2, hidden), nn.Linear(hidden * 2, hidden)
        self.gru = nn.GRUCell(hidden, hidden)
        self.head = nn.Sequential(nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, 1))

    @staticmethod
    def _aggregate(h: torch.Tensor, s: torch.Tensor, d: torch.Tensor, w: torch.Tensor) -> torch.Tensor:
        """Weighted mean of neighbour states, edges used in both directions."""
        n = h.shape[0]
        src = torch.cat([s, d]); dst = torch.cat([d, s]); ww = torch.cat([w, w])
        agg = torch.zeros_like(h).index_add_(0, dst, h[src] * ww[:, None])
        deg = torch.zeros(n, device=h.device).index_add_(0, dst, ww).clamp(min=1e-6)
        return agg / deg[:, None]

    def step(self, mem: torch.Tensor, snap: Snapshot) -> tuple[torch.Tensor, torch.Tensor]:
        """One snapshot. mem: (N_total, hidden). Returns (new_mem, logits for the active nodes)."""
        h = F.relu(self.inp(snap.x))
        for lin in (self.msg1, self.msg2):
            h = F.relu(lin(torch.cat([h, self._aggregate(h, snap.edge_src, snap.edge_dst, snap.edge_w)], -1)))
        h_new = self.gru(h, mem[snap.nodes])
        mem = mem.index_copy(0, snap.nodes, h_new)
        return mem, self.head(h_new).squeeze(-1)

    def init_memory(self, n_nodes: int, device) -> torch.Tensor:
        return torch.zeros(n_nodes, self.hidden, device=device)


# --------------------------------------------------------------------------- graph building
def build_host_index(df: pd.DataFrame, max_nodes: int = 6000) -> dict[str, int]:
    counts = pd.concat([df["Source IP"], df["Destination IP"]]).value_counts()
    return {ip: i for i, ip in enumerate(counts.index[:max_nodes])}


def build_snapshots(df: pd.DataFrame, x_scaled: np.ndarray, host_index: dict[str, int],
                    snapshot_seconds: int = 60, with_labels: bool = True, benign_label: str = "BENIGN") -> list[Snapshot]:
    """df rows and x_scaled rows must align. Returns time-ordered snapshots."""
    src = df["Source IP"].map(host_index).to_numpy()
    dst = df["Destination IP"].map(host_index).to_numpy()
    ok = ~(pd.isna(src) | pd.isna(dst))
    t0 = df["Timestamp"].min()
    bucket = ((df["Timestamp"] - t0).dt.total_seconds() // snapshot_seconds).astype(int).to_numpy()
    attack = (df["Label"].to_numpy() != benign_label) if with_labels and "Label" in df else np.zeros(len(df), bool)
    snaps: list[Snapshot] = []
    for b in np.unique(bucket[ok]):
        m = ok & (bucket == b)
        s, d, xs, at = src[m].astype(np.int64), dst[m].astype(np.int64), x_scaled[m], attack[m]
        nodes = np.unique(np.concatenate([s, d]))
        loc = {g: i for i, g in enumerate(nodes)}
        ls = np.fromiter((loc[g] for g in s), np.int64, len(s)); ld = np.fromiter((loc[g] for g in d), np.int64, len(d))
        n = len(nodes)
        feat = np.zeros((n, xs.shape[1]), np.float32); cnt = np.bincount(ls, minlength=n).astype(np.float32)
        np.add.at(feat, ls, xs)
        feat = feat / np.maximum(cnt, 1)[:, None]
        indeg = np.bincount(ld, minlength=n).astype(np.float32)
        uniq_dst = np.array([len(set(ld[ls == i])) for i in range(n)], np.float32)
        uniq_src = np.array([len(set(ls[ld == i])) for i in range(n)], np.float32)
        struct = np.log1p(np.stack([cnt, indeg, uniq_dst, uniq_src], 1))
        # unique edges with weights
        key = ls * n + ld
        uk, w = np.unique(key, return_counts=True)
        y = np.zeros(n, np.float32)
        np.maximum.at(y, ls, at.astype(np.float32))
        snaps.append(Snapshot(torch.as_tensor(nodes), torch.as_tensor(np.concatenate([feat, struct], 1)),
                              torch.as_tensor(uk // n), torch.as_tensor(uk % n),
                              torch.as_tensor(np.log1p(w).astype(np.float32)), torch.as_tensor(y)))
    return snaps


def _to(s: Snapshot, dev) -> Snapshot:
    return Snapshot(*(t.to(dev) for t in (s.nodes, s.x, s.edge_src, s.edge_dst, s.edge_w, s.y)))


# --------------------------------------------------------------------------- training / evaluation
def train_dygnn(snaps: list[Snapshot], n_nodes: int, epochs: int = 8, chunk: int = 8, lr: float = 2e-3,
                device: str = "cpu", verbose: bool = True, seed: int = 0) -> DyGNN:
    torch.manual_seed(seed)
    dev = torch.device(device)
    model = DyGNN(snaps[0].x.shape[1]).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    pos = sum(float(s.y.sum()) for s in snaps); tot = sum(len(s.y) for s in snaps)
    pw = torch.tensor(min(10.0, max(1.0, (tot - pos) / max(pos, 1.0)) ** 0.5), device=dev)
    snaps = [_to(s, dev) for s in snaps]
    for ep in range(epochs):
        model.train()
        mem = model.init_memory(n_nodes, dev)
        tot_loss, nb = 0.0, 0
        for i in range(0, len(snaps), chunk):                 # truncated back-propagation through time
            mem = mem.detach()
            loss = 0.0
            for s in snaps[i:i + chunk]:
                mem, logits = model.step(mem, s)
                loss = loss + F.binary_cross_entropy_with_logits(logits, s.y, pos_weight=pw)
            loss = loss / len(snaps[i:i + chunk])
            opt.zero_grad(); loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot_loss += loss.item(); nb += 1
        if verbose and (ep % 2 == 0 or ep == epochs - 1):
            print(f"    DyGNN epoch {ep + 1:3d}/{epochs}  loss {tot_loss / max(nb, 1):.4f}")
    return model


@torch.no_grad()
def evaluate_dygnn(model: DyGNN, snaps: list[Snapshot], n_nodes: int, warmup: list[Snapshot] | None = None) -> dict:
    dev = next(model.parameters()).device
    model.eval()
    mem = model.init_memory(n_nodes, dev)
    for s in (warmup or []):
        mem, _ = model.step(mem, _to(s, dev))
    ys, ps = [], []
    for s in snaps:
        s = _to(s, dev)
        mem, logits = model.step(mem, s)
        ys.append(s.y.cpu().numpy()); ps.append(torch.sigmoid(logits).cpu().numpy())
    y, p = np.concatenate(ys), np.concatenate(ps)
    if len(np.unique(y)) < 2:
        return {"auroc": None, "avg_precision": None, "n": int(len(y))}
    return {"auroc": float(roc_auc_score(y, p)), "avg_precision": float(average_precision_score(y, p)), "n": int(len(y))}


@torch.no_grad()
def node_risk(model: DyGNN, snaps: list[Snapshot], n_nodes: int) -> dict[int, float]:
    """Run the last few snapshots from a fresh memory; return the latest risk of every host seen."""
    dev = next(model.parameters()).device
    model.eval()
    mem = model.init_memory(n_nodes, dev)
    risk: dict[int, float] = {}
    for s in snaps:
        s = _to(s, dev)
        mem, logits = model.step(mem, s)
        for g, p in zip(s.nodes.tolist(), torch.sigmoid(logits).tolist()):
            risk[g] = p
    return risk
