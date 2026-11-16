"""Compare policies on fresh simulated networks:  python -m stage3.evaluate"""
from __future__ import annotations

import argparse
import pathlib

import numpy as np
import torch

from . import baselines
from .env import BatchedNetworkEnv
from .ppo import ActorCritic


def run(policy_fn, episodes_envs: int = 64, n_nodes: int = 12, horizon: int = 60, seed: int = 123) -> dict:
    env = BatchedNetworkEnv(episodes_envs, n_nodes, horizon, seed=seed)
    rng = np.random.default_rng(seed)
    obs, mask = env.reset()
    ret = np.zeros(episodes_envs); inf = np.zeros(episodes_envs); iso = np.zeros(episodes_envs)
    for _ in range(horizon):
        obs, mask, _, _, info = env.step(policy_fn(obs, mask, rng))
        ret += info["own_return"]; inf += info["infected_online"]; iso += info["isolated_clean"]
    return {"return": round(float(ret.mean()), 1), "infected_node_steps": round(float(inf.mean()), 1),
            "wrongly_isolated_node_steps": round(float(iso.mean()), 1)}


def ppo_policy(net: ActorCritic):
    def fn(obs, mask, rng=None):
        with torch.no_grad():
            logits, _ = net(torch.as_tensor(obs), torch.as_tensor(mask))
        return logits.argmax(-1).numpy()
    return fn


def compare(net: ActorCritic | None) -> dict:
    res = {"never_act": run(baselines.never_act), "random": run(baselines.random_policy), "rule": run(baselines.rule_policy)}
    if net is not None:
        res["ppo"] = run(ppo_policy(net))
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default=str(pathlib.Path(__file__).resolve().parent.parent / "artifacts" / "ppo_policy.pt"))
    a = ap.parse_args()
    net = None
    if pathlib.Path(a.weights).exists():
        ck = torch.load(a.weights, map_location="cpu", weights_only=True)
        net = ActorCritic(**ck["cfg"]); net.load_state_dict(ck["state"])
    else:
        print(f"(no weights at {a.weights}: run `python -m stage3.train` first; showing baselines only)")
    print(f"{'policy':12} {'return':>9} {'infected node-steps':>20} {'wrongly isolated node-steps':>28}")
    for k, v in compare(net).items():
        print(f"{k:12} {v['return']:9.1f} {v['infected_node_steps']:20.1f} {v['wrongly_isolated_node_steps']:28.1f}")
    print("\nHigher return is better. Fewer infected node-steps = less damage; fewer wrongly-isolated = less lost service.")


if __name__ == "__main__":
    main()
