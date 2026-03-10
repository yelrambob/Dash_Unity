# [BUILD FIRST]
# The 24-hour spawn rate table derived from real exam volume data.
# Each hour maps to: exams_per_hour, spawn_weight, acuity_bias.
#
# acuity_bias: float 0.0–1.0 — higher = more high-acuity patients that hour.
# spawn_weight: relative probability used by SpawnManager to throttle flow.
#
# Based on 6 months of real hourly data:
#   Quiet overnight: ~4 exams/hr
#   Ramp starts:     hour 08
#   Peak plateau:    hours 11–17 (~16–18 exams/hr)
#   Evening taper:   hours 18–20

HOURLY_SPAWN_TABLE = {
    #  hour: {"exams_per_hour": int, "spawn_weight": float, "acuity_bias": float}
     0: {"exams_per_hour":  4, "spawn_weight": 0.25, "acuity_bias": 0.6},
     1: {"exams_per_hour":  3, "spawn_weight": 0.20, "acuity_bias": 0.6},
     2: {"exams_per_hour":  3, "spawn_weight": 0.20, "acuity_bias": 0.6},
     3: {"exams_per_hour":  3, "spawn_weight": 0.20, "acuity_bias": 0.6},
     4: {"exams_per_hour":  4, "spawn_weight": 0.25, "acuity_bias": 0.5},
     5: {"exams_per_hour":  4, "spawn_weight": 0.25, "acuity_bias": 0.5},
     6: {"exams_per_hour":  5, "spawn_weight": 0.30, "acuity_bias": 0.4},
     7: {"exams_per_hour":  7, "spawn_weight": 0.45, "acuity_bias": 0.4},
     8: {"exams_per_hour": 10, "spawn_weight": 0.65, "acuity_bias": 0.35},
     9: {"exams_per_hour": 13, "spawn_weight": 0.80, "acuity_bias": 0.35},
    10: {"exams_per_hour": 15, "spawn_weight": 0.90, "acuity_bias": 0.30},
    11: {"exams_per_hour": 17, "spawn_weight": 1.00, "acuity_bias": 0.30},
    12: {"exams_per_hour": 18, "spawn_weight": 1.00, "acuity_bias": 0.30},
    13: {"exams_per_hour": 17, "spawn_weight": 1.00, "acuity_bias": 0.30},
    14: {"exams_per_hour": 16, "spawn_weight": 0.95, "acuity_bias": 0.30},
    15: {"exams_per_hour": 16, "spawn_weight": 0.95, "acuity_bias": 0.30},
    16: {"exams_per_hour": 16, "spawn_weight": 0.95, "acuity_bias": 0.30},
    17: {"exams_per_hour": 15, "spawn_weight": 0.90, "acuity_bias": 0.35},
    18: {"exams_per_hour": 12, "spawn_weight": 0.75, "acuity_bias": 0.40},
    19: {"exams_per_hour":  9, "spawn_weight": 0.55, "acuity_bias": 0.45},
    20: {"exams_per_hour":  7, "spawn_weight": 0.45, "acuity_bias": 0.50},
    21: {"exams_per_hour":  6, "spawn_weight": 0.38, "acuity_bias": 0.55},
    22: {"exams_per_hour":  5, "spawn_weight": 0.30, "acuity_bias": 0.60},
    23: {"exams_per_hour":  4, "spawn_weight": 0.25, "acuity_bias": 0.60},
}
