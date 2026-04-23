from tests._harness.runner import ScenarioRunner
from tests._harness.scenario import Scenario
from tests._harness.simulator import Simulator


class FakeHost:
    def __init__(self, name):
        self.name = name
        self.received_packets = []
        self.timer_fires = 0
        self.app_payloads = []

    def recv_from_app(self, payload): self.app_payloads.append(payload)
    def recv_from_network(self, packet): self.received_packets.append(packet)
    def on_timer_expire(self): self.timer_fires += 1
    def close(self): pass

    window_base = next_seq = bytes_acked = bytes_delivered = 0
    sack_blocks = []
    state = "LISTEN"
    retransmit_count = {}
    app_recv_buffer = []


def _make_scenario(events, assertions=None):
    return Scenario(
        name="t", category="c", bundle=2, points=1, description="",
        config={"timer_interval": 1.0, "window_size": 4096,
                "a_isn": 1000, "b_isn": 5000, "initial_sender": "A"},
        events=events,
        assertions=assertions or [],
    )


def test_runner_executes_handshake_complete_event():
    sim = Simulator()
    sim.attach(FakeHost("A"), FakeHost("B"))
    scenario = _make_scenario([{"index": 0, "type": "handshake_complete"}])
    runner = ScenarioRunner(sim, scenario, handshake_stub=lambda s: None)
    runner.run()
    assert runner.events_executed == 1


def test_runner_executes_app_send_event():
    sim = Simulator()
    a = FakeHost("A")
    b = FakeHost("B")
    sim.attach(a, b)
    scenario = _make_scenario([{"index": 0, "type": "app_send", "host": "A", "payload": "hello"}])
    runner = ScenarioRunner(sim, scenario, handshake_stub=lambda s: None)
    runner.run()
    assert runner.events_executed == 1
    assert b"hello" in a.app_payloads


def test_runner_executes_tick_event():
    sim = Simulator()
    sim.attach(FakeHost("A"), FakeHost("B"))
    scenario = _make_scenario([{"index": 0, "type": "tick", "t": 5.0}])
    runner = ScenarioRunner(sim, scenario)
    runner.run()
    assert sim.clock == 5.0
    assert runner.events_executed == 1


def test_runner_unknown_event_raises():
    import pytest
    sim = Simulator()
    sim.attach(FakeHost("A"), FakeHost("B"))
    scenario = _make_scenario([{"index": 0, "type": "unknown_event_type"}])
    runner = ScenarioRunner(sim, scenario)
    with pytest.raises(ValueError):
        runner.run()
