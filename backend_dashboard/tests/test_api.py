import pytest
from fastapi.testclient import TestClient

from app.engine import Engine
from app.main import create_app

S1_ATTACK = {"contract_version": "1.0", "node_id": "10.0.0.14", "threat_label": "DDoS", "confidence": 0.94,
             "anomaly_score": 0.87, "risk_score_node": 0.91, "explanation": ["unusual packet rate"]}


@pytest.fixture()
def client():
    eng = Engine(db_path=":memory:", n_qubits=1024, use_real=False)       # stub Stage 1/3: fast, no torch needed
    with TestClient(create_app(eng)) as c:
        yield c


def test_health_and_dashboard_page(client):
    assert client.get("/api/health").json()["status"] == "ok"
    assert "QuantumShield" in client.get("/").text


def test_attack_flows_through_all_stages_and_shows_up_everywhere(client):
    ev = client.post("/api/events/stage1", json=S1_ATTACK).json()
    assert ev["decision"] == "command_issued" and ev["command_verified"] is True
    assert ev["stage3_command"]["payload"]["action"] == "isolate"
    assert client.get("/api/events").json()[0]["id"] == ev["id"]
    node = {n["node_id"]: n for n in client.get("/api/nodes").json()}["10.0.0.14"]
    assert node["status"] == "isolated"
    keys = client.get("/api/keys").json()
    assert keys[0]["status"] == "secure_channel_established" and keys[0]["qber"] < 0.05
    st = client.get("/api/stats").json()
    assert st["isolations"] == 1 and st["key_exchanges_ok"] == 1 and st["nodes_isolated"] == 1


def test_eavesdropper_is_caught_and_no_command_sent(client):
    ev = client.post("/api/events/stage1?eve_fraction=1.0", json=S1_ATTACK).json()
    assert ev["decision"] == "aborted_no_command" and ev["stage3_command"] is None
    assert ev["stage2"]["eavesdrop_detected"] is True and ev["stage2"]["qber"] >= 0.11
    assert client.get("/api/stats").json()["eavesdrop_aborts"] == 1


def test_clean_machine_is_reconnected_with_new_keys(client):
    client.post("/api/events/stage1", json=S1_ATTACK)
    clean = {**S1_ATTACK, "threat_label": "BENIGN", "confidence": 0.98, "anomaly_score": 0.03, "risk_score_node": 0.04, "explanation": []}
    ev = client.post("/api/events/stage1", json=clean).json()
    assert ev["stage3_command"]["payload"]["action"] == "reconnect" and ev["rekeyed"] is True
    assert client.get("/api/stats").json()["reconnections"] == 1


def test_bad_input_is_rejected_by_validation(client):
    assert client.post("/api/events/stage1", json={**S1_ATTACK, "confidence": 3}).status_code == 422
    assert client.post("/api/simulate/unknown").status_code == 404
    assert client.post("/api/approvals/apr_404/approve").status_code == 404
    assert client.post("/api/ingest/flows", json={"flows": [{"a": 1}]}).status_code == 503     # no real predictor in stub mode


def test_websocket_streams_snapshot_then_events(client):
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json()["type"] == "snapshot"
        client.post("/api/simulate/attack")
        msg = ws.receive_json()
        assert msg["type"] == "event" and msg["event"]["stage1"]["threat_label"] != "BENIGN"


def test_api_key_protects_everything_but_health(monkeypatch, client):
    from app import config
    monkeypatch.setattr(config, "API_KEY", "secret")
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/nodes").status_code == 401
    assert client.get("/api/nodes", headers={"X-API-Key": "secret"}).status_code == 200
    assert client.post("/api/reset", headers={"X-API-Key": "nope"}).status_code == 401


