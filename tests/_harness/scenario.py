import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import validate, ValidationError

from .schema import SCENARIO_SCHEMA


@dataclass
class Scenario:
    name: str
    category: str
    bundle: int
    points: float
    description: str
    config: dict[str, Any]
    events: list[dict[str, Any]]
    assertions: list[dict[str, Any]]


def load_scenario(path: Path) -> Scenario:
    with open(path) as f:
        data = json.load(f)
    try:
        validate(instance=data, schema=SCENARIO_SCHEMA)
    except ValidationError as e:
        raise ValueError(f"scenario {path.name} invalid: {e.message}") from e
    return Scenario(
        name=data["name"],
        category=data["category"],
        bundle=data["bundle"],
        points=data["points"],
        description=data.get("description", ""),
        config=data["config"],
        events=data["events"],
        assertions=data["assertions"],
    )
