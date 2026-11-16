"""Train the PPO agent:  python -m stage3.train   (about 2-4 minutes on a laptop CPU)"""
from __future__ import annotations

import argparse
import json
import pathlib

import torch

from .evaluate import compare
from .ppo import train_ppo

ARTIFACTS = pathlib.Path(__file__).resolve().parent.parent / "artifacts"


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=300)
    ap.add_argument("--n-nodes", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(ARTIFACTS))
    a = ap.parse_args(argv)
    net, hist = train_ppo(a.iterations, n_nodes=a.n_nodes, seed=a.seed)
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    torch.save({"state": net.state_dict(), "cfg": net.cfg}, out / "ppo_policy.pt")
    res = compare(net)
    (out / "ppo_report.json").write_text(json.dumps({"comparison": res, "history": hist[::10]}, indent=2))
    for k, v in res.items():
        print(f"  {k:10} {v}")
    print(f"saved -> {out / 'ppo_policy.pt'}")
    return res


if __name__ == "__main__":
    main()
