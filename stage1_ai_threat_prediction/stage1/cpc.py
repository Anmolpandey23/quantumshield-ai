"""CPC Transformer: learns what NORMAL traffic of a host looks like and predicts the next steps.

Contrastive Predictive Coding: an encoder turns each flow into a latent z_t, a causal Transformer
summarises the past into a context c_t, and linear heads W_k predict the latent k steps ahead.
Training (InfoNCE) uses benign sequences only. At run time a sequence that is badly predicted,
or whose latents are far from normal, gets a high anomaly score, which is what makes strange
behaviour stand out EARLY.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class CPCTransformer(nn.Module):
    def __init__(self, n_features: int, d_model: int = 64, n_heads: int = 4, n_layers: int = 2,
                 seq_len: int = 16, horizon: int = 3, dropout: float = 0.1):
        super().__init__()
        self.cfg = dict(n_features=n_features, d_model=d_model, n_heads=n_heads, n_layers=n_layers,
                        seq_len=seq_len, horizon=horizon, dropout=dropout)
        self.seq_len, self.horizon = seq_len, horizon
        self.encoder = nn.Sequential(nn.Linear(n_features, d_model * 2), nn.GELU(), nn.Linear(d_model * 2, d_model))
        self.pos = nn.Parameter(torch.zeros(1, seq_len, d_model))
        layer = nn.TransformerEncoderLayer(d_model, n_heads, d_model * 4, dropout, batch_first=True, norm_first=True)
        self.context = nn.TransformerEncoder(layer, n_layers, enable_nested_tensor=False)
        self.heads = nn.ModuleList([nn.Linear(d_model, d_model) for _ in range(horizon)])
        self.register_buffer("z_mean", torch.zeros(d_model))      # filled by calibrate()
        self.register_buffer("z_std", torch.ones(d_model))
        self.calib = {"center": 0.0, "scale": 1.0}

    def _ctx(self, x: torch.Tensor):
        z = self.encoder(x)
        L = x.shape[1]
        mask = torch.triu(torch.ones(L, L, dtype=torch.bool, device=x.device), 1)     # causal: no peeking ahead
        c = self.context(z + self.pos[:, :L], mask=mask)
        return z, c

    def info_nce(self, x: torch.Tensor) -> torch.Tensor:
        z, c = self._ctx(x)
        B, L, _ = z.shape
        total, n = x.new_zeros(()), 0
        zn = F.normalize(z, dim=-1)
        for k, head in enumerate(self.heads, start=1):
            if L <= k:
                break
            pred = F.normalize(head(c[:, :-k]), dim=-1)           # (B, L-k, d)  predictions of z_{t+k}
            tgt = zn[:, k:]                                       # (B, L-k, d)
            # negatives = the same future position of the OTHER sequences in the batch
            logits = torch.einsum("btd,ctd->tbc", pred, tgt) / 0.1
            labels = torch.arange(B, device=x.device).repeat(L - k)
            total = total + F.cross_entropy(logits.reshape(-1, B), labels)
            n += 1
        return total / max(n, 1)

    @torch.no_grad()
    def raw_error(self, x: torch.Tensor) -> torch.Tensor:
        """Per-sequence error: how badly the next flow was predicted + how far latents are from normal."""
        self.eval()
        z, c = self._ctx(x)
        half = x.shape[1] // 2
        pred = self.heads[0](c[:, :-1])
        cos = 1 - F.cosine_similarity(pred, z[:, 1:], dim=-1)               # (B, L-1)
        novelty = (((z - self.z_mean) / self.z_std).pow(2).mean(-1)).sqrt()   # (B, L)
        return cos[:, half:].mean(1) + 0.25 * novelty[:, half:].mean(1)

    def score(self, x: np.ndarray) -> np.ndarray:
        """Anomaly score in [0, 1]. About 0.1 for typical benign, 0.5 at the benign 95th percentile, ~1 far beyond."""
        dev = next(self.parameters()).device
        err = self.raw_error(torch.as_tensor(x, dtype=torch.float32, device=dev)).cpu().numpy()
        s = 1 / (1 + np.exp(-3.0 * (err - self.calib["center"]) / max(self.calib["scale"], 1e-6)))
        return s.astype(np.float32)


def make_sequences(x: np.ndarray, groups: np.ndarray, seq_len: int, stride: int, min_len: int | None = None):
    """Cut per-host flow sequences (rows must be time-ordered). Returns (N, seq_len, F) and the group id of each."""
    out, owners = [], []
    order = np.argsort(groups, kind="stable")
    g_sorted = groups[order]
    bounds = np.flatnonzero(np.r_[True, g_sorted[1:] != g_sorted[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        idx = order[a:b]                                   # keeps original (time) order inside the host
        if len(idx) < (min_len or seq_len):
            continue
        for s in range(0, len(idx) - seq_len + 1, stride):
            out.append(x[idx[s:s + seq_len]])
            owners.append(g_sorted[a])
    if not out:
        return np.zeros((0, seq_len, x.shape[1]), np.float32), np.array([])
    return np.stack(out).astype(np.float32), np.array(owners)


def train_cpc(seqs: np.ndarray, epochs: int = 15, batch_size: int = 128, lr: float = 1e-3, device: str = "cpu",
              seq_len: int = 16, horizon: int = 3, verbose: bool = True, seed: int = 0) -> CPCTransformer:
    torch.manual_seed(seed)
    dev = torch.device(device)
    model = CPCTransformer(seqs.shape[2], seq_len=seq_len, horizon=horizon).to(dev)
    X = torch.as_tensor(seqs, dtype=torch.float32, device=dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    bs = min(batch_size, max(8, len(X)))
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(len(X), device=dev)
        tot, nb = 0.0, 0
        for i in range(0, len(X) - bs + 1, bs):
            loss = model.info_nce(X[perm[i:i + bs]])
            opt.zero_grad(); loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot += loss.item(); nb += 1
        if verbose and (ep % 5 == 0 or ep == epochs - 1):
            print(f"    CPC epoch {ep + 1:3d}/{epochs}  InfoNCE {tot / max(nb, 1):.4f}")
    return model


@torch.no_grad()
def calibrate_cpc(model: CPCTransformer, train_seqs: np.ndarray, benign_val_seqs: np.ndarray) -> None:
    """Learn what 'normal' error looks like so scores are comparable across datasets."""
    dev = next(model.parameters()).device
    model.eval()
    z = model.encoder(torch.as_tensor(train_seqs[: min(len(train_seqs), 4000)], dtype=torch.float32, device=dev))
    model.z_mean.copy_(z.mean((0, 1))); model.z_std.copy_(z.std((0, 1)).clamp(min=1e-3))
    errs = np.concatenate([model.raw_error(torch.as_tensor(benign_val_seqs[i:i + 1024], dtype=torch.float32, device=dev)).cpu().numpy()
                           for i in range(0, len(benign_val_seqs), 1024)])
    q50, q95, q99 = np.quantile(errs, [0.5, 0.95, 0.99])
    model.calib = {"center": float(q95), "scale": float(max(q99 - q50, 1e-4))}
