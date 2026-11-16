"""Run the whole loop:  python -m integration.demo   (add --live to use the real Stage 1 + Stage 3 models)"""
import sys

from .orchestrator import Orchestrator
from .stubs import stage1_stub


def show(title: str, e: dict) -> None:
    cmd = e["stage3_command"]["payload"]["action"] if e["stage3_command"] else None
    s2 = e["stage2"]["status"] if e["stage2"] else None
    print(f"{title:34} decision={e['decision']:22} stage2={s2}  command={cmd}  verified={e['command_verified']}  node={e.get('node_status')}")


if __name__ == "__main__":
    if "--live" in sys.argv:
        from .live import build_live
        o, _ = build_live()
    else:
        o = Orchestrator()
    show("1. Benign traffic", o.handle(stage1_stub("192.168.1.20", attack=False)))
    show("2. Attack detected", o.handle(stage1_stub("192.168.1.14"), seed=5))
    show("3. Attack + eavesdropper on line", o.handle(stage1_stub("192.168.1.16"), eve_fraction=1.0, seed=6))
    e = o.handle(stage1_stub("192.168.1.15"), seed=7)
    print("4. Replay of a genuine command    ->", o.verifier.verify(e["stage3_command"]))
    show("5. Machine looks clean again", o.handle(stage1_stub("192.168.1.14", attack=False), seed=8))
