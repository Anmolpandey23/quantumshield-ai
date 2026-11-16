"""PPO (Proximal Policy Optimisation) written from scratch in PyTorch, no extra RL library.

One small network is shared by every computer (parameter sharing):
  - a node encoder looks at one computer's observation,
  - the actor sees [that computer's embedding, the network-wide average embedding] and outputs 3 action logits,
  - the critic sees the same input and predicts that computer's future reward.
Illegal actions are masked out before sampling.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .env import OBS_DIM, BatchedNetworkEnv

NEG = -1e9


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int = OBS_DIM, hidden: int = 64):
        super().__init__()
        self.cfg = {"obs_dim": obs_dim, "hidden": hidden}
        self.enc = nn.Sequential(nn.Linear(obs_dim, hidden), nn.Tanh(), nn.Linear(hidden, hidden), nn.Tanh())
        self.actor = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.Tanh(), nn.Linear(hidden, 3))
        self.critic = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.Tanh(), nn.Linear(hidden, 1))

    def forward(self, obs: torch.Tensor, mask: torch.Tensor):
        """obs (B,N,d), mask (B,N,3) -> logits (B,N,3), value (B,N)."""
        h = self.enc(obs)
        g = h.mean(1, keepdim=True).expand_as(h)
        z = torch.cat([h, g], -1)
        logits = self.actor(z).masked_fill(~mask, NEG)
        return logits, self.critic(z).squeeze(-1)

    @torch.no_grad()
    def act_greedy(self, obs: np.ndarray, mask: np.ndarray) -> np.ndarray:
        logits, _ = self(torch.as_tensor(obs, dtype=torch.float32)[None], torch.as_tensor(mask)[None])
        return logits[0].argmax(-1).numpy()


def train_ppo(iterations: int = 300, n_envs: int = 16, n_nodes: int = 12, horizon: int = 60, gamma: float = 0.97,
              lam: float = 0.95, clip: float = 0.2, lr: float = 3e-4, epochs: int = 4, minibatch: int = 256,
              ent_coef: float = 0.01, vf_coef: float = 0.5, seed: int = 0, device: str = "cpu", verbose: bool = True):
    torch.manual_seed(seed); np.random.seed(seed)
    dev = torch.device(device)
    env = BatchedNetworkEnv(n_envs, n_nodes, horizon, seed=seed)
    net = ActorCritic().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    history = []
    for it in range(iterations):
        obs, mask = env.reset()
        O, M, A, LP, R, V = [], [], [], [], [], []
        ep_ret = np.zeros(n_envs); ep_inf = np.zeros(n_envs); ep_iso = np.zeros(n_envs)
        for _ in range(horizon):
            ot = torch.as_tensor(obs, device=dev); mt = torch.as_tensor(mask, device=dev)
            with torch.no_grad():
                logits, v = net(ot, mt)
                dist = torch.distributions.Categorical(logits=logits)
                a = dist.sample()
                lp = dist.log_prob(a)
            obs2, mask2, r, done, info = env.step(a.cpu().numpy())
            O.append(ot); M.append(mt); A.append(a); LP.append(lp); V.append(v)
            R.append(torch.as_tensor(r, device=dev))
            ep_ret += info["own_return"]; ep_inf += info["infected_online"]; ep_iso += info["isolated_clean"]
            obs, mask = obs2, mask2
        with torch.no_grad():
            _, last_v = net(torch.as_tensor(obs, device=dev), torch.as_tensor(mask, device=dev))
        # ---- GAE (per computer)
        adv = torch.zeros(horizon, n_envs, n_nodes, device=dev)
        nxt, gae = last_v, torch.zeros_like(last_v)
        for t in reversed(range(horizon)):
            delta = R[t] + gamma * nxt - V[t]
            gae = delta + gamma * lam * gae
            adv[t] = gae; nxt = V[t]
        ret = adv + torch.stack(V)
        # ---- flatten (time x env) into samples
        o, m, a_, lp0 = (torch.stack(x).reshape(horizon * n_envs, n_nodes, -1) if x[0].dim() == 3 else torch.stack(x).reshape(horizon * n_envs, n_nodes)
                         for x in (O, M, A, LP))
        adv_f, ret_f = adv.reshape(-1, n_nodes), ret.reshape(-1, n_nodes)
        adv_f = (adv_f - adv_f.mean()) / (adv_f.std() + 1e-8)
        n = len(o)
        for _ in range(epochs):
            perm = torch.randperm(n, device=dev)
            for i in range(0, n, minibatch):
                b = perm[i:i + minibatch]
                logits, v = net(o[b], m[b])
                dist = torch.distributions.Categorical(logits=logits)
                lp = dist.log_prob(a_[b])
                ratio = (lp - lp0[b]).exp()
                surr = torch.min(ratio * adv_f[b], ratio.clamp(1 - clip, 1 + clip) * adv_f[b])
                loss = -surr.mean() + vf_coef * F.mse_loss(v, ret_f[b]) - ent_coef * dist.entropy().mean()
                opt.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(net.parameters(), 0.5)
                opt.step()
        history.append({"iteration": it + 1, "return": float(ep_ret.mean()), "infected_node_steps": float(ep_inf.mean()),
                        "clean_isolated_node_steps": float(ep_iso.mean())})
        if verbose and (it % 25 == 0 or it == iterations - 1):
            h = history[-1]
            print(f"  iter {h['iteration']:4d}/{iterations}  return {h['return']:8.1f}  infected-steps {h['infected_node_steps']:6.1f}  "
                  f"wrongly-isolated-steps {h['clean_isolated_node_steps']:6.1f}")
    return net, history
