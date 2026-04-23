import json
import pytest
from pathlib import Path

from .scenario import load_scenario, Scenario
from .simulator import Simulator
from .runner import ScenarioRunner
from .assertions import evaluate_assertion

_HINTS_PATH = Path(__file__).parent / "category_hints.json"


def pytest_collect_file(parent, file_path):
    """Discover scenario JSON files as pytest test cases."""
    if file_path.suffix == ".json" and (
        file_path.parent.name.startswith("bundle")
        or file_path.parent.parent.name.startswith("bundle")
    ):
        return ScenarioFile.from_parent(parent, path=file_path)


class ScenarioFile(pytest.File):
    def collect(self):
        scenario = load_scenario(self.path)
        yield ScenarioItem.from_parent(self, name=scenario.name, scenario=scenario)


class ScenarioItem(pytest.Item):
    def __init__(self, *, scenario: Scenario, **kw):
        super().__init__(**kw)
        self.scenario = scenario
        self.add_marker(pytest.mark.bundle(scenario.bundle))
        self.add_marker(pytest.mark.points(scenario.points))

    def runtest(self):
        from src.rdp.connection import TCPConnection
        sim = Simulator()
        cfg = self.scenario.config
        host_a = TCPConnection(sim.handle_for("A"), "A",
                               cfg["a_isn"], cfg["timer_interval"], cfg["window_size"])
        host_b = TCPConnection(sim.handle_for("B"), "B",
                               cfg["b_isn"], cfg["timer_interval"], cfg["window_size"])
        sim.attach(host_a, host_b)

        runner = ScenarioRunner(sim, self.scenario)
        event_log = []
        for idx, event in enumerate(self.scenario.events):
            runner._dispatch(event)
            event_log.append(event)
            for assertion in self.scenario.assertions:
                if assertion["after_event"] == idx:
                    host = sim._hosts[assertion["host"]]
                    state = _capture_state(host)
                    ok = evaluate_assertion(assertion["check"], state)
                    if not ok:
                        raise ScenarioAssertionFailed(
                            self.scenario, idx, event, assertion, state, event_log,
                        )

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, ScenarioAssertionFailed):
            return excinfo.value.render()
        return super().repr_failure(excinfo)


def _capture_state(host):
    return {
        "window_base": host.window_base,
        "next_seq": host.next_seq,
        "bytes_acked": host.bytes_acked,
        "bytes_delivered": host.bytes_delivered,
        "sack_blocks": host.sack_blocks,
        "state": host.state,
        "retransmit_count": host.retransmit_count,
        "app_recv_buffer": host.app_recv_buffer,
    }


class ScenarioAssertionFailed(Exception):
    def __init__(self, scenario, event_idx, event, assertion, state, event_log):
        self.scenario = scenario
        self.event_idx = event_idx
        self.event = event
        self.assertion = assertion
        self.state = state
        self.event_log = event_log

    def render(self):
        hints = json.loads(_HINTS_PATH.read_text()).get(self.scenario.category, {})
        summary = hints.get("summary", "")
        hint_list = "\n".join(f"  - {h}" for h in hints.get("hints", []))
        recent = "\n".join(
            f"  [{i}] {e['type']} {e.get('host', '')} {e.get('payload', '')}"
            for i, e in enumerate(self.event_log[-5:])
        )
        return (
            f"Scenario {self.scenario.name!r} failed at event {self.event_idx} "
            f"({self.event['type']})\n"
            f"\nFailed assertion: {self.assertion['check']} on host {self.assertion['host']}\n"
            f"Actual state: {self.state}\n"
            f"\nLast events:\n{recent}\n"
            f"\nCategory: {self.scenario.category} — {summary}\n"
            f"Likely bug categories:\n{hint_list}\n"
        )
