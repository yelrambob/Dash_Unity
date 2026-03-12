# Pre-built tech profiles for early game levels.
# Each tech has four attributes (all 0.0–1.0):
#   speed      — drives scan time (±25%)
#   accuracy   — drives cooldown (±22%) and written-up error rate
#   willingness — drives setup time (±15%) and collaboration floor
#   diligence  — drives fireable error probability
#
# Arrival and departure times are in game-time hours (e.g. 7.0 = 07:00).
#
# SHIFT STRUCTURE (levels 1–2, 2 scanners):
#   07:00–15:30  Alex + Jordan    (morning)
#   11:00–19:30  Morgan + Riley   (afternoon)
#   11:00–15:30  overlap window — 4 techs, 2 scanners → collaboration
#
# Future: difficulty levels will vary stat distributions. Scheduler feature
# will let the player pick which techs cover each shift.

TECH_ROSTER = [
    {
        # Solid all-rounder. Careful, reliable, good under pressure.
        "id":          "tech_01",
        "name":        "Alex",
        "speed":       0.85,
        "accuracy":    0.90,
        "willingness": 0.80,
        "diligence":   0.88,
        "shift_start": 7.0,
        "shift_end":   15.5,
    },
    {
        # Average across the board. A bit reluctant; not a self-starter.
        "id":          "tech_02",
        "name":        "Jordan",
        "speed":       0.70,
        "accuracy":    0.75,
        "willingness": 0.65,
        "diligence":   0.78,
        "shift_start": 7.0,
        "shift_end":   15.5,
    },
    {
        # Very fast, enthusiastic, cuts corners on verification. Risk tech.
        # High throughput but diligence=0.62 means real fireable-error exposure
        # during heavy-volume shifts. Pairs well with high-willingness partners.
        "id":          "tech_03",
        "name":        "Morgan",
        "speed":       0.90,
        "accuracy":    0.65,
        "willingness": 0.88,
        "diligence":   0.62,
        "shift_start": 11.0,
        "shift_end":   19.5,
    },
    {
        # Slow and methodical. Almost never makes a real mistake.
        # Low throughput but nearly zero fireable risk. Ideal for lower-volume
        # or high-stakes shifts where errors are catastrophic.
        "id":          "tech_04",
        "name":        "Riley",
        "speed":       0.58,
        "accuracy":    0.83,
        "willingness": 0.72,
        "diligence":   0.94,
        "shift_start": 11.0,
        "shift_end":   19.5,
    },
]
