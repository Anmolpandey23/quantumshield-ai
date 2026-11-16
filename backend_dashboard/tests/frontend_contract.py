"""Python mirror of frontend/src/types/quantumshield.ts.

`check(name, payload)` raises AssertionError when a backend response would not satisfy the TypeScript type the
dashboard reads it with. Keep this file in sync with the .ts types (a test compares the field names).
"""
from __future__ import annotations

import math

NUM = (int, float)
TONES = {"primary", "accent", "success", "warning", "danger", "muted"}
SEV = {"critical", "high", "medium", "low"}
LOGLEVELS = {"DEBUG", "INFO", "SUCCESS", "WARN", "ERROR"}


def _num(v, nullable=False):
    if v is None:
        assert nullable, "null where a number is required"
        return
    assert isinstance(v, NUM) and not isinstance(v, bool), f"not a number: {v!r}"
    assert math.isfinite(v), "NaN/inf is not valid JSON"


def _str(v):
    assert isinstance(v, str), f"not a string: {v!r}"


def _enum(v, allowed):
    assert v in allowed, f"{v!r} not in {sorted(allowed)}"


def _obj(v, spec: dict, optional: dict | None = None):
    assert isinstance(v, dict), f"not an object: {v!r}"
    for k, fn in spec.items():
        assert k in v, f"missing field '{k}'"
        fn(v[k])
    for k, fn in (optional or {}).items():
        if k in v:
            fn(v[k])


def _list(fn):
    def run(v):
        assert isinstance(v, list), f"not a list: {v!r}"
        for x in v:
            fn(x)
    return run


def _opt(fn):
    return lambda v: None if v is None else fn(v)


def _is(allowed):
    return lambda v: _enum(v, allowed)


def threat_event(v):
    _obj(v, {"id": _str, "timestamp": _str, "category": _str, "severity": _is(SEV), "confidence": _num, "source": _str,
             "target": _str, "status": _is({"blocked", "monitoring", "mitigated", "investigating"})})


def node(v):
    _obj(v, {"id": _str, "label": _str, "type": _is({"gateway", "firewall", "router", "switch", "server", "ai", "pqc", "iot", "database", "soc"}),
             "status": _is({"healthy", "warning", "compromised", "healing", "isolated"}),
             "layer": _is({"edge", "core", "service", "endpoint"}), "x": _num, "y": _num, "ip": _str, "load": _num})


def edge(v):
    _obj(v, {"from": _str, "to": _str}, {"status": _is({"normal", "congested", "down", "rerouted"})})


SPECS = {
    "overview": lambda v: _obj(v, {
        "postureScore": _num,
        "kpis": _list(lambda k: _obj(k, {"id": _str, "label": _str, "value": _str, "delta": _str, "trend": _is({"up", "down", "flat"}),
                                          "tone": _is(TONES), "hint": _str})),
        "traffic": _list(lambda t: _obj(t, {"time": _str, "inbound": _num, "outbound": _num, "anomalies": _num})),
        "recentThreats": _list(threat_event)}),
    "threats": lambda v: _obj(v, {
        "model": lambda m: _obj(m, {"name": _str, "version": _str, "architecture": _str, "lastTrained": _str},
                                {"accuracy": lambda x: _num(x, True), "precision": lambda x: _num(x, True),
                                 "recall": lambda x: _num(x, True), "macroF1": lambda x: _num(x, True)}),
        "currentRisk": _num,
        "riskTrend": _list(lambda p: _obj(p, {"hour": _str, "predicted": _num, "observed": _num})),
        "categories": _list(lambda c: _obj(c, {"category": _str, "score": _num})),
        "events": _list(threat_event)}),
    "crypto": lambda v: _obj(v, {
        "coverage": _num,
        "algorithms": _list(lambda a: _obj(a, {"id": _str, "name": _str, "family": _str,
                                               "role": _is({"Key Encapsulation", "Digital Signature"}), "standard": _str,
                                               "securityLevel": _num, "status": _is({"active", "standby", "testing"}),
                                               "publicKeyBytes": _num, "usage": _num}, {"usageLabel": _str})),
        "sessions": _list(lambda s: _obj(s, {"id": _str, "peer": _str, "kem": _str, "signature": _str,
                                              "mode": _is({"hybrid", "pqc-only", "classical"}), "established": _str, "latencyMs": _num})),
        "benchmarks": _list(lambda b: _obj(b, {"operation": _str, "pqcMs": _num}, {"classicalMs": lambda x: _num(x, True)})),
        "rotations": _list(lambda r: _obj(r, {"id": _str, "timestamp": _str, "algorithm": _str, "scope": _str}))}),
    "healing": lambda v: _obj(v, {
        "mttrSeconds": _num, "autoRemediationRate": _num,
        "incidents": _list(lambda i: _obj(i, {"id": _str, "timestamp": _str, "node": _str, "issue": _str, "action": _str,
                                               "durationSec": _num, "status": _is({"resolved", "in-progress", "escalated"})})),
        "policies": _list(lambda p: _obj(p, {"id": _str, "name": _str, "trigger": _str, "action": _str,
                                              "enabled": lambda x: _enum(x, {True, False})})),
        "mttrTrend": _list(lambda t: _obj(t, {"day": _str, "mttr": _num, "incidents": _num}))}),
    "topology": lambda v: _obj(v, {"nodes": _list(node), "edges": _list(edge)}),
    "pipeline": lambda v: _obj(v, {
        "stages": _list(lambda s: _obj(s, {"id": _str, "name": _str, "module": _str,
                                            "status": _is({"running", "idle", "degraded", "error"}), "throughput": _num,
                                            "latencyMs": lambda x: _num(x, True), "queue": _num,
                                            "uptime": lambda x: _num(x, True)})),
        "throughputHistory": _list(lambda r: (_obj(r, {"time": _str}), [_num(x) for k, x in r.items() if k != "time"]))}),
    "logs": _list(lambda l: _obj(l, {"id": _str, "timestamp": _str, "level": _is(LOGLEVELS), "module": _str, "message": _str})),
    "stage_result": lambda v: _obj(v, {
        "stageId": _is({"traffic", "detection", "crypto", "healing", "final"}), "headline": _str,
        "metrics": _list(lambda m: _obj(m, {"label": _str, "value": _str})),
        "logs": _list(lambda l: _obj(l, {"level": _is(LOGLEVELS), "message": _str}))}),
}


def check(name: str, payload) -> None:
    SPECS[name](payload)
