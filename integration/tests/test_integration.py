import json
import pathlib

import pytest

from integration.orchestrator import Orchestrator
from integration.stubs import stage1_stub
from integration.validate import ContractError, validate

EXAMPLES = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "examples"


@pytest.fixture(scope="module")
def orch():
    return Orchestrator()


def test_attack_goes_through_all_stages_and_command_is_verified(orch):
    e = orch.handle(stage1_stub("10.0.0.5"), seed=1)
    assert e["decision"] == "command_issued" and e["command_verified"] is True
    assert e["stage2"]["status"] == "secure_channel_established"
    assert e["stage3_command"]["payload"]["action"] == "isolate"


def test_benign_traffic_never_triggers_stage2(orch):
    e = orch.handle(stage1_stub("10.0.0.6", attack=False))
    assert e["decision"] == "no_action" and e["stage2"] is None and e["stage3_command"] is None


def test_eavesdropper_means_no_command_is_issued(orch):
    e = orch.handle(stage1_stub("10.0.0.7"), eve_fraction=1.0, seed=2)
    assert e["decision"] == "aborted_no_command" and e["stage3_command"] is None
    assert e["stage2"]["eavesdrop_detected"] is True


def test_replayed_command_is_rejected(orch):
    e = orch.handle(stage1_stub("10.0.0.8"), seed=3)
    assert orch.verifier.verify(e["stage3_command"]) == (False, "replay_detected")


def test_broken_stage1_output_is_caught_by_the_contract(orch):
    bad = stage1_stub("10.0.0.9")
    bad["confidence"] = 1.5
    with pytest.raises(ContractError, match="confidence"):
        orch.handle(bad)
    del bad["confidence"]
    with pytest.raises(ContractError, match="confidence"):
        orch.handle(bad)


@pytest.mark.parametrize("path", sorted(EXAMPLES.glob("stage1_*.json")), ids=lambda p: p.name)
def test_example_files_match_their_contract(path):
    validate(json.loads(path.read_text()), "stage1_output")
