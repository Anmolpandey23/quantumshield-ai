import pytest
import torch

from stage3.guardrails import Guardrails
from stage3.node_agent import NodeFleet
from stage3.policy import SelfHealingPolicy
from stage3.ppo import ActorCritic, train_ppo

from stage2.commands import CommandSigner


def s1(node, label="DDoS", conf=0.95, risk=0.92, anomaly=0.9):
    return {"contract_version": "1.0", "node_id": node, "threat_label": label, "confidence": conf,
            "anomaly_score": anomaly, "risk_score_node": risk, "explanation": []}


@pytest.fixture(scope="module")
def trained():
    net, hist = train_ppo(iterations=100, n_envs=16, n_nodes=12, horizon=60, verbose=False)
    return net, hist


def test_ppo_learns_something(trained):
    net, hist = trained
    assert hist[-1]["return"] > hist[0]["return"] + 100          # far better than the untrained start


def test_policy_isolates_a_clearly_infected_node_and_reconnects_it_later(trained):
    net, _ = trained
    p = SelfHealingPolicy(net, Guardrails())
    for n in ("a", "b", "c", "d"):
        for _ in range(3):
            p.observe(s1(n, "BENIGN", 0.98, 0.05, 0.05))
    for _ in range(3):
        p.observe(s1("a"))
    d = p.decide(s1("a"))
    assert d["action"] == "isolate" and not d["requires_approval"]
    p.on_applied("a", "isolate")
    for _ in range(6):                                           # node now looks clean for a while
        p.observe(s1("a", "BENIGN", 0.99, 0.03, 0.02))
    assert p.decide(s1("a", "BENIGN", 0.99, 0.03, 0.02))["action"] == "reconnect"


def test_critical_node_needs_a_human(trained):
    net, _ = trained
    p = SelfHealingPolicy(net, Guardrails(critical_nodes={"gw"}))
    for n in ("a", "b", "gw"):
        p.observe(s1(n, "BENIGN", 0.98, 0.05, 0.05))
    for _ in range(4):
        p.observe(s1("gw"))
    d = p.decide(s1("gw"))
    assert d["action"] == "isolate" and d["requires_approval"] is True
    assert p(s1("gw"), {}) == "monitor"                           # the plain-callable form never acts without approval


def test_fallback_without_weights_still_works(tmp_path):
    with pytest.warns(UserWarning):
        p = SelfHealingPolicy.load(tmp_path / "nope.pt")
    for _ in range(3):
        p.observe(s1("x", "BENIGN", 0.9, 0.05, 0.05)); p.observe(s1("y", "BENIGN", 0.9, 0.05, 0.05))
    for _ in range(3):
        p.observe(s1("x"))
    assert p.decide(s1("x"))["source"] in ("rule_fallback", "guardrail") and p.decide(s1("x"))["action"] == "isolate"


def test_node_agent_obeys_only_valid_signed_commands():
    signer = CommandSigner()
    fleet = NodeFleet(signer.public_key)
    cmd = signer.sign("n1", "isolate")
    assert fleet.apply(cmd) == (True, "applied") and fleet.status("n1") == "isolated"
    assert fleet.apply(cmd) == (False, "replay_detected")
    assert fleet.apply(signer.sign("n2", "isolate"))[0] and fleet.status("n2") == "isolated"
    forged = signer.sign("n3", "reconnect"); forged["payload"]["node_id"] = "n9"
    assert fleet.apply(forged) == (False, "bad_signature")
    other = CommandSigner()
    assert fleet.apply(other.sign("n4", "isolate")) == (False, "bad_signature")      # wrong controller key
    wrong = signer.sign("n5", "isolate")
    assert fleet.agent("n6").receive(wrong) == (False, "wrong_node")
