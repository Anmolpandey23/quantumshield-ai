"""Supervised flow classifier (MLP). Trained on real flows + TabDDPM synthetic flows.
Gives the threat label and confidence, and supports gradient x input explanations (XAI)."""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import f1_score


class FlowClassifier(nn.Module):
    def __init__(self, n_features: int, n_classes: int, hidden: int = 256, dropout: float = 0.2):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(n_features, hidden), nn.ReLU(), nn.Dropout(dropout),
                                 nn.Linear(hidden, hidden // 2), nn.ReLU(), nn.Dropout(dropout),
                                 nn.Linear(hidden // 2, n_classes))
        self.cfg = {"n_features": n_features, "n_classes": n_classes, "hidden": hidden, "dropout": dropout}

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    @torch.no_grad()
    def predict_proba(self, x: np.ndarray, batch: int = 8192) -> np.ndarray:
        self.eval()
        dev = next(self.parameters()).device
        out = [F.softmax(self(torch.as_tensor(x[i:i + batch], dtype=torch.float32, device=dev)), -1).cpu().numpy()
               for i in range(0, len(x), batch)]
        return np.concatenate(out) if out else np.zeros((0, self.cfg["n_classes"]), np.float32)

    def attribution(self, x: np.ndarray, target: int) -> np.ndarray:
        """|gradient x input| of the logit of class `target`, averaged over the rows of x -> (n_features,)."""
        self.eval()
        dev = next(self.parameters()).device
        xt = torch.as_tensor(x, dtype=torch.float32, device=dev).clone().requires_grad_(True)
        self(xt)[:, target].sum().backward()
        return (xt.grad * xt).abs().mean(0).detach().cpu().numpy()


def train_classifier(x: np.ndarray, y: np.ndarray, x_val: np.ndarray, y_val: np.ndarray, n_classes: int,
                     epochs: int = 20, batch_size: int = 512, lr: float = 2e-3, device: str = "cpu",
                     verbose: bool = True, seed: int = 0) -> tuple[FlowClassifier, float]:
    torch.manual_seed(seed)
    dev = torch.device(device)
    model = FlowClassifier(x.shape[1], n_classes).to(dev)
    counts = np.bincount(y, minlength=n_classes).astype(np.float32)
    cw = torch.as_tensor((counts.sum() / np.maximum(counts, 1) / n_classes) ** 0.5, device=dev)   # soft class weights
    X, Y = torch.as_tensor(x, device=dev), torch.as_tensor(y, device=dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    best, best_state = -1.0, None
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(len(X), device=dev)
        for i in range(0, len(X), batch_size):
            b = perm[i:i + batch_size]
            loss = F.cross_entropy(model(X[b]), Y[b], weight=cw)
            opt.zero_grad(); loss.backward(); opt.step()
        f1 = f1_score(y_val, model.predict_proba(x_val).argmax(1), average="macro", zero_division=0)
        if f1 > best:
            best, best_state = f1, {k: v.detach().clone() for k, v in model.state_dict().items()}
        if verbose and (ep % 5 == 0 or ep == epochs - 1):
            print(f"    classifier epoch {ep + 1:3d}/{epochs}  val macro-F1 {f1:.4f}")
    model.load_state_dict(best_state)
    return model, best
