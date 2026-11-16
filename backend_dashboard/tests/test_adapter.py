"""Adapter tests. Pure Python: no FastAPI, torch or qiskit needed (events are built by hand to match contracts/pipeline_event)."""
import json
import pathlib
import re
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from app import adapter                      # noqa: E402
import frontend_contract as fc               # noqa: E402

T0 = datetime(2026, 11, 16, 9, 0, 0, tzinfo=timezone.utc)
_ids = iter(range(1, 10_000))


def s1(node, label="DDoS", conf=0.94, anom=0.87, risk=0.91):
    return {"contract_version": "1.0", "node_id": node, "threat_label": label, "confidence": conf, "anomaly_score": anom,
            "risk_score_node": risk, "explanation": ["unusual packet rate"] if label != "BENIGN" else []}


_keyn = iter(range(1, 10_000))


def s2_ok(node, qber=0.01, ms=210.5):
    return {"node_id": node, "status": "secure_channel_established", "eavesdrop_detected": False, "qber": qber, "key_gen_time_ms": ms,
            "shared_key_id": f"key_{node}_{next(_keyn):08x}", "timings_ms": {"qrng_ms": 40.0, "bb84_ms": 120.0, "ml_kem_ms": 30.0, "hkdf_aes_ms": 1.0, "ml_dsa_ms": 19.5},
            "sizes_bytes": {"kem_public_key": 1184, "kem_ciphertext": 1088, "sig_public_key": 1952, "signature": 3309}}


def s2_eve(node):
    return {"node_id": node, "status": "aborted_eavesdrop_detected", "eavesdrop_detected": True, "qber": 0.25, "key_gen_time_ms": 150.0,
            "reason": "eavesdropper", "timings_ms": {"qrng_ms": 40.0, "bb84_ms": 110.0}}


def ev(minutes, node, decision, stage1, stage2=None, action=None, status="online", **extra):
    e = {"id": next(_ids), "contract_version": "1.0", "timestamp": (T0 + timedelta(minutes=minutes)).isoformat(), "node_id": node,
         "decision": decision, "stage1": stage1, "stage2": stage2,
         "stage3_command": {"payload": {"node_id": node, "action": action, "issued_at": 1.0, "nonce": "0" * 32}, "signature": "ab"} if action else None,
         "command_verified": True if action else None, "node_status": status}
    e.update(extra)
    return e


def ctx(events_chrono, nodes, node_keys=None, mode=None):
    return {"events": list(reversed(events_chrono)), "keys": [], "nodes": nodes, "stats": {"threats_flagged": 0},
            "pending": [], "mode": mode or {"stage1": "stub", "stage3": "stub"}, "n_qubits": 1024, "node_keys": node_keys or {},
            "guardrails": {"enabled": True, "min_confidence_to_isolate": 0.6, "min_risk_to_isolate": 0.5, "max_isolated_fraction": 0.5,
                           "max_isolations_per_minute": 5, "critical_nodes": ["10.0.0.2"], "has_guardrails": True},
            "started": None, "model": {}, "now": T0 + timedelta(minutes=30)}


def with_keys(c):
    c["keys"] = [{"id": e["id"], "timestamp": e["timestamp"], "node_id": e["node_id"], "status": e["stage2"]["status"], "qber": e["stage2"]["qber"],
                  "key_gen_time_ms": e["stage2"]["key_gen_time_ms"], "eavesdrop_detected": e["stage2"]["eavesdrop_detected"],
                  "shared_key_id": e["stage2"].get("shared_key_id"), "timings_ms": e["stage2"].get("timings_ms")}
                 for e in c["events"] if e.get("stage2")]
    c["stats"] = {"threats_flagged": len([e for e in c["events"] if e.get("stage2")])}
    return c


def node(n, status, risk, key=None, critical=False):
    return {"node_id": n, "status": status, "threat_label": "BENIGN", "risk_score_node": risk, "confidence": 0.9, "anomaly_score": 0.1,
            "explanation": [], "key_id": key, "critical": critical, "last_seen": T0.isoformat()}


def scenario():
    """node A: attacked, isolated, later reconnected.  node B: eavesdropper caught.  node C: benign."""
    A, B, C = "10.0.0.5", "10.0.0.6", "10.0.0.7"
    events = [
        ev(0, C, "no_action", s1(C, "BENIGN", 0.98, 0.04, 0.05)),
        ev(1, A, "command_issued", s1(A), s2_ok(A), "isolate", "isolated", policy={"action": "isolate", "source": "ppo", "proposed": "isolate", "reason": "ok", "requires_approval": False}),
        ev(2, B, "aborted_no_command", s1(B, "PortScan", 0.9, 0.8, 0.8), s2_eve(B)),
        ev(3, A, "command_issued", s1(A, "BENIGN", 0.98, 0.03, 0.04), s2_ok(A, 0.02, 180.0), "reconnect", "online", rekeyed=True,
           policy={"action": "reconnect", "source": "ppo", "proposed": "reconnect", "reason": "ok", "requires_approval": False}),
    ]
    cur = events[3]["stage2"]["shared_key_id"]                    # the key from the reconnect handshake is the live one
    nodes = [node(A, "online", 0.04, cur), node(B, "online", 0.8), node(C, "online", 0.05)]
    return with_keys(ctx(events, nodes, {A: cur}))


