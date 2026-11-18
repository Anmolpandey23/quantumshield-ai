"""FastAPI app.  Run:  uvicorn app.main:app --reload --port 8000   (from the backend_dashboard folder)
Docs (try every endpoint in the browser):  http://localhost:8000/docs
Built-in dashboard:                        http://localhost:8000/
"""
from __future__ import annotations

import asyncio
import hmac
import pathlib
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from . import adapter, config
from .engine import Engine

STATIC = pathlib.Path(__file__).resolve().parent.parent / "static"


class Stage1In(BaseModel):
    contract_version: str = "1.0"
    node_id: str = Field(min_length=1)
    threat_label: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    anomaly_score: float = Field(ge=0, le=1)
    risk_score_node: float = Field(ge=0, le=1)
    explanation: list[str] = []

class FlowsIn(BaseModel):
    flows: list[dict] = Field(min_length=1, max_length=5000,
                              description="rows with the 34 CIC features + 'Source IP', 'Destination IP', 'Timestamp'")

class SimConfigIn(BaseModel):
    """Body the dashboard's Simulation Center sends (matches frontend SimulationConfig)."""
    scenario: Literal["ddos", "lateral", "hndl"]
    intensity: int = Field(ge=0, le=100)
    nodes: int = Field(ge=1, le=250)


class Approver(BaseModel):
    approver: str = "operator"


