# [BUILD FIRST]
# Defines acuity levels 1–5 (1 = most critical, 5 = routine).
# Each level controls spawn weighting, queue priority,
# typical exam types, and wait penalty calculation.

ACUITY_TABLE = {
    1: {
        "label":           "Trauma / Critical",
        "queue_priority":  1,          # lower = higher priority in queue
        "spawn_weight":    0.10,       # base fraction of spawns at this acuity
        "typical_exams":  ["trauma_full", "head"],
        "wait_threshold":  5 * 60,     # seconds before wait penalty kicks in
        "penalty_mult":    3.0,        # multiplier on WAIT_PENALTY_PER_MINUTE
    },
    2: {
        "label":           "Emergent",
        "queue_priority":  2,
        "spawn_weight":    0.20,
        "typical_exams":  ["head", "abdpel"],
        "wait_threshold":  10 * 60,
        "penalty_mult":    2.0,
    },
    3: {
        "label":           "Urgent",
        "queue_priority":  3,
        "spawn_weight":    0.35,
        "typical_exams":  ["abdpel", "head"],
        "wait_threshold":  20 * 60,
        "penalty_mult":    1.5,
    },
    4: {
        "label":           "Semi-urgent",
        "queue_priority":  4,
        "spawn_weight":    0.25,
        "typical_exams":  ["abdpel"],
        "wait_threshold":  30 * 60,
        "penalty_mult":    1.0,
    },
    5: {
        "label":           "Routine",
        "queue_priority":  5,
        "spawn_weight":    0.10,
        "typical_exams":  ["abdpel"],
        "wait_threshold":  45 * 60,
        "penalty_mult":    0.5,
    },
}
