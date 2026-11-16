"""Simulated network for training the self-healing agent (many networks run in parallel, vectorised in numpy).

World
  * N computers connected by a random graph. Computers 0 and 1 are 'critical' (gateway / server).
  * Hidden truth: each computer is clean or infected. Infection spreads to online neighbours.
  * The agent never sees the truth. It sees what Stage 1 would report: a noisy risk / confidence / anomaly score.
    A 'monitored' computer is watched closely (less noisy). An isolated one is watched in quarantine.
Actions per computer, every step:  0 monitor   1 isolate   2 reconnect
Reward per computer (a mix of its own and the team's):
  -1.0 per step infected and still online (damage, x3 for critical),   -0.25 per step isolated while clean (lost service),
  -0.1 for each isolate command,   -0.01 per monitored computer.
"""
from __future__ import annotations

import numpy as np

from .guardrails import ISOLATE, MONITOR, RECONNECT, action_mask, enforce_isolation_cap

OBS_DIM = 11
OBS_NAMES = ["risk", "confidence", "anomaly", "is_online", "is_monitored", "is_isolated", "iso_time",
             "neighbour_risk", "isolated_fraction", "ema_risk", "is_critical"]


class BatchedNetworkEnv:
    def __init__(self, n_envs: int = 16, n_nodes: int = 12, horizon: int = 60, beta: float = 0.12,
                 p_external: float = 0.012, p_clean_in_quarantine: float = 0.15, max_isolated_fraction: float = 0.5,
                 team_weight: float = 0.5, seed: int = 0):
        self.E, self.N, self.horizon = n_envs, n_nodes, horizon
        self.beta, self.p_ext, self.p_clean = beta, p_external, p_clean_in_quarantine
        self.max_iso_frac, self.team_w = max_isolated_fraction, team_weight
        self.rng = np.random.default_rng(seed)
        self.critical = np.zeros((n_envs, n_nodes), bool); self.critical[:, :2] = True
        self.reset()

    # ------------------------------------------------------------------ world
    def _random_graph(self) -> np.ndarray:
        adj = np.zeros((self.E, self.N, self.N), np.float32)
        for e in range(self.E):
            for i in range(self.N):                                    # ring keeps it connected
                j = (i + 1) % self.N; adj[e, i, j] = adj[e, j, i] = 1
            for _ in range(self.N):                                    # random chords
                i, j = self.rng.integers(0, self.N, 2)
                if i != j:
                    adj[e, i, j] = adj[e, j, i] = 1
        return adj

    def reset(self) -> tuple[np.ndarray, np.ndarray]:
        self.adj = self._random_graph()
        self.infected = np.zeros((self.E, self.N), bool)
        for e in range(self.E):
            self.infected[e, self.rng.choice(self.N, self.rng.integers(1, 3), replace=False)] = True
        self.status = np.zeros((self.E, self.N), np.int64)             # 0 online, 1 monitored, 2 isolated
        self.iso_time = np.zeros((self.E, self.N), np.float32)
        self.ema = np.zeros((self.E, self.N), np.float32)
        self.t = 0
        self._observe()
        return self.obs, self.mask

    # ------------------------------------------------------------------ what the agent sees
    def _observe(self) -> None:
        base = np.where(self.infected, 0.85, 0.10)
        sigma = np.select([self.status == 1, self.status == 2], [0.10, 0.12], default=0.25)
        risk = np.clip(base + self.rng.normal(0, 1, base.shape) * sigma, 0, 1)
        conf = np.clip(0.5 + np.abs(risk - 0.5) + self.rng.normal(0, 0.08, base.shape), 0, 1)
        anomaly = np.clip(base * 0.9 + self.rng.normal(0, 1, base.shape) * (sigma + 0.05), 0, 1)
        self.ema = 0.5 * self.ema + 0.5 * risk if self.t > 0 else risk
        nbr = (self.adj @ risk[..., None])[..., 0] / np.maximum(self.adj.sum(-1), 1)
        iso_frac = (self.status == 2).mean(1, keepdims=True).repeat(self.N, 1)
        onehot = np.stack([self.status == 0, self.status == 1, self.status == 2], -1).astype(np.float32)
        self.obs = np.concatenate([
            risk[..., None], conf[..., None], anomaly[..., None], onehot, np.minimum(self.iso_time, 10)[..., None] / 10,
            nbr[..., None], iso_frac[..., None], self.ema[..., None], self.critical[..., None]], -1).astype(np.float32)
        self.risk = risk
        self.mask = action_mask(self.status)

    # ------------------------------------------------------------------ dynamics
    def step(self, actions: np.ndarray):
        """actions: (E, N) ints. Illegal actions are turned into monitor. Returns obs, mask, reward (E,N), done, info."""
        actions = np.where(np.take_along_axis(self.mask, actions[..., None], -1)[..., 0], actions, MONITOR)
        for e in range(self.E):                                        # blast-radius guardrail, same as at deploy time
            actions[e] = enforce_isolation_cap(actions[e], self.risk[e], self.status[e], self.max_iso_frac)

        iso_cmd = (actions == ISOLATE)
        rec_cmd = (actions == RECONNECT)
        mon_cmd = (actions == MONITOR) & (self.status != 2)
        self.status = np.where(iso_cmd, 2, np.where(rec_cmd, 0, np.where(mon_cmd, 1, self.status)))
        self.iso_time = np.where(iso_cmd, 0, np.where(self.status == 2, self.iso_time + 1, 0)).astype(np.float32)

        active = self.status != 2
        carriers = (self.infected & active).astype(np.float32)
        n_inf_nbrs = (self.adj @ carriers[..., None])[..., 0]
        p_inf = 1 - (1 - self.beta) ** n_inf_nbrs
        p_inf = 1 - (1 - p_inf) * (1 - self.p_ext)
        newly = active & ~self.infected & (self.rng.random(self.infected.shape) < p_inf)
        cleaned = (self.status == 2) & self.infected & (self.rng.random(self.infected.shape) < self.p_clean)
        self.infected = (self.infected | newly) & ~cleaned

        w = np.where(self.critical, 3.0, 1.0)
        own = (-1.0 * w * (self.infected & active)
               - 0.25 * w * ((self.status == 2) & ~self.infected)
               - 0.10 * iso_cmd - 0.01 * (self.status == 1))
        reward = ((1 - self.team_w) * own + self.team_w * own.mean(1, keepdims=True)).astype(np.float32)

        self.t += 1
        info = {"infected_online": (self.infected & active).sum(1).astype(float),
                "isolated_clean": ((self.status == 2) & ~self.infected).sum(1).astype(float),
                "own_return": own.sum(1)}
        done = self.t >= self.horizon
        self._observe()
        return self.obs, self.mask, reward, done, info