def create_app(engine: Engine | None = None) -> FastAPI:
    eng = engine or Engine()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await eng.start_healing_watcher()
        yield
        await eng.stop_sim()
        await eng.stop_healing_watcher()

    app = FastAPI(title="QuantumShield AI API", version="1.0.0", lifespan=lifespan)
    app.state.engine = eng
    app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=False,
                       allow_methods=["*"], allow_headers=["*"])

    def auth(x_api_key: str | None = Header(default=None)) -> None:
        if config.API_KEY and not (x_api_key and hmac.compare_digest(x_api_key, config.API_KEY)):
            raise HTTPException(401, "missing or wrong X-API-Key header")

    secured = [Depends(auth)]

    # ------------------------------------------------------------------ routes
    def snap() -> dict:
        return adapter.collect(eng)

    @app.get("/api/health")
    def health():
        return eng.health()

    @app.get("/api/stats", dependencies=secured)
    def stats():
        return eng.stats()

    @app.get("/api/nodes", dependencies=secured)
    def nodes():
        return eng.nodes()

    @app.get("/api/events", dependencies=secured)
    def events(limit: int = Query(50, ge=1, le=1000), node_id: str | None = None, decision: str | None = None):
        return eng.store.recent(limit, node_id, decision)

    @app.get("/api/keys", dependencies=secured)
    def keys(limit: int = Query(50, ge=1, le=1000)):
        return eng.store.keys(limit)

    @app.post("/api/events/stage1", dependencies=secured)
    async def post_stage1(body: Stage1In, eve_fraction: float = Query(0.0, ge=0, le=1)):
        """Push one Stage 1 result through Stage 2 -> 3 -> 4 (used by the simulator, tests and teammates)."""
        ev = await run_in_threadpool(eng.process_stage1, body.model_dump(), eve_fraction)
        await eng.broadcast(ev)
        return ev

    @app.post("/api/ingest/flows", dependencies=secured)
    async def ingest(body: FlowsIn):
        """Real path: raw network flows -> Stage 1 models -> Stage 2 -> Stage 3 -> dashboard."""
        try:
            evs = await run_in_threadpool(eng.process_flows, body.flows)
        except RuntimeError as exc:
            raise HTTPException(503, str(exc))
        except KeyError as exc:
            raise HTTPException(422, f"missing column {exc}")
        for ev in evs:
            await eng.broadcast(ev)
        return evs

    @app.post("/api/simulate/{scenario}", dependencies=secured)
    async def simulate(scenario: str, node_id: str | None = None):
        """scenario = attack | eavesdrop | clean. One click on the dashboard."""
        try:
            ev = await run_in_threadpool(eng.scenario, scenario, node_id)
        except ValueError as exc:
            raise HTTPException(404, str(exc))
        await eng.broadcast(ev)
        return ev

    @app.post("/api/simulator/start", dependencies=secured)
    async def sim_start(interval: float = Query(3.0, ge=0.5, le=60)):
        return await eng.start_sim(interval)

    @app.post("/api/simulator/stop", dependencies=secured)
    async def sim_stop():
        return await eng.stop_sim()

    @app.get("/api/approvals", dependencies=secured)
    def approvals():
        return eng.orch.list_pending()

    @app.post("/api/approvals/{approval_id}/approve", dependencies=secured)
    async def approve(approval_id: str, body: Approver = Approver()):
        try:
            ev = await run_in_threadpool(eng.approve, approval_id, body.approver)
        except KeyError:
            raise HTTPException(404, "unknown or already handled approval id")
        await eng.broadcast(ev)
        return ev

    @app.post("/api/approvals/{approval_id}/reject", dependencies=secured)
    async def reject(approval_id: str, body: Approver = Approver()):
        try:
            ev = await run_in_threadpool(eng.reject, approval_id, body.approver)
        except KeyError:
            raise HTTPException(404, "unknown or already handled approval id")
        await eng.broadcast(ev)
        return ev

    @app.post("/api/reset", dependencies=secured)
    async def reset():
        await eng.stop_sim()
        eng.reset()
        await eng.broadcast(None)
        return {"ok": True}

    @app.websocket("/ws")
    async def ws(socket: WebSocket, api_key: str | None = None):
        if config.API_KEY and not (api_key and hmac.compare_digest(api_key, config.API_KEY)):
            await socket.close(code=4401)
            return
        await socket.accept()
        q = eng.subscribe()
        try:
            await socket.send_json(eng.snapshot_message())
            while True:
                await socket.send_json(await q.get())
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            eng.unsubscribe(q)

    # ---- shapes for the React dashboard (frontend/). Built from real events by app/adapter.py ----
    @app.get("/api/overview", dependencies=secured)
    def overview():
        return adapter.overview(snap())

    @app.get("/api/threats", dependencies=secured)
    def threats():
        return adapter.threats(snap())

    @app.get("/api/crypto", dependencies=secured)
    def crypto():
        return adapter.crypto(snap())

    @app.get("/api/healing", dependencies=secured)
    def healing():
        return adapter.healing(snap())

    @app.post("/api/healing/restore", dependencies=secured)
    async def restore_isolated(node_id: str | None = None):
        """Restore quarantined nodes by sending clean traffic steps to satisfy cooldown and trigger PQC reconnection."""
        if node_id:
            targets = [node_id] if eng.orch.status.get(node_id) == "isolated" else []
        else:
            targets = [n for n, st in eng.orch.status.items() if st == "isolated"]
        reconnected = []
        for n in targets:
            for _ in range(3):
                ev = await run_in_threadpool(eng.scenario, "clean", n)
                if ev.get("decision") == "command_issued" and ev.get("node_status") == "online":
                    reconnected.append(n)
                    break
        await eng.broadcast(None)
        return {"reconnected": reconnected, "remaining_isolated": sum(1 for st in eng.orch.status.values() if st == "isolated")}

    @app.get("/api/topology", dependencies=secured)
    def topology():
        return adapter.topology(snap())

    @app.get("/api/pipeline", dependencies=secured)
    def pipeline():
        return adapter.pipeline(snap())

    @app.get("/api/logs", dependencies=secured)
    def logs():
        return adapter.logs(snap())

    @app.post("/api/simulation/{stage}", dependencies=secured)
    async def simulation(stage: Literal["traffic", "detection", "crypto", "healing", "final"], body: SimConfigIn):
        """Simulation Center. `traffic` injects the scenario and runs the real pipeline; later stages report on that run."""
        if stage == "traffic":
            await run_in_threadpool(eng.run_scenario, body.scenario, body.intensity, body.nodes)
            await eng.broadcast(None)
        elif eng.sim_run is None:
            raise HTTPException(409, "no scenario has been run yet: call stage 'traffic' first")
        ctx = await run_in_threadpool(adapter.collect, eng)
        return adapter.simulation_stage(stage, eng.sim_run, ctx)

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    return app


app = create_app()
