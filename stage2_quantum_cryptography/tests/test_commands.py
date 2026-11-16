from stage2.commands import CommandSigner, CommandVerifier


def make():
    s = CommandSigner()
    return s, CommandVerifier(s.public_key, max_age_s=30)


def test_genuine_command_is_accepted():
    s, v = make()
    assert v.verify(s.sign("n1", "isolate")) == (True, "ok")


def test_forged_edit_is_rejected():
    s, v = make()
    cmd = s.sign("n1", "isolate")
    cmd["payload"]["action"] = "reconnect"
    assert v.verify(cmd) == (False, "bad_signature")


def test_replay_is_rejected():
    s, v = make()
    cmd = s.sign("n1", "monitor")
    assert v.verify(cmd)[0] is True
    assert v.verify(cmd) == (False, "replay_detected")


def test_stale_command_is_rejected():
    s, v = make()
    assert v.verify(s.sign("n1", "isolate", now=1000.0), now=2000.0) == (False, "stale_command")


def test_action_outside_allowlist_is_rejected():
    s, v = make()
    assert v.verify(s.sign("n1", "format_disk")) == (False, "action_not_allowed")


def test_attacker_key_and_garbage_are_rejected():
    s, v = make()
    assert v.verify(CommandSigner().sign("n1", "reconnect")) == (False, "bad_signature")
    assert v.verify({"nope": 1}) == (False, "malformed_command")
