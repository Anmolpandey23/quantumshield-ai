"""What runs ON each computer: verify the signed command, then obey it. Nothing unsigned is ever executed."""
from __future__ import annotations

from dataclasses import dataclass, field

from .guardrails import ISOLATED, MONITORED, ONLINE


@dataclass
class NodeAgent:
    node_id: str
    verifier: object                       # stage2.commands.CommandVerifier (this node's own copy: own replay memory)
    state: str = ONLINE
    history: list = field(default_factory=list)

    def receive(self, signed_command: dict) -> tuple[bool, str]:
        ok, reason = self.verifier.verify(signed_command)
        if not ok:
            self.history.append(("rejected", reason))
            return False, reason
        p = signed_command["payload"]
        if p["node_id"] != self.node_id:
            self.history.append(("rejected", "wrong_node"))
            return False, "wrong_node"
        self.state = {"isolate": ISOLATED, "reconnect": ONLINE, "monitor": MONITORED if self.state != ISOLATED else ISOLATED}[p["action"]]
        self.history.append((p["action"], "applied"))
        return True, "applied"


class NodeFleet:
    """All node agents of the network. In production each agent lives on its own machine."""

    def __init__(self, controller_public_key: bytes, max_age_s: float = 30.0):
        from stage2.commands import CommandVerifier           # imported lazily: needs the stage2 folder on sys.path
        self._mk = lambda: CommandVerifier(controller_public_key, max_age_s)
        self.agents: dict[str, NodeAgent] = {}

    def agent(self, node_id: str) -> NodeAgent:
        if node_id not in self.agents:
            self.agents[node_id] = NodeAgent(node_id, self._mk())
        return self.agents[node_id]

    def apply(self, signed_command: dict) -> tuple[bool, str]:
        return self.agent(signed_command["payload"]["node_id"]).receive(signed_command)

    def status(self, node_id: str) -> str:
        return self.agent(node_id).state