def test_human_approval_flow_end_to_end():
    eng = Engine(db_path=":memory:", n_qubits=512, use_real=True)         # real Stage 3 policy (rule fallback if no weights)
    eng.orch.policy.guardrails.critical_nodes.add("10.0.0.2")
    with TestClient(create_app(eng)) as c:
        for n in ("10.0.0.2", "10.0.0.5", "10.0.0.6"):
            for _ in range(3):
                c.post("/api/events/stage1", json={**S1_ATTACK, "node_id": n, "threat_label": "BENIGN", "confidence": .98,
                                                   "anomaly_score": .03, "risk_score_node": .04, "explanation": []})
        pending = None
        for _ in range(4):
            ev = c.post("/api/events/stage1", json={**S1_ATTACK, "node_id": "10.0.0.2"}).json()
            if ev["decision"] == "pending_human_approval":
                pending = ev["pending_approval"]; break
        assert pending, "critical node must wait for a human"
        assert c.get("/api/approvals").json()[0]["approval_id"] == pending["approval_id"]
        ok = c.post(f"/api/approvals/{pending['approval_id']}/approve", json={"approver": "alice"}).json()
        assert ok["decision"] == "command_issued" and ok["command_verified"] is True
        assert c.get("/api/approvals").json() == []


# ---------------------------------------------------------------------------------------- dashboard (frontend/) endpoints
DASHBOARD_ROUTES = {"overview": "/api/overview", "threats": "/api/threats", "crypto": "/api/crypto", "healing": "/api/healing",
                    "topology": "/api/topology", "pipeline": "/api/pipeline", "logs": "/api/logs"}


def test_dashboard_endpoints_match_the_frontend_types_on_an_empty_system(client):
    import frontend_contract as fc
    for name, path in DASHBOARD_ROUTES.items():
        r = client.get(path)
        assert r.status_code == 200, path
        fc.check(name, r.json())


def test_dashboard_endpoints_reflect_real_events(client):
    import frontend_contract as fc
    client.post("/api/events/stage1", json=S1_ATTACK)                          # isolated, key issued
    client.post("/api/events/stage1?eve_fraction=1.0", json={**S1_ATTACK, "node_id": "10.0.0.15"})   # eavesdropper caught
    for name, path in DASHBOARD_ROUTES.items():
        fc.check(name, client.get(path).json())
    topo = client.get("/api/topology").json()
    assert {n["id"] for n in topo["nodes"]} >= {"controller", "10.0.0.14", "10.0.0.15"}
    inc = {i["node"]: i for i in client.get("/api/healing").json()["incidents"]}
    assert inc["10.0.0.14"]["status"] == "in-progress" and inc["10.0.0.15"]["status"] == "escalated"
    assert client.get("/api/threats").json()["events"][0]["category"] == "DDoS"
    assert any(l["level"] == "ERROR" for l in client.get("/api/logs").json())


def test_simulation_center_runs_the_real_pipeline_stage_by_stage(client):
    import frontend_contract as fc
    cfg = {"scenario": "ddos", "intensity": 100, "nodes": 40}            # 12 attacked nodes: at least one is always isolated
    assert client.post("/api/simulation/detection", json=cfg).status_code == 409        # must start with 'traffic'
    for stage in ("traffic", "detection", "crypto", "healing", "final"):
        r = client.post(f"/api/simulation/{stage}", json=cfg)
        assert r.status_code == 200, stage
        fc.check("stage_result", r.json())
        assert r.json()["stageId"] == stage
    assert client.get("/api/stats").json()["isolations"] >= 1                           # real commands were issued


def test_simulation_hndl_scenario_is_caught_by_bb84(client):
    cfg = {"scenario": "hndl", "intensity": 100, "nodes": 8}
    client.post("/api/simulation/traffic", json=cfg)
    out = client.post("/api/simulation/healing", json=cfg).json()
    assert "No node isolated" in out["headline"]
    assert client.get("/api/stats").json()["eavesdrop_aborts"] >= 1


def test_simulation_input_is_validated(client):
    assert client.post("/api/simulation/traffic", json={"scenario": "nope", "intensity": 5, "nodes": 5}).status_code == 422
    assert client.post("/api/simulation/traffic", json={"scenario": "ddos", "intensity": 5, "nodes": 0}).status_code == 422
    assert client.post("/api/simulation/bogus", json={"scenario": "ddos", "intensity": 5, "nodes": 5}).status_code == 422


def test_dashboard_endpoints_need_the_api_key(monkeypatch, client):
    from app import config
    monkeypatch.setattr(config, "API_KEY", "secret")
    for path in DASHBOARD_ROUTES.values():
        assert client.get(path).status_code == 401
        assert client.get(path, headers={"X-API-Key": "secret"}).status_code == 200
    cfg = {"scenario": "ddos", "intensity": 10, "nodes": 4}
    assert client.post("/api/simulation/traffic", json=cfg).status_code == 401