def test_every_response_matches_the_typescript_types():
    c = scenario()
    for name, fn in [("overview", adapter.overview), ("threats", adapter.threats), ("crypto", adapter.crypto), ("healing", adapter.healing),
                     ("topology", adapter.topology), ("pipeline", adapter.pipeline), ("logs", adapter.logs)]:
        out = fn(c)
        fc.check(name, out)
        json.dumps(out, allow_nan=False)          # strict JSON: no NaN / Infinity


def test_empty_system_is_valid_and_honest():
    c = ctx([], [])
    for name, fn in [("overview", adapter.overview), ("threats", adapter.threats), ("crypto", adapter.crypto), ("healing", adapter.healing),
                     ("topology", adapter.topology), ("pipeline", adapter.pipeline), ("logs", adapter.logs)]:
        out = fn(c)
        fc.check(name, out)
        json.dumps(out, allow_nan=False)
    assert adapter.overview(c)["postureScore"] == 100 and adapter.overview(c)["kpis"][3]["value"] == "—"
    assert adapter.topology(c)["edges"] == [] and adapter.healing(c)["mttrSeconds"] == 0


def test_mttr_is_measured_from_timestamps_not_invented():
    c = scenario()
    assert adapter.healing(c)["mttrSeconds"] == 120           # isolate at minute 1, reconnect at minute 3
    assert adapter.overview(c)["kpis"][3]["value"] == "120s"
    inc = {i["action"][:9]: i for i in adapter.healing(c)["incidents"]}
    assert inc["Reconnect"]["durationSec"] == 120 and inc["Reconnect"]["status"] == "resolved"


def test_eavesdropper_abort_is_reported_as_escalated_and_logged_as_error():
    c = scenario()
    inc = [i for i in adapter.healing(c)["incidents"] if i["node"] == "10.0.0.6"][0]
    assert inc["status"] == "escalated" and "no command sent" in inc["action"]
    assert any(l["level"] == "ERROR" and "aborted_eavesdrop_detected" in l["message"] for l in adapter.logs(c))


def test_threat_events_severity_and_status():
    c = scenario()
    t = {e["source"]: e for e in adapter.threats(c)["events"] if e["category"] != "x"}
    assert any(e["severity"] == "critical" for e in adapter.threats(c)["events"])
    assert [e for e in adapter.threats(c)["events"] if e["category"] == "PortScan"][0]["status"] == "investigating"
    assert all(e["id"].startswith("THR-") for e in t.values())


def test_no_fake_numbers_where_pipeline_has_no_measurement():
    c = scenario()
    m = adapter.threats(c)["model"]
    assert m["accuracy"] is None and m["precision"] is None and m["recall"] is None
    assert all(b["classicalMs"] is None for b in adapter.crypto(c)["benchmarks"])
    assert all(s["uptime"] is None for s in adapter.pipeline(c)["stages"])


def test_crypto_sessions_only_for_nodes_that_hold_the_current_key():
    c = scenario()
    sess = adapter.crypto(c)["sessions"]
    assert [s["peer"] for s in sess] == ["10.0.0.5"] and sess[0]["kem"] == "ML-KEM-768"
    assert adapter.crypto(c)["coverage"] == 33              # 1 of 3 nodes holds a key
    assert adapter.crypto(c)["algorithms"][0]["publicKeyBytes"] == 1184


def test_topology_has_one_node_per_machine_plus_controller_and_marks_isolated_links_down():
    c = scenario()
    c["nodes"][0]["status"] = "isolated"
    t = adapter.topology(c)
    assert len(t["nodes"]) == 4 and {e["to"] for e in t["edges"]} == {"10.0.0.5", "10.0.0.6", "10.0.0.7"}
    assert [e for e in t["edges"] if e["to"] == "10.0.0.5"][0]["status"] == "down"
    assert [n for n in t["nodes"] if n["id"] == "10.0.0.5"][0]["status"] == "isolated"


def test_simulation_stages_report_the_run():
    c = scenario()
    run = {"config": {"scenario": "ddos", "intensity": 60, "nodes": 3}, "attack": "DDoS", "attacked": 2, "events": list(reversed(c["events"]))[:3]}
    for st in ["traffic", "detection", "crypto", "healing", "final"]:
        fc.check("stage_result", adapter.simulation_stage(st, run, c))
    assert "Eavesdropper" in adapter.simulation_stage("crypto", run, c)["headline"]


def test_python_contract_mirrors_ts_field_names():
    ts = (pathlib.Path(__file__).resolve().parents[2] / "frontend/src/types/quantumshield.ts").read_text()
    if not ts:
        return
    for field in ["postureScore", "recentThreats", "currentRisk", "riskTrend", "autoRemediationRate", "mttrTrend", "throughputHistory",
                  "publicKeyBytes", "usageLabel", "macroF1", "durationSec", "latencyMs"]:
        assert re.search(rf"\b{field}\b", ts), f"{field} missing from quantumshield.ts"
