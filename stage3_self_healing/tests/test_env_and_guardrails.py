import numpy as np

from stage3 import baselines
from stage3.env import OBS_DIM, BatchedNetworkEnv
from stage3.evaluate import run
from stage3.guardrails import ISOLATE, MONITOR, RECONNECT, Guardrails, action_mask, enforce_isolation_cap


def test_env_shapes_and_illegal_actions_are_ignored():
    env = BatchedNetworkEnv(4, 8, 10, seed=1)
    obs, mask = env.reset()
    assert obs.shape == (4, 8, OBS_DIM) and mask.shape == (4, 8, 3)
    assert not mask[..., RECONNECT].any()                              # nothing is isolated yet
    obs, mask, r, done, info = env.step(np.full((4, 8), RECONNECT))    # illegal for everyone -> becomes monitor
    assert (env.status == 1).all() and r.shape == (4, 8) and not done


def test_isolating_a_clean_network_stops_spread_and_costs_availability():
    env = BatchedNetworkEnv(8, 10, 20, seed=2)
    env.reset()
    env.step(np.full((8, 10), ISOLATE))
    assert ((env.status == 2).mean(1) <= 0.5 + 1e-9).all()                   # blast-radius cap enforced in the simulator too


def test_rule_beats_doing_nothing():
    assert run(baselines.rule_policy, 16)["return"] > run(baselines.never_act, 16)["return"]


def test_action_mask_and_cap():
    st = np.array([0, 1, 2])
    m = action_mask(st)
    assert m[0].tolist() == [True, True, False] and m[2].tolist() == [True, False, True]
    acts = enforce_isolation_cap(np.array([ISOLATE] * 6), np.array([.9, .8, .7, .6, .5, .4]), np.zeros(6, int), 0.5)
    assert (acts == ISOLATE).sum() == 3 and acts[0] == ISOLATE and acts[5] == MONITOR   # the 3 riskiest win


def s1(node, label="DDoS", conf=0.95, risk=0.9):
    return {"node_id": node, "threat_label": label, "confidence": conf, "anomaly_score": 0.9, "risk_score_node": risk}


def test_guardrails_rules():
    g = Guardrails(critical_nodes={"gw"}, max_isolated_fraction=0.5)
    st = {"a": "online", "b": "online", "gw": "online", "d": "online"}
    assert g.check("isolate", s1("a"), st)[0] == "isolate"
    assert g.check("isolate", s1("a", conf=0.3), st)[0] == "monitor"                  # not enough evidence
    assert g.check("isolate", s1("a", label="BENIGN"), st)[0] == "monitor"
    assert g.check("isolate", s1("gw"), st) == ("isolate", True, "critical node: human approval required")
    assert g.check("fly_to_moon", s1("a"), st)[0] == "monitor"                        # allowlist
    st2 = {"a": "online", "b": "isolated", "gw": "isolated", "d": "online"}
    assert g.check("isolate", s1("a"), st2)[0] == "monitor"                           # blast radius: 2 of 4 already isolated
    assert g.check("reconnect", s1("a"), st)[0] == "monitor"                          # cannot reconnect a node that is online
    g.enabled = False
    assert g.check("isolate", s1("a"), st)[0] == "monitor"                            # kill switch
