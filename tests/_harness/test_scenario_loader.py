import json
import pytest
from pathlib import Path
from tests._harness.scenario import load_scenario, Scenario


def test_load_valid_scenario(tmp_path):
    content = {
        "name": "test_foo",
        "category": "retransmit",
        "bundle": 3,
        "points": 2,
        "description": "desc",
        "config": {
            "timer_interval": 1.0,
            "window_size": 4096,
            "a_isn": 1000,
            "b_isn": 5000,
            "initial_sender": "A",
        },
        "events": [
            {"index": 0, "type": "handshake_complete"}
        ],
        "assertions": [
            {"after_event": 0, "host": "A", "check": "state == ESTABLISHED"}
        ],
    }
    path = tmp_path / "s.json"
    path.write_text(json.dumps(content))
    scenario = load_scenario(path)
    assert scenario.name == "test_foo"
    assert scenario.bundle == 3
    assert len(scenario.events) == 1


def test_load_rejects_missing_name(tmp_path):
    content = {"category": "retransmit", "bundle": 3, "points": 2,
               "config": {}, "events": [], "assertions": []}
    path = tmp_path / "s.json"
    path.write_text(json.dumps(content))
    with pytest.raises(ValueError):
        load_scenario(path)
