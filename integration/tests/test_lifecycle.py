"""Full life of a node with the REAL Stage 3 policy, node agents, guardrails and human approval."""
import pytest

from integration.orchestrator import Orchestrator
from integration.stubs import stage1_stub
from stage3.guardrails import Guardrails
from stage3.node_agent import NodeFleet
from stage3.policy import SelfHealingPolicy

QUBITS = 512


def make(critical=()):
    policy = SelfHealingPolicy(None, Guardrails(critical_nodes=set(critical)))         # rule fallback: deterministic for tests
    o = Orchestrator(policy=policy, n_qubits=QUBITS)
    o.fleet = NodeFleet(o.signer.public_key)
    return o


def warm(o, nodes):
    for n in nodes:
        for _ in range(3):
            o.handle(stage1_stub(n, attack=False))


def test_isolate_then_reconnect_with_fresh_keys():
    o = make()
    warm(o, ["a", "b", "c", "d"])
    for _ in range(2):
        o.handle(stage1_stub("a"), seed=1)                                   # repeated high risk
    assert o.status["a"] == "isolated" and "a" not in o.node_keys
    assert o.fleet.status("a") == "isolated"                                 # the node itself obeyed, after verifying
    last = None
    for i in range(8):                                                       # it now looks clean
        last = o.handle(stage1_stub("a", attack=False), seed=10 + i)
        if last["decision"] == "command_issued":                              # first signed command after quarantine
            break
    assert last["stage3_command"]["payload"]["action"] == "reconnect" and last["rekeyed"] is True
    assert o.status["a"] == "online" and o.node_keys["a"] == last["stage2"]["shared_key_id"]


def test_critical_node_waits_for_a_human_then_can_be_approved_or_rejected():
    o = make(critical={"gw"})
    warm(o, ["a", "b", "gw"])
    e = None
    for i in range(3):
        e = o.handle(stage1_stub("gw"), seed=20 + i)
        if e["decision"] == "pending_human_approval":
            break
    assert e["decision"] == "pending_human_approval" and e["stage3_command"] is None
    assert o.status.get("gw", "online") != "isolated"                        # nothing happened yet
    aid = e["pending_approval"]["approval_id"]
    assert o.list_pending()[0]["approval_id"] == aid
    ok = o.approve(aid, "alice")
    assert ok["decision"] == "command_issued" and ok["command_verified"] and o.status["gw"] == "isolated"
    assert o.list_pending() == []

    o2 = make(critical={"gw"})
    warm(o2, ["a", "b", "gw"])
    for i in range(3):
        e = o2.handle(stage1_stub("gw"), seed=30 + i)
        if e["decision"] == "pending_human_approval":
            break
    r = o2.reject(e["pending_approval"]["approval_id"])
    assert r["decision"] == "command_rejected" and o2.status.get("gw", "online") != "isolated"


def test_eavesdropper_blocks_even_a_critical_decision():
    o = make()
    warm(o, ["a", "b"])
    e = o.handle(stage1_stub("a"), eve_fraction=1.0, seed=3)
    assert e["decision"] == "aborted_no_command" and o.status.get("a", "online") == "online"


def test_unknown_approval_id_raises():
    with pytest.raises(KeyError):
        make().approve("apr_999")
