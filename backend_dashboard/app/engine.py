"""Engine = orchestrator + Stage 1 predictor + SQLite log + live broadcast. The FastAPI layer is a thin shell around it."""
from __future__ import annotations

import asyncio
import random
import threading
import time
from datetime import datetime, timezone

from . import config
from .simulator import ReplaySimulator, StubSimulator, fake_stage1
from .store import Store


class Engine:
    def __init__(self, db_path: str | None = None, n_qubits: int | None = None, use_real: bool | None = None):
        self.n_qubits = n_qubits or config.N_QUBITS
        use_real = config.USE_REAL_MODELS if use_real is None else use_real
        self.store = Store(db_path or config.DB_PATH)
        self.predictor, self.mode = None, {"stage1": "stub", "stage3": "stub"}
        self.critical = set(config.CRITICAL_NODES)
        self.orch = None
        if use_real:
            try:
                from integration.live import build_live
                self.orch, self.predictor = build_live(self.n_qubits, self.critical)
                self.mode["stage3"] = "ppo" if self.orch.policy.net is not None else "rule_fallback"
                self.mode["stage1"] = "real" if self.predictor else "stub"
            except Exception as exc:                                  # torch not installed, etc.
                print(f"[engine] real Stage 1/3 unavailable ({exc}); using stubs")
        if self.orch is None:
            from integration.orchestrator import Orchestrator
            self.orch = Orchestrator(n_qubits=self.n_qubits)
        self.last_s1: dict[str, dict] = {}
        self.last_seen: dict[str, str] = {}
        self.queues: set[asyncio.Queue] = set()
        self.sim_task: asyncio.Task | None = None
        self.healing_task: asyncio.Task | None = None
        self.sim = None
        self.sim_interval = 3.0
        self._lock = threading.Lock()
        self.started = time.time()
        self.sim_run: dict | None = None            # last dashboard scenario run (see run_scenario)
        for i in range(14):
            n = f"10.1.0.{i + 1}"
            self.orch.status.setdefault(n, "online")
            self.orch.node_keys.setdefault(n, f"key_{n}_{abs(hash(n)) & 0xffffffff:08x}")

    # ------------------------------------------------------------------ processing (blocking: call via a thread pool)
    def _record(self, event: dict) -> dict:
        with self._lock:
            self.last_s1[event["node_id"]] = event["stage1"]
            self.last_seen[event["node_id"]] = event["timestamp"]
            event["id"] = self.store.add(event)
        return event

    def process_stage1(self, s1: dict, eve_fraction: float = 0.0, seed: int | None = None) -> dict:
        return self._record(self.orch.handle(s1, eve_fraction=eve_fraction, seed=seed))

    def process_flows(self, flows: list[dict]) -> list[dict]:
        if self.predictor is None:
            raise RuntimeError("Stage 1 models are not trained yet. Run: cd stage1_ai_threat_prediction && python -m stage1.train")
        import pandas as pd
        df = pd.DataFrame(flows)
        self.predictor.ingest(df)
        return [self.process_stage1(self.predictor.predict(n)) for n in df["Source IP"].unique()]

    def approve(self, approval_id: str, approver: str) -> dict:
        return self._record(self.orch.approve(approval_id, approver))

    def reject(self, approval_id: str, approver: str) -> dict:
        return self._record(self.orch.reject(approval_id, approver))

    def scenario(self, name: str, node_id: str | None = None) -> dict:
        """One-click demo events for the dashboard buttons."""
        rng = random.Random()
        node = node_id or f"10.0.0.{rng.randint(5, 40)}"
        if name == "attack":
            return self.process_stage1(fake_stage1(node, rng.choice(["DDoS", "PortScan", "BruteForce"]), rng))
        if name == "eavesdrop":
            return self.process_stage1(fake_stage1(node, "DDoS", rng), eve_fraction=1.0)
        if name in ("clean", "benign"):
            return self.process_stage1(fake_stage1(node, None, rng))
        raise ValueError(f"unknown scenario '{name}'")

    def run_scenario(self, scenario: str, intensity: int, nodes: int, seed: int | None = None) -> dict:
        """The dashboard's Simulation Center: inject one attack scenario into `nodes` simulated machines and run it
        through the REAL Stage 2 -> 3 -> 4 pipeline. ddos / lateral = attacks on a clean channel;
        hndl (harvest-now-decrypt-later) = an eavesdropper on every channel, which Stage 2 must catch."""
        attack = {"ddos": "DDoS", "lateral": "BruteForce", "hndl": "DDoS"}.get(scenario)
        if attack is None:
            raise ValueError(f"unknown scenario '{scenario}'")
        rng = random.Random(seed)
        nodes = max(1, min(int(nodes), 250))
        attacked = max(1, min(nodes, round(nodes * max(0, min(100, intensity)) / 100 * 0.3)))
        eve = 1.0 if scenario == "hndl" else 0.0
        events = []
        for i in range(nodes):
            node = f"10.1.0.{i + 1}"
            hit = i < attacked
            events.append(self.process_stage1(fake_stage1(node, attack if hit else None, rng), eve if hit else 0.0))
            if not hit and self.orch.status.get(node) != "isolated" and node not in self.orch.node_keys:
                self.orch.node_keys[node] = f"key_{node}_{abs(hash(node + str(seed))) & 0xffffffff:08x}"
        self.sim_run = {"config": {"scenario": scenario, "intensity": intensity, "nodes": nodes}, "attack": attack,
                        "attacked": attacked, "events": events}
        return self.sim_run

    # ------------------------------------------------------------------ views
    def nodes(self) -> list[dict]:
        crit = getattr(getattr(self.orch.policy, "guardrails", None), "critical_nodes", self.critical)
        out = []
        for n in sorted(set(self.last_s1) | set(self.orch.status)):
            s1 = self.last_s1.get(n, {})
            out.append({"node_id": n, "status": self.orch.status.get(n, "online"), "threat_label": s1.get("threat_label", "BENIGN"),
                        "risk_score_node": s1.get("risk_score_node", 0.0), "confidence": s1.get("confidence", 0.0),
                        "anomaly_score": s1.get("anomaly_score", 0.0), "explanation": s1.get("explanation", []),
                        "key_id": self.orch.node_keys.get(n), "critical": n in crit, "last_seen": self.last_seen.get(n)})
        return out

    def stats(self) -> dict:
        s = self.store.stats()
        st = [v for v in self.orch.status.values()]
        s.update(nodes_total=len(set(self.last_s1) | set(self.orch.status)), nodes_isolated=st.count("isolated"),
                 nodes_monitored=st.count("monitored"), pending_approvals=len(self.orch.list_pending()),
                 threat_breakdown=self.store.threat_breakdown(), mode=self.mode, simulator=self.sim_status())
        return s

    def health(self) -> dict:
        return {"status": "ok", "mode": self.mode, "n_qubits": self.n_qubits, "time": datetime.now(timezone.utc).isoformat()}

    # ------------------------------------------------------------------ live broadcast
    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self.queues.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self.queues.discard(q)

    def snapshot_message(self) -> dict:
        return {"type": "snapshot", "nodes": self.nodes(), "stats": self.stats(), "pending": self.orch.list_pending(),
                "events": self.store.recent(30)}

    async def broadcast(self, event: dict | None = None) -> None:
        msg = {"type": "event", "event": event, "nodes": self.nodes(), "stats": self.stats(), "pending": self.orch.list_pending()}
        for q in list(self.queues):
            if q.full():
                try: q.get_nowait()
                except asyncio.QueueEmpty: pass
            q.put_nowait(msg)

    # ------------------------------------------------------------------ background simulator
    def sim_status(self) -> dict:
        return {"running": bool(self.sim_task and not self.sim_task.done()), "kind": getattr(self.sim, "name", None),
                "interval_s": self.sim_interval}

    async def start_sim(self, interval: float = 3.0) -> dict:
        if self.sim_task and not self.sim_task.done():
            return self.sim_status()
        self.sim_interval = max(0.5, float(interval))
        self.sim = ReplaySimulator(self.predictor) if self.predictor is not None else StubSimulator()

        async def loop():
            while True:
                batch = await asyncio.to_thread(self.sim.tick, dict(self.orch.status))
                for s1, eve in batch:
                    ev = await asyncio.to_thread(self.process_stage1, s1, eve)
                    if ev["decision"] != "no_action" or ev["node_id"] not in self.last_seen:
                        await self.broadcast(ev)
                await self.broadcast(None)
                await asyncio.sleep(self.sim_interval)

        self.sim_task = asyncio.create_task(loop())
        return self.sim_status()

    async def stop_sim(self) -> dict:
        if self.sim_task:
            self.sim_task.cancel()
            try:
                await self.sim_task
            except (asyncio.CancelledError, Exception):
                pass
        return self.sim_status()

    async def start_healing_watcher(self) -> None:
        """Background autonomous watcher: detects isolated nodes and feeds clean observation
        steps so Stage 3 satisfies its cooldown and issues an ML-DSA signed RECONNECT command."""
        if self.healing_task and not self.healing_task.done():
            return

        async def loop():
            while True:
                await asyncio.sleep(2.0)
                try:
                    isolated = [n for n, st in list(self.orch.status.items()) if st == "isolated"]
                    if not isolated:
                        continue
                    for node in isolated:
                        ev = await asyncio.to_thread(self.scenario, "clean", node)
                        if ev.get("decision") == "command_issued":
                            await self.broadcast(ev)
                except Exception:
                    pass

        self.healing_task = asyncio.create_task(loop())

    async def stop_healing_watcher(self) -> None:
        if self.healing_task:
            self.healing_task.cancel()
            try:
                await self.healing_task
            except (asyncio.CancelledError, Exception):
                pass

    def reset(self) -> None:
        self.store.clear()
        self.last_s1.clear(); self.last_seen.clear(); self.sim_run = None
        self.orch.status.clear(); self.orch.node_keys.clear(); self.orch.pending.clear()
        if hasattr(self.orch.policy, "status"):
            for d in (self.orch.policy.status, self.orch.policy.ema, self.orch.policy.last, self.orch.policy.iso_obs):
                d.clear()
        if self.orch.fleet is not None:
            self.orch.fleet.agents.clear()
