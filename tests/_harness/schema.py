SCENARIO_SCHEMA = {
    "type": "object",
    "required": ["name", "category", "bundle", "points", "config", "events", "assertions"],
    "properties": {
        "name": {"type": "string"},
        "category": {"type": "string"},
        "bundle": {"type": "integer", "enum": [1, 2, 3]},
        "points": {"type": "number"},
        "description": {"type": "string"},
        "config": {
            "type": "object",
            "required": ["timer_interval", "window_size", "a_isn", "b_isn", "initial_sender"],
        },
        "events": {"type": "array"},
        "assertions": {"type": "array"},
    },
}
