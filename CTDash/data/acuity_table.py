# [BUILD FIRST]
# Acuity table based on real departmental priority hierarchy.
#
# 4 tiers instead of 5 — reflects how the department actually operates:
#
#   Tier 1 — True emergencies: Trauma, Stroke. Non-negotiable, always first.
#   Tier 2 — Critical protocols: Aortic Dissection, AAA, PE, SAH.
#             Legitimate emergencies but subject to priority creep/abuse.
#             Player must judge legitimacy on higher difficulty levels.
#   Tier 3 — Inflated STATs: The ~80% of orders labeled STAT that aren't.
#             After Tier 1 and 2, these are treated in order of arrival time.
#   Tier 4 — Routine: Urgent, Routine inpatient, Scheduled outpatient,
#             Pending discharge. All treated the same in practice.
#
# spawn_weights are derived from 6 months of real volume data:
#   ~48,000 total exams: STAT ~82%, Routine/Urgent ~16%, critical ~2%
#
# Priority creep mechanic (future):
#   On higher difficulty levels, a fraction of Tier 3 orders will be
#   falsely labeled as Tier 2. Player can downgrade them but risks
#   a penalty if they're wrong.

ACUITY_TABLE = {
    1: {
        "label":          "Trauma / Stroke",
        "queue_priority": 1,              # always first, no exceptions
        "spawn_weight":   0.02,           # rare but highest stakes
        "typical_exams":  ["trauma_full", "head", "cta_head"],
        "wait_threshold": 2 * 60,         # 2 game-minutes before penalty — very tight
        "penalty_mult":   5.0,            # harshest penalty in the game
        "can_downgrade":  False,          # player cannot reassign these
        "notes": "Trauma and Medical Alert Stroke. Time is brain / time is life.",
    },
    2: {
        "label":          "Critical Protocol",
        "queue_priority": 2,
        "spawn_weight":   0.03,           # slightly more common than tier 1
        "typical_exams":  ["cta_chest", "cta_head", "abdpel", "head"],
        "wait_threshold": 5 * 60,         # 5 game-minutes
        "penalty_mult":   3.0,
        "can_downgrade":  True,           # future mechanic: player can challenge order
        "notes": "Aortic Dissection, AAA, PE Protocol, SAH. Legitimate but "
                 "subject to abuse. SAH in particular used to bypass STAT queue.",
    },
    3: {
        "label":          "Inflated STAT",
        "queue_priority": 3,
        "spawn_weight":   0.80,           # the bulk of real volume — ~80% of all orders
        "typical_exams":  ["head", "abdpel", "chest", "spine", "cta_chest", "extremity"],
        "wait_threshold": 25 * 60,        # 25 game-minutes — reflects real STAT reality
        "penalty_mult":   1.5,
        "can_downgrade":  False,          # nothing to downgrade to — already the bulk tier
        "notes": "Everything labeled STAT that isn't Tier 1 or 2. "
                 "Treated in arrival order after true emergencies are cleared. "
                 "Priority creep means nothing is actually STAT when everything is STAT.",
    },
    4: {
        "label":          "Routine",
        "queue_priority": 4,
        "spawn_weight":   0.15,           # ~16% of real volume
        "typical_exams":  ["abdpel", "chest", "spine", "extremity", "head"],
        "wait_threshold": 30 * 60,        # 30 game-minutes
        "penalty_mult":   0.5,            # low penalty — these patients expect to wait
        "can_downgrade":  False,
        "notes": "Urgent, Routine inpatient, Scheduled outpatient, Pending discharge. "
                 "All treated the same in practice — taken in order after STATs are clear.",
    },
}
