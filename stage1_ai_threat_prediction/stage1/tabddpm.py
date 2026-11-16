"""TabDDPM (Gaussian-diffusion part) for numeric network-flow features, conditioned on the attack class.

Why: real attacks are rare. We train a diffusion model on the (scaled) flow features and then sample
extra, realistic flows for the rare classes to balance the classifier's training set.
Training is class-balanced (rare classes are shown more often) and uses classifier-free label dropout.
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def _time_embedding(t: torch.Tensor, dim: int) -> torch.Tensor:
    half = dim // 2
    freqs = torch.exp(-math.log(10000) * torch.arange(half, device=t.device) / half)
    ang = t.float()[:, None] * freqs[None]
    return torch.cat([ang.sin(), ang.cos()], dim=-1)


class Denoiser(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden: int = 256, n_blocks: int = 3, t_dim: int = 64):
        super().__init__()
        self.t_dim, self.null_class = t_dim, n_classes          # index n_classes = "no label"
        self.cls = nn.Embedding(n_classes + 1, hidden)
        self.t_mlp = nn.Sequential(nn.Linear(t_dim, hidden), nn.SiLU(), nn.Linear(hidden, hidden))
        self.inp = nn.Linear(n_features, hidden)
        self.blocks = nn.ModuleList([nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, hidden * 2), nn.SiLU(),
                                                   nn.Linear(hidden * 2, hidden)) for _ in range(n_blocks)])
        self.out = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, n_features))

    def forward(self, x: torch.Tensor, t: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        h = self.inp(x) + self.t_mlp(_time_embedding(t, self.t_dim)) + self.cls(y)
        for b in self.blocks:
            h = h + b(h)
        return self.out(h)


class TabDDPM:
    def __init__(self, n_features: int, n_classes: int, timesteps: int = 200, hidden: int = 256,
                 device: str = "cpu"):
        self.n_features, self.n_classes, self.T, self.device = n_features, n_classes, timesteps, torch.device(device)
        self.model = Denoiser(n_features, n_classes, hidden).to(self.device)
        betas = torch.linspace(1e-4, 0.02 * 1000 / timesteps, timesteps)   # same total noise as 1000-step linear
        betas = betas.clamp(max=0.999)
        alphas = 1 - betas
        abar = torch.cumprod(alphas, 0)
        self.betas, self.alphas, self.abar = betas.to(self.device), alphas.to(self.device), abar.to(self.device)

    # ------------------------------------------------------------------ training
    def fit(self, x: np.ndarray, y: np.ndarray, epochs: int = 30, batch_size: int = 512, lr: float = 2e-3,
            label_dropout: float = 0.1, verbose: bool = True) -> list[float]:
        X = torch.as_tensor(x, dtype=torch.float32, device=self.device)
        Y = torch.as_tensor(y, dtype=torch.long, device=self.device)
        counts = torch.bincount(Y, minlength=self.n_classes).float().clamp(min=1)
        w = (1.0 / counts.sqrt())[Y]                                # rare classes are sampled more often
        opt = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)
        steps = max(1, math.ceil(len(X) / batch_size))
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps)
        history = []
        self.model.train()
        for ep in range(epochs):
            total = 0.0
            for _ in range(steps):
                idx = torch.multinomial(w, min(batch_size, len(X)), replacement=True)
                x0, y0 = X[idx], Y[idx].clone()
                y0[torch.rand(len(y0), device=self.device) < label_dropout] = self.n_classes
                t = torch.randint(0, self.T, (len(x0),), device=self.device)
                eps = torch.randn_like(x0)
                ab = self.abar[t][:, None]
                xt = ab.sqrt() * x0 + (1 - ab).sqrt() * eps
                loss = F.mse_loss(self.model(xt, t, y0), eps)
                opt.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                opt.step(); sched.step()
                total += loss.item()
            history.append(total / steps)
            if verbose and (ep % 10 == 0 or ep == epochs - 1):
                print(f"    TabDDPM epoch {ep + 1:3d}/{epochs}  loss {history[-1]:.4f}")
        return history

    # ------------------------------------------------------------------ sampling
    @torch.no_grad()
    def sample(self, y: np.ndarray, guidance: float = 1.5, seed: int | None = None) -> np.ndarray:
        """Generate one synthetic (scaled) flow per label in `y`. guidance>1 = follow the class label harder."""
        self.model.eval()
        g = torch.Generator(device=self.device)
        if seed is not None:
            g.manual_seed(seed)
        Yc = torch.as_tensor(y, dtype=torch.long, device=self.device)
        Yu = torch.full_like(Yc, self.n_classes)
        x = torch.randn(len(Yc), self.n_features, device=self.device, generator=g)
        for i in reversed(range(self.T)):
            t = torch.full((len(Yc),), i, device=self.device, dtype=torch.long)
            eps = self.model(x, t, Yc)
            if guidance != 1.0:
                eps_u = self.model(x, t, Yu)
                eps = eps_u + guidance * (eps - eps_u)
            ab, a, b = self.abar[i], self.alphas[i], self.betas[i]
            x0 = ((x - (1 - ab).sqrt() * eps) / ab.sqrt()).clamp(-6, 6)
            ab_prev = self.abar[i - 1] if i > 0 else torch.tensor(1.0, device=self.device)
            mean = (ab_prev.sqrt() * b / (1 - ab)) * x0 + (a.sqrt() * (1 - ab_prev) / (1 - ab)) * x
            if i > 0:
                var = b * (1 - ab_prev) / (1 - ab)
                x = mean + var.sqrt() * torch.randn(x.shape, device=self.device, generator=g)
            else:
                x = mean
        return x.clamp(-10, 10).cpu().numpy()

    def balance(self, x: np.ndarray, y: np.ndarray, target_per_class: int, max_new: int = 20000,
                seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
        """Return ONLY the synthetic rows needed to lift every rare class to `target_per_class`."""
        counts = np.bincount(y, minlength=self.n_classes)
        labels = []
        for c in range(self.n_classes):
            need = max(0, target_per_class - counts[c])
            if counts[c] > 0 and need > 0:
                labels += [c] * int(min(need, max_new))
        if not labels:
            return np.zeros((0, x.shape[1]), np.float32), np.zeros(0, np.int64)
        labels = np.array(labels, np.int64)
        return self.sample(labels, seed=seed), labels

    # ------------------------------------------------------------------ io
    def save(self, path: str) -> None:
        torch.save({"state": self.model.state_dict(), "n_features": self.n_features, "n_classes": self.n_classes,
                    "T": self.T, "hidden": self.model.inp.out_features}, path)

    @classmethod
    def load(cls, path: str, device: str = "cpu") -> "TabDDPM":
        ck = torch.load(path, map_location=device, weights_only=True)
        m = cls(ck["n_features"], ck["n_classes"], ck["T"], ck["hidden"], device)
        m.model.load_state_dict(ck["state"])
        return m
