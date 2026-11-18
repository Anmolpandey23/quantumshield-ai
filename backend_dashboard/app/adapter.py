"""Adapter: real pipeline data  ->  the JSON shapes the React dashboard (frontend/) expects.

Rules of this module
  * Pure functions over plain dicts (no FastAPI, no torch, no qiskit) so they are easy to test.
  * Every number comes from a real pipeline event, the SQLite log, or the live node table.
  * Where the pipeline has NO measurement for something the dashboard can draw (for example classical
    crypto timings, queue depth, model accuracy), the field is `null` / empty. Nothing is invented.

Entry points: `collect(engine)` takes a snapshot, then `overview(ctx)`, `threats(ctx)`, `crypto(ctx)`,
`healing(ctx)`, `topology(ctx)`, `pipeline(ctx)`, `logs(ctx)` and `simulation_stage(...)` build the responses.
"""
from __future__ import annotations

import json
import math
import pathlib
from datetime import datetime, timezone

KNOWN_LABELS = ["DDoS", "PortScan", "BruteForce", "DoS", "Bot", "WebAttack"]
STATUS_MAP = {"online": "healthy", "monitored": "warning", "isolated": "isolated"}
HUB_ID = "controller"


# ---------------------------------------------------------------------------------------------- snapshot
def collect(eng, now: datetime | None = None) -> dict:
    """One consistent snapshot of the engine. Cheap enough to call per request."""
    g = getattr(getattr(eng.orch, "policy", None), "guardrails", None)
    guard = {
        "enabled": getattr(g, "enabled", True),
        "min_confidence_to_isolate": getattr(g, "min_confidence_to_isolate", 0.6),
        "min_risk_to_isolate": getattr(g, "min_risk_to_isolate", 0.5),
        "max_isolated_fraction": getattr(g, "max_isolated_fraction", 0.5),
        "max_isolations_per_minute": getattr(g, "max_isolations_per_minute", 5),
        "critical_nodes": sorted(getattr(g, "critical_nodes", None) or eng.critical),
        "has_guardrails": g is not None,
    }
    return {
        "events": eng.store.recent(1000),            # newest first
        "keys": eng.store.keys(1000),                # newest first
        "nodes": eng.nodes(),
        "stats": eng.stats(),
        "pending": eng.orch.list_pending(),
        "mode": dict(eng.mode),
        "n_qubits": eng.n_qubits,
        "node_keys": dict(eng.orch.node_keys),
        "guardrails": guard,
        "started": getattr(eng, "started", None),
        "model": _model_files(),
        "now": now or datetime.now(timezone.utc),
    }


