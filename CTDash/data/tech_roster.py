# [LATER] — depends on tech.py being built first
# Pre-built tech profiles for early game levels.
# Each tech has: speed, accuracy, willingness, knowledge_base (all 0.0–1.0).
# Arrival and departure times are in game-time hours (e.g. 7.0 = 07:00).
# Later difficulty levels will have worse stat distributions.

TECH_ROSTER = [
    {
        "id":             "tech_01",
        "name":           "Alex",
        "speed":          0.85,
        "accuracy":       0.90,
        "willingness":    0.80,
        "knowledge_base": 0.85,
        "shift_start":    7.0,
        "shift_end":      15.5,
    },
    {
        "id":             "tech_02",
        "name":           "Jordan",
        "speed":          0.70,
        "accuracy":       0.75,
        "willingness":    0.65,
        "knowledge_base": 0.70,
        "shift_start":    7.0,
        "shift_end":      15.5,
    },
    # TODO: add afternoon and evening techs
]
