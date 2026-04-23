from .scenario import Scenario
from .simulator import Simulator


class ScenarioRunner:
    """Walks a scenario's event list, executing each event against the simulator."""

    def __init__(self, simulator: Simulator, scenario: Scenario, handshake_stub=None):
        self.sim = simulator
        self.scenario = scenario
        self.events_executed = 0
        self._handshake_stub = handshake_stub

    def run(self) -> None:
        for event in self.scenario.events:
            self._dispatch(event)
            self.events_executed += 1

    def _dispatch(self, event: dict) -> None:
        etype = event["type"]
        if etype == "handshake_complete":
            if self._handshake_stub is not None:
                self._handshake_stub(self.sim)
            else:
                self._run_handshake()
        elif etype == "app_send":
            host = self.sim._hosts[event["host"]]
            payload = event["payload"]
            host.recv_from_app(payload.encode() if isinstance(payload, str) else payload)
            self.sim.run_pending()
        elif etype == "app_close":
            host = self.sim._hosts[event["host"]]
            host.close()
            self.sim.run_pending()
        elif etype == "drop_next":
            self.sim.arm_trap({"type": "drop_next", "match": event.get("match", {})})
        elif etype == "corrupt_next":
            self.sim.arm_trap({"type": "corrupt_next", "match": event.get("match", {})})
        elif etype == "tick":
            self.sim.tick(event["t"])
        else:
            raise ValueError(f"unknown event type: {etype}")

    def _run_handshake(self) -> None:
        """Drive hosts through a full 3-way handshake."""
        initial_sender = self.scenario.config["initial_sender"]
        initial = self.sim._hosts[initial_sender]
        initial.recv_from_app(b"")
        for _ in range(10):
            self.sim.run_pending()
            a_state = self.sim._hosts["A"].state
            b_state = self.sim._hosts["B"].state
            if a_state == "ESTABLISHED" and b_state == "ESTABLISHED":
                return
            self.sim.tick(self.sim.clock + 0.1)
        raise RuntimeError(f"handshake did not complete: A={a_state} B={b_state}")