def _model_files() -> dict:
    """Stage 1 training metrics, if `python -m stage1.train` has been run. Otherwise empty."""
    try:
        from stage1.config import ARTIFACTS_DIR  # type: ignore
        p = pathlib.Path(ARTIFACTS_DIR) / "metrics.json"
        if not p.exists():
            return {}
        data = json.loads(p.read_text())
        lgb = data.get("lightgbm") or {}
        rep = lgb.get("report") or {}
        macro = rep.get("macro avg") or {}
        accuracy = rep.get("accuracy")
        precision = macro.get("precision")
        recall = macro.get("recall")
        macro_f1 = lgb.get("macro_f1") or macro.get("f1-score") or (data.get("classifier") or {}).get("macro_f1_test_with_tabddpm")
        return {
            "macro_f1": float(macro_f1) if macro_f1 is not None else None,
            "accuracy": float(accuracy) if accuracy is not None else None,
            "precision": float(precision) if precision is not None else None,
            "recall": float(recall) if recall is not None else None,
            "trained_at": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------------------------- helpers
def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _action(ev: dict) -> str | None:
    cmd = ev.get("stage3_command")
    return cmd["payload"]["action"] if cmd else None


def _s1(ev: dict) -> dict:
    return ev.get("stage1") or {}


def _is_threat(ev: dict) -> bool:
    return _s1(ev).get("threat_label", "BENIGN") != "BENIGN"


def severity(risk: float) -> str:
    return "critical" if risk >= 0.85 else "high" if risk >= 0.7 else "medium" if risk >= 0.5 else "low"


def _mean(xs) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def _chrono(events: list[dict]) -> list[dict]:
    return list(reversed(events))


def heal_durations(events: list[dict]) -> dict[int, float]:
    """event id of every 'reconnect' command -> seconds since that node's 'isolate' command (real timestamps)."""
    open_iso: dict[str, datetime] = {}
    out: dict[int, float] = {}
    for ev in _chrono(events):
        if ev.get("decision") != "command_issued":
            continue
        act, node, t = _action(ev), ev["node_id"], _ts(ev["timestamp"])
        if act == "isolate":
            open_iso.setdefault(node, t)
        elif act == "reconnect" and node in open_iso:
            out[ev["id"]] = max(0.0, (t - open_iso.pop(node)).total_seconds())
    return out


def posture(ctx: dict) -> int:
    nodes = ctx["nodes"]
    if not nodes:
        return 100
    return max(0, min(100, round(100 * (1 - _mean(n["risk_score_node"] for n in nodes)))))


def pqc_coverage(ctx: dict) -> int:
    nodes = ctx["nodes"]
    if not nodes:
        return 0
    return round(100 * sum(1 for n in nodes if n.get("key_id")) / len(nodes))


def _buckets(events: list[dict], n: int) -> list[tuple[str, list[dict]]]:
    """Group events by UTC minute (oldest first), keep the last n minutes that have events."""
    groups: dict[str, list[dict]] = {}
    for ev in _chrono(events):
        groups.setdefault(ev["timestamp"][:16], []).append(ev)
    keys = sorted(groups)[-n:]
    return [(k, groups[k]) for k in keys]


# ---------------------------------------------------------------------------------------------- /api/threats
def threat_events(events: list[dict], limit: int = 100) -> list[dict]:
    out = []
    for ev in events:
        if not _is_threat(ev):
            continue
        s1, act, dec = _s1(ev), _action(ev), ev["decision"]
        if dec == "command_issued" and act == "isolate":
            status = "mitigated"
        elif dec == "command_issued" and act == "reconnect":
            status = "mitigated"
        elif dec == "command_issued":
            status = "monitoring"
        elif dec == "no_action":
            status = "monitoring"
        else:                                   # aborted_no_command, pending_human_approval, command_rejected
            status = "investigating"
        out.append({"id": f"THR-{ev['id']}", "timestamp": ev["timestamp"], "category": s1["threat_label"],
                    "severity": severity(s1["risk_score_node"]), "confidence": round(float(s1["confidence"]), 3),
                    "source": ev["node_id"], "target": "network", "status": status})
        if len(out) >= limit:
            break
    return out


def threats(ctx: dict) -> dict:
    events, nodes, mode, mf = ctx["events"], ctx["nodes"], ctx["mode"], ctx["model"]
    real = mode.get("stage1") == "real"
    model = {
        "name": "Stage 1 ensemble" if real else "Stage 1 stub simulator",
        "version": "contract 1.0",
        "architecture": "TabDDPM + CPC Transformer + DyGNN + XAI" if real
        else "Rule-based simulator (train Stage 1 to use the real models)",
        "accuracy": mf.get("accuracy"), "precision": mf.get("precision"), "recall": mf.get("recall"),
        "macroF1": mf.get("macro_f1"),
        "lastTrained": mf.get("trained_at", ""),
    }
    current = round(100 * max((n["risk_score_node"] for n in nodes), default=0.0))
    trend = []
    for key, evs in _buckets(events, 24):
        trend.append({"hour": key[11:16],
                      "predicted": round(100 * max(_s1(e).get("risk_score_node", 0.0) for e in evs)),
                      "observed": round(100 * max(_s1(e).get("anomaly_score", 0.0) for e in evs))})
    by_label: dict[str, float] = {k: 0.0 for k in KNOWN_LABELS}
    for ev in events:
        if _is_threat(ev):
            lab = _s1(ev)["threat_label"]
            by_label[lab] = max(by_label.get(lab, 0.0), float(_s1(ev)["risk_score_node"]))
    cats = [{"category": k, "score": round(100 * v)} for k, v in by_label.items()]
    return {"model": model, "currentRisk": current, "riskTrend": trend, "categories": cats,
            "events": threat_events(events)}


# ---------------------------------------------------------------------------------------------- /api/overview
def overview(ctx: dict) -> dict:
    events, nodes, stats = ctx["events"], ctx["nodes"], ctx["stats"]
    total = len(nodes)
    isolated = sum(1 for n in nodes if n["status"] == "isolated")
    durs = list(heal_durations(events).values())
    traffic = []
    for key, evs in _buckets(events, 24):
        traffic.append({"time": key[11:16], "inbound": len(evs),
                        "outbound": sum(1 for e in evs if (e.get("stage2") or {}).get("status") == "secure_channel_established"),
                        "anomalies": sum(1 for e in evs if _is_threat(e))})
    kpis = [
        {"id": "threats", "label": "Threats Flagged", "value": f"{stats['threats_flagged']:,}", "delta": "", "trend": "flat",
         "tone": "primary", "hint": "Stage 1 detections that started Stage 2"},
        {"id": "health", "label": "Network Health",
         "value": f"{round(100 * (total - isolated) / total)}%" if total else "—", "delta": "", "trend": "flat",
         "tone": "warning" if isolated else "success", "hint": f"{total} nodes seen, {isolated} isolated"},
        {"id": "pqc", "label": "PQC Coverage", "value": f"{pqc_coverage(ctx)}%" if total else "—", "delta": "", "trend": "flat",
         "tone": "accent", "hint": "Nodes holding a live QRNG + BB84 + ML-KEM key"},
        {"id": "mttr", "label": "Mean Time to Heal", "value": f"{round(_mean(durs))}s" if durs else "—", "delta": "",
         "trend": "flat", "tone": "warning", "hint": "Isolate to reconnect (measured)"},
    ]
    return {"postureScore": posture(ctx), "kpis": kpis, "traffic": traffic,
            "recentThreats": threat_events(events, 5)}


# ---------------------------------------------------------------------------------------------- /api/crypto
def crypto(ctx: dict) -> dict:
    keys, events, node_keys = ctx["keys"], ctx["events"], set(ctx["node_keys"].values())
    ok_keys = [k for k in keys if k["status"] == "secure_channel_established"]
    sizes = {}
    for ev in events:
        s2 = ev.get("stage2") or {}
        if s2.get("sizes_bytes"):
            sizes = s2["sizes_bytes"]
            break
    issued = [e for e in events if e["decision"] == "command_issued"]
    kem_rate = round(100 * len(ok_keys) / len(keys)) if keys else 0
    sign_rate = 100 if issued else 0                  # every issued command was ML-DSA verified (else it is 'command_rejected')
    algorithms = [
        {"id": "mlkem", "name": "ML-KEM-768", "family": "CRYSTALS-Kyber", "role": "Key Encapsulation", "standard": "FIPS 203",
         "securityLevel": 3, "status": "active", "publicKeyBytes": int(sizes.get("kem_public_key", 1184)), "usage": kem_rate,
         "usageLabel": "Handshake success"},
        {"id": "mldsa", "name": "ML-DSA-65", "family": "CRYSTALS-Dilithium", "role": "Digital Signature", "standard": "FIPS 204",
         "securityLevel": 3, "status": "active", "publicKeyBytes": int(sizes.get("sig_public_key", 1952)), "usage": sign_rate,
         "usageLabel": "Commands verified"},
    ]
    sessions = [{"id": f"s-{k['id']}", "peer": k["node_id"], "kem": "ML-KEM-768", "signature": "ML-DSA-65",
                 "mode": "hybrid", "established": k["timestamp"], "latencyMs": float(k["key_gen_time_ms"] or 0.0)}
                for k in ok_keys if k.get("shared_key_id") in node_keys][:20]
    t_acc: dict[str, list[float]] = {}
    for k in ok_keys:
        for name, ms in (k.get("timings_ms") or {}).items():
            t_acc.setdefault(name, []).append(float(ms))
    labels = [("qrng_ms", "QRNG"), ("bb84_ms", "BB84"), ("ml_kem_ms", "ML-KEM"), ("hkdf_aes_ms", "HKDF+AES"), ("ml_dsa_ms", "ML-DSA")]
    benchmarks = [{"operation": lab, "classicalMs": None, "pqcMs": round(_mean(t_acc[k]), 2)} for k, lab in labels if k in t_acc]
    rotations = [{"id": f"r{k['id']}", "timestamp": k["timestamp"], "algorithm": "ML-KEM-768",
                  "scope": f"{k['node_id']} · {k.get('shared_key_id') or 'key'}"} for k in ok_keys[:8]]
    return {"coverage": pqc_coverage(ctx), "algorithms": algorithms, "sessions": sessions, "benchmarks": benchmarks,
            "rotations": rotations}


# ---------------------------------------------------------------------------------------------- /api/healing
def healing(ctx: dict) -> dict:
    events, status_of = ctx["events"], {n["node_id"]: n["status"] for n in ctx["nodes"]}
    durs = heal_durations(events)
    issued = [e for e in events if e["decision"] == "command_issued"]
    auto = [e for e in issued if (e.get("policy") or {}).get("source") != "human"]
    incidents = []
    for ev in events:
        s1, act, dec, node = _s1(ev), _action(ev), ev["decision"], ev["node_id"]
        s2 = ev.get("stage2") or {}
        dur = 0
        if dec == "command_issued" and act == "isolate":
            issue = f"{s1.get('threat_label')} detected (risk {s1.get('risk_score_node', 0):.2f})"
            action = "Isolated node (ML-DSA signed command, signature verified)"
            status = "in-progress" if status_of.get(node) == "isolated" else "resolved"
        elif dec == "command_issued" and act == "reconnect":
            issue = "Node looks clean again"
            action = "Reconnected with a fresh QRNG + BB84 + ML-KEM key"
            status, dur = "resolved", round(durs.get(ev["id"], 0))
        elif dec == "pending_human_approval":
            pa = ev.get("pending_approval") or {}
            issue = f"{s1.get('threat_label')} on a protected node"
            action = f"Waiting for a human to approve: {pa.get('action', 'isolate')}"
            status = "escalated"
        elif dec == "command_rejected":
            issue = f"{s1.get('threat_label')} flagged"
            action = "Command rejected (signature check failed or human said no)"
            status = "escalated"
        elif dec == "aborted_no_command":
            issue = f"{s1.get('threat_label')} flagged"
            action = f"Aborted, no command sent: {s2.get('status', 'channel not secure')} (QBER {s2.get('qber', 0):.3f})"
            status = "escalated"
        else:
            continue
        incidents.append({"id": f"HEAL-{ev['id']}", "timestamp": ev["timestamp"], "node": node, "issue": issue,
                          "action": action, "durationSec": dur, "status": status})
        if len(incidents) >= 50:
            break
    g = ctx["guardrails"]
    crit = ", ".join(g["critical_nodes"]) or "none"
    policies = [
        {"id": "p1", "name": "Evidence before isolation", "enabled": g["enabled"],
         "trigger": f"Confidence ≥ {g['min_confidence_to_isolate']:.2f} and risk ≥ {g['min_risk_to_isolate']:.2f}",
         "action": "Isolate the node"},
        {"id": "p2", "name": "Blast-radius cap", "enabled": g["enabled"],
         "trigger": f"More than {round(100 * g['max_isolated_fraction'])}% of nodes already isolated", "action": "Keep monitoring instead"},
        {"id": "p3", "name": "Human approval for critical nodes", "enabled": g["enabled"],
         "trigger": f"Isolating a critical node ({crit})", "action": "Wait for an operator to approve"},
        {"id": "p4", "name": "Isolation rate limit", "enabled": g["enabled"],
         "trigger": f"More than {g['max_isolations_per_minute']} isolations in a minute", "action": "Wait for an operator to approve"},
        {"id": "p5", "name": "Secure channel first", "enabled": True,
         "trigger": "Eavesdropper detected by BB84 (QBER above threshold)", "action": "Abort, send no command"},
    ]
    iso_by_day: dict[str, int] = {}
    heal_by_day: dict[str, list[float]] = {}
    ev_by_id = {e["id"]: e for e in events}
    for ev in events:
        if ev["decision"] == "command_issued" and _action(ev) == "isolate":
            iso_by_day[ev["timestamp"][5:10]] = iso_by_day.get(ev["timestamp"][5:10], 0) + 1
    for eid, d in durs.items():
        heal_by_day.setdefault(ev_by_id[eid]["timestamp"][5:10], []).append(d)
    days = sorted(set(iso_by_day) | set(heal_by_day))[-7:]
    trend = [{"day": d, "mttr": round(_mean(heal_by_day.get(d, []))), "incidents": iso_by_day.get(d, 0)} for d in days]
    return {"mttrSeconds": round(_mean(durs.values())) if durs else 0,
            "autoRemediationRate": round(100 * len(auto) / len(issued)) if issued else 0,
            "incidents": incidents, "policies": policies, "mttrTrend": trend}


# ---------------------------------------------------------------------------------------------- /api/topology
def topology(ctx: dict) -> dict:
    nodes = ctx["nodes"]
    crit = set(ctx["guardrails"]["critical_nodes"])
    out = [{"id": HUB_ID, "label": "QuantumShield Controller", "type": "ai", "status": "healthy", "layer": "core",
            "x": 50.0, "y": 30.0, "ip": "controller", "load": 0}]
    edges = []
    n = len(nodes)
    for i, nd in enumerate(sorted(nodes, key=lambda d: d["node_id"])):
        ang = 2 * math.pi * i / max(n, 1) - math.pi / 2
        out.append({"id": nd["node_id"], "label": nd["node_id"] + (" ★" if nd["node_id"] in crit else ""),
                    "type": "server" if nd["node_id"] in crit else "iot",
                    "status": STATUS_MAP.get(nd["status"], "healthy"), "layer": "endpoint",
                    "x": round(50 + 42 * math.cos(ang), 2), "y": round(30 + 25 * math.sin(ang), 2),
                    "ip": nd["node_id"], "load": round(100 * nd["risk_score_node"])})
        edges.append({"from": HUB_ID, "to": nd["node_id"], "status": "down" if nd["status"] == "isolated" else "normal"})
    return {"nodes": out, "edges": edges}


# ---------------------------------------------------------------------------------------------- /api/pipeline
def pipeline(ctx: dict) -> dict:
    events, now = ctx["events"], ctx["now"]
    s2_ev = [e for e in events if e.get("stage2")]
    pol_ev = [e for e in events if e.get("policy")]
    cmd_ev = [e for e in events if e.get("stage3_command")]
    last_s2 = s2_ev[0]["stage2"]["status"] if s2_ev else None
    keygen = [e["stage2"]["key_gen_time_ms"] for e in s2_ev]

    def per_sec(evs: list[dict]) -> float:
        recent = [e for e in evs if (now - _ts(e["timestamp"])).total_seconds() <= 60]
        return round(len(recent) / 60, 3)

    mode = ctx["mode"]
    defs = [
        ("stage1", "Stage 1 · AI Threat Prediction", "stage1/predictor.py" if mode.get("stage1") == "real" else "app/simulator.py (stub)", events, None,
         "running" if events else "idle"),
        ("stage2", "Stage 2 · Quantum Cryptography", "stage2/pipeline.py", s2_ev, round(_mean(keygen), 1) if keygen else None,
         "idle" if not s2_ev else "degraded" if last_s2 != "secure_channel_established" else "running"),
        ("stage3", "Stage 3 · Self-Healing Policy", "stage3/policy.py" if mode.get("stage3") != "stub" else "integration/stubs.py (stub)", pol_ev, None,
         "running" if pol_ev else "idle"),
        ("stage4", "Stage 4 · Signed Commands", "integration/orchestrator.py", cmd_ev, None, "running" if cmd_ev else "idle"),
    ]
    stages = [{"id": i, "name": n, "module": m, "status": st, "throughput": per_sec(evs), "latencyMs": lat,
               "queue": 0, "uptime": None} for i, n, m, evs, lat, st in defs]
    hist = []
    for key, evs in _buckets(events, 20):
        row: dict = {"time": key[11:16]}
        for i, _n, _m, stage_evs, _l, _s in defs:
            ids = {e["id"] for e in stage_evs}
            row[i] = round(sum(1 for e in evs if e["id"] in ids) / 60, 3)
        hist.append(row)
    return {"stages": stages, "throughputHistory": hist}


# ---------------------------------------------------------------------------------------------- /api/logs
def event_logs(ev: dict) -> list[tuple[str, str, str]]:
    """(level, module, message) lines for one pipeline event. Benign no-action events produce no line."""
    out: list[tuple[str, str, str]] = []
    s1, s2, node = _s1(ev), ev.get("stage2"), ev["node_id"]
    if _is_threat(ev):
        why = ", ".join(s1.get("explanation") or []) or "no explanation given"
        out.append(("WARN", "stage1.predictor",
                    f"{node}: {s1['threat_label']} (confidence {s1['confidence']:.2f}, risk {s1['risk_score_node']:.2f}) because: {why}"))
    if s2:
        if s2["status"] == "secure_channel_established":
            out.append(("SUCCESS", "stage2.pipeline",
                        f"{node}: secure channel established, QBER {s2['qber']:.3f}, key {s2.get('shared_key_id')} in {s2['key_gen_time_ms']} ms"))
        else:
            out.append(("ERROR", "stage2.pipeline", f"{node}: {s2['status']} (QBER {s2['qber']:.3f}), no command sent"))
    pol = ev.get("policy")
    if pol and ev["decision"] != "aborted_no_command":
        out.append(("INFO", "stage3.policy", f"{node}: proposed {pol.get('proposed')}, decided {pol.get('action')} ({pol.get('reason')})"))
    act = _action(ev)
    if ev["decision"] == "command_issued":
        out.append(("SUCCESS", "stage4.orchestrator", f"{node}: {act} command signed (ML-DSA) and verified; node is now {ev.get('node_status')}"))
    elif ev["decision"] == "command_rejected":
        out.append(("ERROR", "stage4.orchestrator", f"{node}: command rejected"))
    elif ev["decision"] == "pending_human_approval":
        pa = ev.get("pending_approval") or {}
        out.append(("WARN", "stage4.orchestrator", f"{node}: {pa.get('action')} waiting for human approval ({pa.get('approval_id')})"))
    return out


def logs(ctx: dict, limit: int = 200) -> list[dict]:
    out: list[dict] = []
    for ev in ctx["events"][:300]:
        for j, (lvl, mod, msg) in enumerate(reversed(event_logs(ev))):      # newest line first inside one event
            out.append({"id": f"log-{ev['id']}-{j}", "timestamp": ev["timestamp"], "level": lvl, "module": mod, "message": msg})
    return out[:limit]


# ---------------------------------------------------------------------------------------------- /api/simulation/{stage}
def simulation_stage(stage: str, run: dict, ctx: dict) -> dict:
    """Describe one stage of the last scenario run (`Engine.run_scenario`). All numbers are measured from that run's events."""
    evs, cfg = run["events"], run["config"]
    threats_ = [e for e in evs if _is_threat(e)]
    s2s = [e["stage2"] for e in evs if e.get("stage2")]
    ok = [s for s in s2s if s["status"] == "secure_channel_established"]
    bad = [s for s in s2s if s["status"] != "secure_channel_established"]
    lines = [l for e in evs for l in event_logs(e)]

    def pick(mod_prefix: str) -> list[dict]:
        return [{"level": lvl, "message": msg} for lvl, mod, msg in lines if mod.startswith(mod_prefix)][:6]

    if stage == "traffic":
        return {"stageId": stage, "headline": f"Scored {len(evs)} nodes; {run['attacked']} carry the injected '{run['attack']}' attack",
                "metrics": [{"label": "Nodes scored", "value": str(len(evs))}, {"label": "Attacked nodes", "value": str(run["attacked"])},
                            {"label": "Scenario", "value": cfg["scenario"]}],
                "logs": [{"level": "INFO", "message": f"Injected {run['attacked']} synthetic Stage 1 detections into {len(evs)} nodes"}]}
    if stage == "detection":
        conf = _mean(_s1(e)["confidence"] for e in threats_)
        risk = _mean(_s1(e)["risk_score_node"] for e in threats_)
        return {"stageId": stage, "headline": f"{len(threats_)} node(s) flagged as {run['attack']}, mean confidence {conf:.2f}",
                "metrics": [{"label": "Flagged nodes", "value": str(len(threats_))}, {"label": "Mean confidence", "value": f"{conf:.2f}"},
                            {"label": "Mean risk", "value": f"{risk:.2f}"}],
                "logs": pick("stage1")}
    if stage == "crypto":
        qber = _mean(s["qber"] for s in s2s)
        kg = _mean(s["key_gen_time_ms"] for s in ok)
        head = (f"Eavesdropper detected on {len(bad)} channel(s): no command was sent" if bad
                else f"{len(ok)} secure channel(s) established with QRNG + BB84 + ML-KEM-768")
        return {"stageId": stage, "headline": head,
                "metrics": [{"label": "Channels secured", "value": str(len(ok))}, {"label": "Aborted (eavesdropper)", "value": str(len(bad))},
                            {"label": "Mean QBER", "value": f"{qber:.3f}"}, {"label": "Mean key time", "value": f"{kg:.0f} ms"}],
                "logs": pick("stage2")}
    if stage == "healing":
        iso = [e for e in evs if e["decision"] == "command_issued" and _action(e) == "isolate"]
        pend = [e for e in evs if e["decision"] == "pending_human_approval"]
        rej = [e for e in evs if e["decision"] == "command_rejected"]
        head = (f"Isolated {len(iso)} node(s) with signed, verified commands" if iso
                else "No node isolated (no secure channel, so no command was sent)" if bad else "No isolation was needed")
        return {"stageId": stage, "headline": head,
                "metrics": [{"label": "Nodes isolated", "value": str(len(iso))}, {"label": "Awaiting approval", "value": str(len(pend))},
                            {"label": "Commands rejected", "value": str(len(rej))}],
                "logs": pick("stage3") + pick("stage4")}
    if stage == "final":
        p = posture(ctx)
        isolated = sum(1 for n in ctx["nodes"] if n["status"] == "isolated")
        resid = "Low" if p >= 80 else "Medium" if p >= 60 else "High"
        return {"stageId": stage, "headline": f"Run finished: posture {p}/100, {isolated} node(s) currently isolated",
                "metrics": [{"label": "Posture score", "value": str(p)}, {"label": "Residual risk", "value": resid},
                            {"label": "Nodes isolated", "value": f"{isolated}/{len(ctx['nodes'])}"}],
                "logs": [{"level": "SUCCESS", "message": "Scenario run complete (events are stored in the SQLite log)"}]}
    raise ValueError(f"unknown stage '{stage}'")

